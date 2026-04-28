"""Flask application factory for the Harare Darts Association website."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import inspect, text

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app():
    """Create and configure the Flask application."""
    # Calculate absolute paths for static and template folders
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
        static_url_path='/static'
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

    # Create tables and ensure the latest columns exist
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()
        _ensure_schema(app)

        # Create default admin users if they don't exist
        _seed_defaults(app)

    return app


def _ensure_schema(app):
    """Ensure schema additions are present in existing databases."""
    inspector = inspect(db.engine)
    with db.engine.begin() as conn:
        if inspector.has_table('player_game_week_stats'):
            existing = {col['name'] for col in inspector.get_columns('player_game_week_stats')}
            if 'one_seventies' not in existing:
                conn.execute(text('ALTER TABLE player_game_week_stats ADD COLUMN one_seventies INTEGER DEFAULT 0'))
        if inspector.has_table('results'):
            existing = {col['name'] for col in inspector.get_columns('results')}
            if 'one_seventies_scored' not in existing:
                conn.execute(text('ALTER TABLE results ADD COLUMN one_seventies_scored TEXT'))
        if inspector.has_table('tournaments'):
            existing = {col['name'] for col in inspector.get_columns('tournaments')}
            if 'results' not in existing:
                conn.execute(text('ALTER TABLE tournaments ADD COLUMN results TEXT'))
            if 'is_trials' not in existing:
                conn.execute(text('ALTER TABLE tournaments ADD COLUMN is_trials BOOLEAN DEFAULT FALSE'))
            if 'results_data' not in existing:
                conn.execute(text('ALTER TABLE tournaments ADD COLUMN results_data TEXT'))
            if 'tournament_type' not in existing:
                conn.execute(text("ALTER TABLE tournaments ADD COLUMN tournament_type VARCHAR(50) DEFAULT 'standard'"))


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
