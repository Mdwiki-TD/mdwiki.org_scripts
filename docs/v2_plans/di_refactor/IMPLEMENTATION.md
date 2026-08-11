# Dependency Injection — Implementation Guide

## What was added

```
src/main_app/di/
├── __init__.py
├── container.py          # Container, init/get/reset helpers
├── providers.py          # ServiceProviders.register_all(...)
├── flask_integration.py  # init_di(app), resolve(Interface)
└── README.md

src/main_app/application/content/
├── fix_redirects.py      # FixRedirectsService (constructor-injected)
└── medical_updater.py    # MedicalUpdaterService (constructor-injected)

src/main_app/domain/
└── shared_classes.py     # UpdaterTextOutcome (domain DTO)

src/main_app/shared/auth/
└── auth_users_service.py # Refactored for constructor injection + backward-compatible façade
```

## Integration steps (in the real repo)

### 1. Copy the `di/` package
```bash
cp -r artifacts/di_refactor/src/main_app/di src/main_app/
```

### 2. Wire the container in `create_app` (`src/main_app/__init__.py`)

Add after config / extensions init and before blueprint registration:

```python
from .di import ServiceProviders, init_container
from .di.flask_integration import init_di

container = init_container()
ServiceProviders.register_all(
    container,
    app=app,
    settings=settings,
    db=_db,
)
init_di(app, container)
```

### 3. Update service constructors (pattern)

**Before**
```python
class AuthUsersNewService:
    def __init__(self) -> None:
        self.users_service = UsersService()
        self.user_token_service = UserTokenService()
        self.admin_service = AdminService()
```

**After**
```python
class AuthUsersNewService:
    def __init__(
        self,
        users_service: UsersService | None = None,
        user_token_service: UserTokenService | None = None,
        admin_service: AdminService | None = None,
    ) -> None:
        self.users_service = users_service or UsersService()
        self.user_token_service = user_token_service or UserTokenService()
        self.admin_service = admin_service or AdminService()
```

The `or Xxx()` fallbacks keep existing call sites working during migration.
Remove them once every construction goes through the container.

### 4. Register factories in `providers.py`

Already done for:
- `UsersService`, `UserTokenService`, `AdminService`, `JobsService`, `SettingsService`
- `AuthUsersNewService` (depends on the three above)

Add content services once the application layer is in place (see commented example in `create_app_snippet.py`).

### 5. Update call sites gradually

| Location | Change |
|----------|--------|
| Route handlers / admin classes | Prefer `resolve(Service)` or inject into the route class constructor |
| Workers | Receive services via constructor from the job runner |
| Static façades (`AuthUserService`) | Delegate to the container (already shown) |
| Tests | `container.override(UsersService, FakeUsersService())` |

### 6. Tests

Copy `tests/test_container.py` and run:

```bash
pytest tests/test_container.py -q
```

For service tests:

```python
def test_auth_users(container):
    container.override(UsersService, FakeUsersService())
    svc = container.resolve(AuthUsersNewService)
    ...
```

## Design choices

| Choice | Rationale |
|--------|-----------|
| No third-party DI library | Keeps the dependency surface small; matches the project’s style |
| Constructor injection first | Explicit, easy to type-check and test |
| Optional zero-arg fallbacks | Zero-downtime migration |
| `resolve()` helper | Escape hatch for Flask views / CLI during transition |
| Process-wide + app.extensions | Works for web requests, CLI jobs, and background workers |

## Next recommended steps

1. Apply the same constructor-injection pattern to `JobsService`, `SettingsService`, and admin route classes.
2. Finish extracting `domain/wikitext` and register `FixRedirectsService` / `MedicalUpdaterService`.
3. Remove the zero-arg fallbacks and the static `AuthUserService` façade.
4. Consider request-scoped services later if needed (the teardown hook is already prepared).
