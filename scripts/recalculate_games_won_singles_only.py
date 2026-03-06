import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import MatchDetail, PlayerGameWeekStats, Fixture

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

with app.app_context():
    print("Recalculating player stats from match details (singles TLW only)...")
    
    # clear all player stats
    PlayerGameWeekStats.query.delete()
    db.session.commit()
    print("Cleared existing player stats.")
    
    # iterate all match details
    matches = MatchDetail.query.all()
    updated = 0
    
    for md in matches:
        # get fixture and game week
        result = md.result
        if not result or not result.fixture:
            continue
        
        fixture = result.fixture
        gw_num = fixture.game_week.week_number if fixture.game_week else 0
        
        # only count singles
        if md.match_type == 'single':
            # home player
            if md.home_player1_id:
                stats = PlayerGameWeekStats.query.filter_by(
                    player_id=md.home_player1_id, game_week=gw_num
                ).first()
                if not stats:
                    stats = PlayerGameWeekStats(player_id=md.home_player1_id, game_week=gw_num)
                    db.session.add(stats)
                stats.games_played = (stats.games_played or 0) + 1
                stats.games_won = (stats.games_won or 0) + (md.home_legs_won or 0)
                updated += 1
            
            # away player
            if md.away_player1_id:
                stats = PlayerGameWeekStats.query.filter_by(
                    player_id=md.away_player1_id, game_week=gw_num
                ).first()
                if not stats:
                    stats = PlayerGameWeekStats(player_id=md.away_player1_id, game_week=gw_num)
                    db.session.add(stats)
                stats.games_played = (stats.games_played or 0) + 1
                stats.games_won = (stats.games_won or 0) + (md.away_legs_won or 0)
                updated += 1
    
    db.session.commit()
    print(f"Recalculated stats for {updated} player-matches (singles only).")
    print("Done! Games Won now reflects only singles TLW.")
