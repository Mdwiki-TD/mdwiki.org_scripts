**Dependency injection is implemented** as a ready-to-apply package under:

`/home/workdir/artifacts/di_refactor/`

### What you get

| Path | Purpose |
|------|---------|
| `src/main_app/di/container.py` | Lightweight `Container` (singleton / factory / transient, thread-safe) |
| `src/main_app/di/providers.py` | Central registration of DB + auth services |
| `src/main_app/di/flask_integration.py` | `init_di(app)` + `resolve(Interface)` helper |
| `src/main_app/shared/auth/auth_users_service.py` | Refactored for **constructor injection** + backward-compatible façade |
| `src/main_app/application/content/fix_redirects.py` | Example use-case with injected ports |
| `src/main_app/application/content/medical_updater.py` | Same pattern for the medical updater |
| `src/main_app/create_app_snippet.py` | Exact wiring to drop into `create_app` |
| `tests/test_container.py` | Unit tests for the container |
| `IMPLEMENTATION.md` | Step-by-step integration guide |

### Design (practical, not over-engineered)

- **Constructor injection** is the primary style.
- Small in-house container — no extra dependency.
- Optional zero-arg fallbacks so existing `Service()` calls keep working during migration.
- Flask integration via `app.extensions["di_container"]` + process-wide fallback for CLI/workers.
- Easy test overrides: `container.override(UsersService, FakeUsersService())`.

### Minimal integration in `create_app`

```python
from .di import ServiceProviders, init_container
from .di.flask_integration import init_di

container = init_container()
ServiceProviders.register_all(container, app=app, settings=settings, db=_db)
init_di(app, container)
```

### Example of a refactored service

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

Factories in `providers.py` wire the real graph:

```python
container.register_factory(
    AuthUsersNewService,
    lambda: AuthUsersNewService(
        users_service=container.resolve(UsersService),
        user_token_service=container.resolve(UserTokenService),
        admin_service=container.resolve(AdminService),
    ),
)
```

### Migration order

1. Copy `di/` into the real repo and wire it in `create_app`.
2. Add constructor parameters (with fallbacks) to existing services.
3. Register them in `ServiceProviders`.
4. Switch call sites gradually (`resolve(...)` or inject into route/worker classes).
5. Remove fallbacks and static façades once everything goes through the container.

Full details and next steps are in `artifacts/di_refactor/IMPLEMENTATION.md`.
