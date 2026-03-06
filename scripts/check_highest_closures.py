import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import Result

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    bad = Result.query.filter((Result.highest_close > 0) | (Result.highest_close_player != None)).all()
    print(f"Results with highest close info: {len(bad)}")
    for r in bad:
        print(r.id, r.highest_close, r.highest_close_player)
