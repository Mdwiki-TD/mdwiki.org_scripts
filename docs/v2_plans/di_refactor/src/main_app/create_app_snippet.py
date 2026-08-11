"""
Illustration of how to wire DI inside the existing create_app factory.

Copy the relevant parts into src/main_app/__init__.py.
"""

from __future__ import annotations

from typing import Any

from flask import Flask

# --- existing imports remain ---
# from .config import ensure_directories, settings
# from .db import init_db
# from .extensions import csrf_init_app, db as _db, migrate
# ...


def create_app(config_class: type) -> Flask:
    if config_class is None:
        raise ValueError("config_class must be provided")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.url_map.strict_slashes = False
    app.config.from_object(config_class())

    # ----- existing initialisation (csrf, db, migrate, …) -----
    # csrf_init_app(app)
    # ...

    # ----- NEW: dependency injection -----
    from .di import ServiceProviders, init_container
    from .di.flask_integration import init_di

    container = init_container()
    ServiceProviders.register_all(
        container,
        app=app,
        settings=None,  # pass the real settings object
        db=None,  # pass the real SQLAlchemy instance
    )
    init_di(app, container)

    # Optional: register content services once the application layer exists
    # from .application.content.fix_redirects import FixRedirectsService
    # from .application.content.medical_updater import MedicalUpdaterService
    # from .api_services import MwClientPage
    # from .api_services.clients.wiki_client import get_user_site
    # from .domain.wikitext.redirects import work_on_text, RunState
    # from .domain.wikitext.medical import med_updater_one
    # from .domain.wikitext.named_param import add_param_named
    #
    # container.register_factory(
    #     FixRedirectsService,
    #     lambda: FixRedirectsService(
    #         site_factory=get_user_site,
    #         page_factory=lambda title, site: MwClientPage(title, site),
    #         work_on_text=work_on_text,
    #         run_state_factory=RunState,
    #     ),
    # )
    # container.register_factory(
    #     MedicalUpdaterService,
    #     lambda: MedicalUpdaterService(
    #         site_factory=get_user_site,
    #         page_factory=lambda title, site: MwClientPage(title, site),
    #         med_updater_one=med_updater_one,
    #         add_param_named=add_param_named,
    #     ),
    # )

    # ----- rest of existing create_app (blueprints, error pages, …) -----
    # ensure_directories()
    # register_error_pages(app)
    # ...

    return app


# Example route that uses constructor-injected service via resolve
# (prefer injecting into a thin controller / route class when possible)
def example_view() -> Any:
    from .application.content.fix_redirects import FixRedirectsService
    from .di.flask_integration import resolve
    from .public.auth.utils import load_user

    user = load_user()
    svc = resolve(FixRedirectsService)
    outcome = svc.run(
        title="Example",
        save=False,
        user_payload=user.to_auth_payload() if user else None,
    )
    return outcome.to_json()
