# Dependency Injection

Lightweight, explicit dependency injection for `main_app` services.

## Design

- **Constructor injection** is the primary style.
- A small `Container` holds factories / singletons.
- No third-party DI library is required.
- Easy to override in tests via `container.override(...)`.

## Quick usage

### 1. Wire the container in `create_app`

```python
from .di import init_container, ServiceProviders
from .di.flask_integration import init_di

def create_app(config_class: type) -> Flask:
    app = Flask(...)
    # ... existing config, db, csrf ...

    container = init_container()
    ServiceProviders.register_all(
        container,
        app=app,
        settings=settings,
        db=_db,
    )
    init_di(app, container)

    # ... register blueprints, etc.
    return app
```

### 2. Inject into services (preferred)

```python
class AuthUsersNewService:
    def __init__(
        self,
        users_service: UsersService,
        user_token_service: UserTokenService,
        admin_service: AdminService,
    ) -> None:
        self.users_service = users_service
        self.user_token_service = user_token_service
        self.admin_service = admin_service
```

### 3. Resolve only when constructor injection is impossible

```python
from main_app.di.flask_integration import resolve
from main_app.database.services import JobsService

jobs = resolve(JobsService)
```

### 4. Tests

```python
def test_something(container):
    fake = FakeUsersService()
    container.override(UsersService, fake)
    svc = container.resolve(AuthUsersNewService)
    ...
```

## Migration strategy

1. Add the `di/` package (this code).
2. Change service `__init__` methods to accept collaborators.
3. Register factories in `ServiceProviders`.
4. Update call sites gradually (routes, workers, CLI).
5. Remove remaining `Service()` zero-arg constructions.
