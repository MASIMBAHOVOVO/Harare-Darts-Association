"""Flask application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hda-dev-secret-key-change-in-production')

    # Use DATABASE_URL or POSTGRES_URL for MySQL/Postgres, fallback to SQLite for local dev
    _uri = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    if _uri and _uri.startswith("postgres://"):
        _uri = _uri.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = _uri or (
        'sqlite:///' + os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'hda.db'
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
