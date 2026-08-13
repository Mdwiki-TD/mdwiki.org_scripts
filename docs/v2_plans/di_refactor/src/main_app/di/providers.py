"""Central registration of all application services.

Call ``ServiceProviders.register_all(container, ...)`` from ``create_app``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .container import Container

if TYPE_CHECKING:
    from flask import Flask


class ServiceProviders:
    """Registers concrete implementations into the container."""

    @staticmethod
    def register_all(
        container: Container,
        *,
        app: Flask | None = None,
        settings: Any = None,
        db: Any = None,
    ) -> None:
        """Wire every known service.

        Parameters are optional so unit tests can register only what they need.
        """
        # Late imports avoid circular dependencies at module load time.
        from ..database.services.admin_service import AdminService
        from ..database.services.jobs_service import JobsService
        from ..database.services.settings_service import SettingsService
        from ..database.services.user_token_service import UserTokenService
        from ..database.services.users_service import UsersService
        from ..shared.auth.auth_users_service import AuthUsersNewService

        # ----- persistence / DB services (singletons per app) -----
        container.register_factory(UsersService, lambda: UsersService())
        container.register_factory(UserTokenService, lambda: UserTokenService())
        container.register_factory(AdminService, lambda: AdminService())
        container.register_factory(JobsService, lambda: JobsService())
        container.register_factory(SettingsService, lambda: SettingsService())

        # ----- auth application service -----
        def _auth_users_factory() -> AuthUsersNewService:
            return AuthUsersNewService(
                users_service=container.resolve(UsersService),
                user_token_service=container.resolve(UserTokenService),
                admin_service=container.resolve(AdminService),
            )

        container.register_factory(AuthUsersNewService, _auth_users_factory)

        # ----- content application services (example) -----
        # Uncomment / adapt once the application layer is extracted:
        #
        # from ..application.content.fix_redirects import FixRedirectsService
        # from ..application.content.medical_updater import MedicalUpdaterService
        #
        # container.register_factory(
        #     FixRedirectsService,
        #     lambda: FixRedirectsService(
        #         settings=settings,
        #         # site_factory injected later
        #     ),
        # )

        # Store settings & db on the container for services that still need them
        # during the transition period.
        if settings is not None:
            container.register_singleton(type(settings), settings)
        if db is not None:
            container.register_singleton(type(db), db)
