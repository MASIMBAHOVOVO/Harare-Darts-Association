from app import create_app, db
from app.models import Team
import os

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    teams = Team.query.all()
    print(f'Total teams: {len(teams)}')
    for team in teams[:5]:  # Show first 5 teams
        print(f'{team.name}: played={team.played}, won={team.won}, lost={team.lost}, points={team.points}')