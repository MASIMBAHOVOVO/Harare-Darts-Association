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
    
    # Optimized connection pooling for high concurrency (100+ users)
    # pool_size: base number of connections kept in the pool (default: 5)
    # max_overflow: maximum overflow connections beyond pool_size (default: 10)
    # pool_recycle: recycle connections after this many seconds (prevent timeouts)
    # pool_pre_ping: test connections before using them (detect dead connections)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,          # Increased from default 5 to handle more concurrent requests
        'max_overflow': 40,       # Allow up to 60 total connections (20 + 40)
        'pool_recycle': 280,      # Recycle connections every ~4.5 minutes
        'pool_pre_ping': True,    # Test connections before use
        'pool_timeout': 30,       # Wait up to 30 seconds for a connection
        'echo_pool': False,       # Set to True for debugging pool issues
    }
