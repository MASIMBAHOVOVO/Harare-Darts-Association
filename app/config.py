"""Flask application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hda-dev-secret-key-change-in-production')

    database_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    
    # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Use DATABASE_URL env var for PostgreSQL, fallback to SQLite for local dev
    SQLALCHEMY_DATABASE_URI = database_url or (
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
