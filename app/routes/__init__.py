from app.routes import auth, cards, events, overview, pages


def register_routes(app):
    for module in (pages, auth, overview, events, cards):
        app.register_blueprint(module.bp)
