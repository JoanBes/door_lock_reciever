from flask import Flask

from app import config
from app.database import close_db, init_db
from app.routes import register_routes


def create_app():
    app = Flask(
        __name__,
        template_folder=str(config.BASE_DIR / "templates"),
        static_folder=str(config.BASE_DIR / "static"),
    )
    app.teardown_appcontext(close_db)
    app.config.update(
        SECRET_KEY=config.load_secret_key(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    init_db().close()
    register_routes(app)
    return app
