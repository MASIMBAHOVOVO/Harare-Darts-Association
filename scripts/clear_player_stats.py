import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import PlayerGameWeekStats

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    count = PlayerGameWeekStats.query.count()
    print(f'Deleting {count} corrupted player stat records...')
    PlayerGameWeekStats.query.delete()
    db.session.commit()
    print('Done. Player stats cleared. Fresh data will be calculated when results are approved.')
