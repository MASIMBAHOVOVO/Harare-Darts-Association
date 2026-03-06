from app import create_app, db
from app.models import Team, User, Fixture, Result, GameWeek
import os

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    # Get Coolcats team
    coolcats = Team.query.filter_by(name='Coolcats').first()
    print(f"\n=== Team: {coolcats.name if coolcats else 'Not found'} ===")
    if coolcats:
        print(f"Team Number: {coolcats.team_number}")
        print(f"Users: {[u.username for u in coolcats.users]}")
        
        # Get all fixtures for Coolcats
        fixtures = Fixture.query.filter(
            ((Fixture.home_team_number == coolcats.team_number) | 
             (Fixture.away_team_number == coolcats.team_number)) &
            (Fixture.is_bye == False)
        ).all()
        
        print(f"\nTotal fixtures for Coolcats: {len(fixtures)}")
        
        for i, fixture in enumerate(fixtures[:10]):
            home = Team.query.filter_by(team_number=fixture.home_team_number).first()
            away = Team.query.filter_by(team_number=fixture.away_team_number).first()
            gw = GameWeek.query.get(fixture.game_week_id)
            result = Result.query.filter_by(fixture_id=fixture.id).first()
            
            print(f"\nFixture {i+1}:")
            print(f"  {fixture.home_team_number} {home.name if home else '?'} vs {fixture.away_team_number} {away.name if away else 'Bye'}")
            print(f"  GameWeek: {gw.week_number if gw else 'None'}")
            print(f"  is_played: {fixture.is_played}")
            print(f"  Result: {result.id if result else 'None'}")
            if result:
                print(f"  Result approved: {result.approved}")
                print(f"  Result status: {result.status}")
    
    # Check for pending results overall
    print(f"\n=== All Pending Results ===")
    pending = Result.query.filter_by(approved=False).all()
    print(f"Total pending results: {len(pending)}")
    for r in pending[:5]:
        fixture = Fixture.query.get(r.fixture_id)
        if fixture:
            gw = GameWeek.query.get(fixture.game_week_id)
            print(f"  Fixture {fixture.id} (GW {gw.week_number if gw else '?'}): Status={r.status}, Approved={r.approved}")
