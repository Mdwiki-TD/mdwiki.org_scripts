# Flask-Security-Too Integration & Migration Plan

This document outlines a detailed, production-grade architectural review and migration plan to transition the existing custom authentication and authorization mechanisms of the **mdwiki-org-scripts** repository to **Flask-Security-Too**.

---

## 1. Executive Summary

The **mdwiki-org-scripts** application currently uses a bespoke authentication framework built on top of MediaWiki OAuth handshake credentials, stored in a custom `user_tokens` table. Users have a corresponding record in the stable `users` table. Access control is managed via custom decorators:
* `@oauth_required` and `@user_login_required` verify presence of logged-in sessions and cached user profiles.
* `@admin_required` checks if the user is an active administrator in the `admin_users` coordinator table.
* Hand-rolled flags like `can_run_jobs` and `can_run_bg_jobs` act as custom permission attributes on the user model.

While this structure is simple, migrating to **Flask-Security-Too** provides significant long-term architectural benefits, including robust standards-compliant session management, structured role and permission systems, unified datastores, enhanced password hashing (if direct credentials are ever introduced), and cleaner decorators.

This migration plan is designed to be **incremental and backward-compatible**, ensuring that both authentication schemes can temporarily coexist during transition and avoiding large-scale breaking refactorings of core application components.

---

## 2. Current Architecture Analysis & High-Level Assessment

### Current Authentication Flow
1. **Initiation:** The user visits `/login`. A random `state` token and an OAuth `request_token` from MediaWiki are generated and stored in the Flask session.
2. **MediaWiki Handshake:** The user is redirected to Meta-Wiki to authorize the application.
3. **Callback Handling:** Meta-Wiki redirects back to `/callback` with an OAuth verifier and the state token.
4. **Credential Extraction:** The application completes the handshake, retrieves an access token and user identity, and then maps/creates a row in the `users` table and upserts OAuth credentials in `user_tokens`.
5. **Session Management:** The user’s stable ID (`user_id`) is stored in `session["uid"]` and a signed cookie.
6. **Request Lifecycle:** On every request, a `before_app_request` hook (`load_logged_in_user()`) intercepts the request:
   - Resolves `user_id` from the session or signed cookie fallback.
   - Fetches OAuth credentials and username using `AuthUserService.get_authenticated_user()`.
   - Caches a composite `CurrentUser` object into Flask global `g._current_user`.
   - Sets template variables (`is_authenticated`, `current_username`, `is_admin`) in app context processor.

### Custom Access Control Mechanisms
* **Authentication Decorators:**
  - `@oauth_required`: Demands a full OAuth credential bundle (checks `g._current_user`). Redirects unauthenticated requests to `/login` after setting `session["post_login_redirect"]`.
  - `@user_login_required`: Requires user login, but redirects the user to their referrer (or home) with a flash message rather than forcing the login flow.
* **Authorization Decorators:**
  - `@admin_required`: Intercepts calls, loads the user, and validates `user.is_active_admin` (which queries the `admin_users` table to see if `is_active=True`). Triggers an HTTP 403 Forbidden on violation.
* **Permission Flags:**
  - `can_run_jobs`: Controls whether a user can execute synchronous medical updates.
  - `can_run_bg_jobs`: Controls whether a user can trigger daemon background jobs.

---

## 3. Dependency Graph

```
           +-----------------------+
           |   MediaWiki OAuth /   |
           |    Meta-Wiki login    |
           +-----------+-----------+
                       |
                       v [Access Token / Identity]
           +-----------+-----------+
           |     /callback Route   |
           +-----------+-----------+
                       |
                       +---------------------------------------+
                       | (Retrieves / Creates)                 | (Stores)
                       v                                       v
         +-------------+-------------+             +-----------+-----------+
         |     UserRecord Model      |             |   UserTokenRecord     |
         |         (users)           |             |    (user_tokens)      |
         +-------------+-------------+             +-----------------------+
                       |
                       | (References username)
                       v
         +-------------+-------------+
         |    AdminUserRecord Model  | (Check if active coordinator)
         |       (admin_users)       |
         +-------------+-------------+
                       |
                       +---------------------------------------+
                       |                                       |
                       v (before_app_request hook)             v (Context processor)
         +-------------+-------------+             +-----------+-----------+
         |   Flask g._current_user   | ------------>|  HTML Templates &     |
         |   (CurrentUser Class)     |             |  Custom Macros        |
         +-------------+-------------+             +-----------------------+
                       |
                       +-------------------+-------------------+
                       |                   |                   |
                       v                   v                   v
                @oauth_required     @user_login_required   @admin_required
```

---

## 4. Phased Migration Strategy & Roadmap

An incremental 6-phase migration strategy prevents breaking changes, preserves tool availability on Wikimedia Toolforge, and keeps the codebase fully testable at all points.

```
+-------------------------------------------------------------------------------------------------------------------------+
|                                                      ROADMAP SUMMARY                                                    |
+------------------------------------+------------------------------------------------------------------------------------+
| Phase 1: Dependency Integration   | Add Flask-Security-Too and dependencies; configure Flask-Security configs.         |
+------------------------------------+------------------------------------------------------------------------------------+
| Phase 2: Schema Expansion & Models | Adapt `UserRecord` to Flask-Security model requirements; define `Role` models.       |
+------------------------------------+------------------------------------------------------------------------------------+
| Phase 3: Security Initialisation   | Init Flask-Security with custom UserDatastore; bridge existing sessions.          |
+------------------------------------+------------------------------------------------------------------------------------+
| Phase 4: Decorator & Route Bridge  | Replace custom decorators, update template mappings and route-level protection.    |
+------------------------------------+------------------------------------------------------------------------------------+
| Phase 5: OAuth Login Integration   | Update Callback authentication logic to register logins with Flask-Security.      |
+------------------------------------+------------------------------------------------------------------------------------+
| Phase 6: Post-Migration Cleanup    | Delete legacy current user helper and obsolete decorators; run cleanups.           |
+------------------------------------+------------------------------------------------------------------------------------+
```

---

## 5. Detailed Step-by-Step Implementation Guide

### Phase 1: Dependency Integration

#### Why this step is needed
Installs Flask-Security-Too and its corresponding cryptographic and serialization dependencies into the virtual environment, establishing the foundation for security hooks.

#### Files that need modification
* `requirements.txt`
* `requirements-dev.txt`
* `src/main_app/config/flask_config.py`

#### Expected code changes
Add Flask-Security-Too to `requirements.txt`:
```text
Flask-Security-Too>=5.5.0
```

Configure Flask settings in `src/main_app/config/flask_config.py`:
```python
    # Flask-Security settings
    SECURITY_PASSWORD_HASH: str = "bcrypt"
    # Note: MediaWiki handles passwords; we require a dummy secret key to satisfy Flask-Security.
    SECURITY_PASSWORD_SALT: str = settings.security.secret_key
    SECURITY_REGISTERABLE: bool = False
    SECURITY_SEND_REGISTER_EMAIL: bool = False
    SECURITY_LOGIN_WITHOUT_CONFIRMATION: bool = True

    # Disable built-in views we don't need (since login is strictly OAuth)
    SECURITY_LOGIN_URL: str = "/login-security-disabled"
    SECURITY_LOGOUT_URL: str = "/logout-security-disabled"
    SECURITY_REGISTER_URL: str = "/register-security-disabled"

    # Session handling
    SECURITY_URL_PREFIX: str = "/auth"
    SECURITY_FLASH_MESSAGES: bool = True
```

#### Potential issues
* Conflicting dependencies with existing packages. Since Flask-Security-Too requires specific versions of packages, running `pip install` with exact constraints prevents system breaks.
* Flask-WTF and WTForms conflicts. Standardized configuration flags must be carefully synchronized.

#### Verification steps
Ensure Python can import the library successfully:
```bash
python -c "import flask_security"
```

---

### Phase 2: Schema Expansion & Models

#### Why this step is needed
Flask-Security-Too requires specific database attributes (e.g., active status, distinct role associations, and unique identifiers) to perform authentication, role checks, and permission checks.

#### Files that need modification
* `src/main_app/db/models/users.py`

#### Expected code changes

##### Before Schema Modification:
`UserRecord` has no `active`, `fs_uniquifier`, or Roles linkage. `AdminUserRecord` is a standalone coordinator table.

##### Recommended Flask-Security Models Setup (After):
Create roles and role mappings while maintaining database compatibility:

```python
from flask_security import UserMixin, RoleMixin
from sqlalchemy import Table, Column, Integer, ForeignKey

# Association Table for User <-> Roles mapping
roles_users = Table(
    "roles_users",
    db.Model.metadata,
    Column("user_id", Integer(), ForeignKey("users.user_id", ondelete="CASCADE")),
    Column("role_id", Integer(), ForeignKey("roles.id", ondelete="CASCADE"))
)


class Role(db.Model, RoleMixin):
    """
    Standard Flask-Security role representation.
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permissions: Mapped[str | None] = mapped_column(String(255), nullable=True)


class UserRecord(db.Model, UserMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    can_run_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    can_run_bg_jobs: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)

    # Flask-Security Fields
    active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("1"))
    fs_uniquifier: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    # Optional password field (unused since OAuth is the driver; marked nullable)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())

    # One-to-One relationship with UserTokenRecord
    token: Mapped[UserTokenRecord | None] = relationship(back_populates="user", uselist=False)

    # Roles relationship
    roles: Mapped[list[Role]] = relationship(
        "Role", secondary=roles_users, backref="users"
    )

    # Flask-Security compatibility getters
    @property
    def id(self) -> int:
        return self.user_id
```

#### Potential issues
* **Database migrations for SQLite vs MySQL:** The `fs_uniquifier` must be populated for pre-existing users. We can write an Alembic script that generates a random `uuid.uuid4().hex` for all existing users.
* **MRO Conflict:** `db.Model` already inherits from `BaseModel`. To avoid MRO issues, inherit exactly as `class UserRecord(db.Model, UserMixin)`.

#### Verification steps
Create database tables using test configurations and inspect constraints:
```bash
python -m pytest tests/unit/test_extensions.py
```

---

### Phase 3: Security Initialisation & Custom UserDatastore

#### Why this step is needed
Initializes `Security` within the Flask app factory (`create_app`) and establishes a custom `SQLAlchemyUserDatastore` that bridges user identifiers properly.

#### Files that need modification
* `src/main_app/extensions/__init__.py`
* `src/main_app/__init__.py`

#### Expected code changes

##### In `src/main_app/extensions/__init__.py`:
```python
from flask_security import Security, SQLAlchemyUserDatastore

security = Security()
```

##### In `src/main_app/__init__.py`:
```python
from .extensions import security
from .db.models.users import UserRecord, Role

def init_app_and_db(app, _db) -> bool:
    _db.init_app(app)
    migrate.init_app(app, _db)

    # Setup Flask-Security datastore
    user_datastore = SQLAlchemyUserDatastore(_db, UserRecord, Role)
    security.init_app(app, user_datastore)

    # Store reference on app for global access
    app.user_datastore = user_datastore
    ...
```

#### Verification steps
Ensure Flask-Security initializes without circular import problems. Start development server locally and monitor initialization outputs.

---

### Phase 4: Decorator & Route Bridge

#### Why this step is needed
Maps existing custom authentication and authorization decorators directly to the standard Flask-Security-Too implementations.

#### Decorator Mapping Table

| Custom Decorator | Flask-Security Equivalent | Architectural Difference & Notes |
| :--- | :--- | :--- |
| `@oauth_required` | `@auth_required("session", "token")` | Ensures session identity or valid API tokens are present. Handles automated login redirection. |
| `@user_login_required`| `@login_required` | Blocks access for non-authenticated requests; redirects to customizable login endpoint or flashes error. |
| `@admin_required` | `@roles_required("admin")` | Checks for membership in the `"admin"` role. Restricts view access instantly with standard `403` handling. |
| `can_run_jobs` check | `@permissions_required("run_jobs")` | Flask-Security features permission-based string checks on active User objects. |
| `can_run_bg_jobs` check| `@permissions_required("run_bg_jobs")`| Simplifies conditional checks down to explicit permissions rather than hard-coded model columns. |

#### Complete Before/After Refactoring Code Examples

##### Case 1: Custom `@admin_required` Refactoring
###### Before (`src/main_app/admin/decorators.py`):
```python
def admin_required(view: FuncType) -> FuncType:
    @wraps(view)
    def wrapped(*args, **kwargs):
        user: CurrentUser | None = load_user()
        if not user:
            return redirect(url_for("auth.login"))
        if not user.is_active_admin:
            logger.warning("User %s tried to access admin-only route", user.username)
            abort(403)
        return view(*args, **kwargs)
    return cast(FuncType, wrapped)
```

###### After (Recommended Flask-Security Replacement):
```python
from flask_security import roles_required

# In routes:
@bp_admin.route("/", methods=["GET"])
@roles_required("admin")
def admin_dashboard() -> str:
    ...
```
*Why this replacement is correct:* By leveraging `@roles_required("admin")`, we eliminate manual user checking, standardise logging, and offload session lookup to the underlying security package.

---

##### Case 2: `@oauth_required` Refactoring
###### Before (`src/main_app/public/auth/utils.py`):
```python
def oauth_required(func: FuncType) -> FuncType:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        user = load_user()
        if not user:
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return cast(FuncType, wrapper)
```

###### After (Recommended Flask-Security Replacement):
```python
from flask_security import auth_required

# In routes:
@bp_newupdater.route("/update", methods=["GET"])
@auth_required()
def newupdater() -> str | Response:
    ...
```
*Why this replacement is correct:* `@auth_required` guarantees active authentication. If combined with a custom security login entry point, it matches the native behavior of `post_login_redirect` out-of-the-box.

---

### Phase 5: OAuth Login Integration & Datastore Bindings

#### Why this step is needed
Since we use MediaWiki OAuth, registration and initial verification happen externally. After Meta-Wiki redirects back to our application, we must load the authenticated user record and register their session with Flask-Security.

#### Files that need modification
* `src/main_app/shared/auth/auth_users_service.py`
* `src/main_app/public/auth/routes.py`

#### Expected code changes
When the OAuth callback finishes successfully, register the logged-in state with Flask-Security using `login_user()`:

##### Before (`src/main_app/public/auth/routes.py`):
```python
            # Set sessions
            session["uid"] = user_id
            session["username"] = user_record.username

            # Set response and cookies
            response = make_response(redirect(session.pop("post_login_redirect", url_for("main.index"))))
            _set_response_cookies(user_id, response)
```

##### After (Recommended Flask-Security Integration):
```python
            from flask_security import login_user
            import uuid

            # 1. Fetch user from custom database
            user_record = AuthUserService.save_and_get_user_db_instance(username)

            # 2. Ensure fs_uniquifier exists
            if not user_record.fs_uniquifier:
                user_record.fs_uniquifier = uuid.uuid4().hex
                db.session.commit()

            # 3. Synchronize roles
            # Sync existing Coordinator (AdminUserRecord) status with the Flask-Security Role structure
            admin_role = app.user_datastore.find_or_create_role(name="admin")
            if AuthUserService.is_active_coordinator(username):
                if admin_role not in user_record.roles:
                    app.user_datastore.add_role_to_user(user_record, admin_role)
            else:
                if admin_role in user_record.roles:
                    app.user_datastore.remove_role_from_user(user_record, admin_role)

            # 4. Authenticate the session via Flask-Security
            login_user(user_record, remember=True)
            db.session.commit()
```

#### Potential issues
* Flask-Security `current_user` relies on a proxy object. Existing references to local user parameters like `user.can_run_jobs` should now map to standard properties or permission checks on the active user proxy.

---

### Phase 6: Post-Migration Cleanup

#### Why this step is needed
Removes redundant files, legacy decorators, obsolete cookie verifiers, and unnecessary session overrides to reduce architectural debt.

#### Files that need deletion
* `src/main_app/admin/decorators.py` (Fully replaced by `@roles_required`)
* Legacy references to `load_logged_in_user` and `oauth_required` in `src/main_app/public/auth/utils.py`

---

## 6. Risk Analysis & Fallback/Rollback Strategy

| Phase | Core Risk | Mitigation Strategy | Rollback Action |
| :--- | :--- | :--- | :--- |
| **Phase 1: Dependencies** | Package version mismatch or installation error | Install explicit dependencies under isolation | Revert additions to `requirements.txt` and execute environment clean |
| **Phase 2: Schema Modification**| Database migration fails on existing MySQL schema | Run safe migration dry-runs first, keeping schema non-restrictive | Revert alembic migration step and restore database using snapshot |
| **Phase 3: Security Setup** | Circular application imports during Flask startup | Ensure Flask-Security initialization is decoupled from app-context models | Revert factory-level initialization in `create_app` |
| **Phase 4: Decorators** | Users lockouts due to missing or mismatched roles | Add diagnostic logs on unauthorized callbacks | Revert decorators to custom `@admin_required` references |
| **Phase 5: OAuth Login Bind**| OAuth login flows break, causing Meta-Wiki verification to fail | Keep dual-session bindings (both `session["uid"]` and `login_user`) temporarily | Bypass `login_user` check and fallback to explicit `session["uid"]` |

---

## 7. Testing Strategy

### Unit Testing Custom User Databases
Create a mock test case utilizing SQLite to verify the security mappings:
```python
def test_flask_security_user_datastore(mock_app):
    with mock_app.app_context():
        # 1. Access security datastore
        ds = mock_app.extensions["security"].datastore

        # 2. Add User and assign Role
        user = ds.create_user(username="test_user", fs_uniquifier="unique-123")
        role = ds.find_or_create_role(name="admin")
        ds.add_role_to_user(user, role)

        # 3. Assert relations are populated correctly
        assert "admin" in [r.name for r in user.roles]
```

### Integration & Manual Verification
1. Run `python -m pytest` inside the sandbox workspace to ensure zero regressions across old suites.
2. Run automated verification scripts simulating login callbacks to ensure user profiles are stored correctly under both legacy session parameters and security proxies.

---

## 8. Final Recommendations & Best Practices

1. **Security Hashing:** Always ensure that password hashing salts are populated via strong env variables in production configuration even if passwords are not utilized due to standard OAuth practices.
2. **Modular Architecture:** Keep OAuth logic entirely in the `auth` module and avoid importing Flask-Security components directly inside core DB services, maintaining a strict separation of concerns.
3. **Session Verification:** Utilize token-based cookie validation configurations in production tool servers to guarantee instant session termination on Toolforge when a user terminates their authorization.
