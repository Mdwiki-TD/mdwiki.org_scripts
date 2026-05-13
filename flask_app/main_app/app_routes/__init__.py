"""

"""

from flask import Flask

from .main import bp_main
from .dup import bp_dup


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_dup)


__all__ = [
    "register_blueprints",
]
