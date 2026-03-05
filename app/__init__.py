"""Flask application factory for the Harare Darts Association website."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
    app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Create tables
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

        # Create default admin users if they don't exist
        _seed_defaults(app)

    return app


def _seed_defaults(app):
    """Seed default users and sample data if database is empty."""
    from app.models import User
    from werkzeug.security import generate_password_hash

    if User.query.first() is None:
        defaults = [
            User(
                username='secretary',
                password_hash=generate_password_hash('hda2024sec'),
                role='secretary_general',
                full_name='Secretary General'
            ),
            User(
                username='fixture_sec',
                password_hash=generate_password_hash('hda2024fix'),
                role='fixture_secretary',
                full_name='Fixture Secretary'
            ),
            User(
                username='captain1',
                password_hash=generate_password_hash('hda2024cap'),
                role='captain',
                full_name='Team Captain Demo'
            ),
        ]
        for user in defaults:
            db.session.add(user)
        db.session.commit()
