import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import Team

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    teams = Team.query.all()
    print(f'Clearing standings for {len(teams)} teams...')

    for team in teams:
        team.played = 0
        team.won = 0
        team.lost = 0
        team.doubles = 0
        team.singles = 0
        team.scores = 0
        team.points = 0

    db.session.commit()
    print('Done! All team standings have been reset to zero.')
    print('New standings will be calculated when results are approved.')
