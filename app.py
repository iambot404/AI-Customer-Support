import os
from flask import Flask, render_template, session
from config import Config
from database.db import init_db, get_user_by_id
from routes.auth import auth_bp
from routes.tickets import tickets_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize the database schema
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            app.logger.error(f"Error initializing database: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)

    # Context processor to inject current user into all templates
    @app.context_processor
    def inject_user():
        user_id = session.get("user_id")
        current_user = get_user_by_id(user_id) if user_id else None
        return {"current_user": current_user}

    # Custom 404 handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    # Custom 500 handler
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("404.html", error_message="An internal server error occurred."), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f">> AI Ticket Classifier running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
