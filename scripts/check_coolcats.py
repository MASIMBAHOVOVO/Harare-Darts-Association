import sys, os
sys.path.insert(0, '.')
from app import create_app, db
from app.models import Fixture, Result, Team, GameWeek

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    print("=== Database Check ===")
    
    # Count fixtures and results
    f_count = db.session.query(Fixture).count()
    r_count = db.session.query(Result).count()
    p_count = db.session.query(Result).filter_by(approved=False).count()
    print(f"Fixtures: {f_count}")
    print(f"Results: {r_count}")
    print(f"Pending Results: {p_count}")
    
    # Check Coolcats
    coolcats = db.session.query(Team).filter_by(name='Coolcats').first()
    if coolcats:
        print(f"\nCoolcats (Team #{coolcats.team_number}):")
        
        # Fixtures where Coolcats is home
        home_fixtures = db.session.query(Fixture).filter_by(home_team_number=coolcats.team_number).all()
        print(f"  Home fixtures: {len(home_fixtures)}")
        for f in home_fixtures[:3]:
            gw = db.session.query(GameWeek).get(f.game_week_id)
            result = db.session.query(Result).filter_by(fixture_id=f.id).first()
            print(f"    Fixture {f.id} (GW {gw.week_number if gw else '?'}): is_played={f.is_played}, result={result.id if result else 'None'}, " + (f"approved={result.approved}" if result else ""))
        
        # Fixtures where Coolcats is away
        away_fixtures = db.session.query(Fixture).filter_by(away_team_number=coolcats.team_number).all()
        print(f"  Away fixtures: {len(away_fixtures)}")
        for f in away_fixtures[:3]:
            gw = db.session.query(GameWeek).get(f.game_week_id)
            result = db.session.query(Result).filter_by(fixture_id=f.id).first()
            print(f"    Fixture {f.id} (GW {gw.week_number if gw else '?'}): is_played={f.is_played}, result={result.id if result else 'None'}, " + (f"approved={result.approved}" if result else ""))
