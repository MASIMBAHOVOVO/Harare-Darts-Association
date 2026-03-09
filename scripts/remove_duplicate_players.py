"""Remove duplicate player names from the database, keeping the player with the most data."""
import sys
import os
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Player, PlayerGameWeekStats, MatchDetail

app = create_app()

def count_player_data(player):
    """Count the amount of data associated with a player."""
    count = 0
    # Count game week stats
    count += PlayerGameWeekStats.query.filter_by(player_id=player.id).count()
    # Count match details where player is involved
    count += MatchDetail.query.filter(
        db.or_(
            MatchDetail.home_player1_id == player.id,
            MatchDetail.home_player2_id == player.id,
            MatchDetail.away_player1_id == player.id,
            MatchDetail.away_player2_id == player.id
        )
    ).count()
    return count

def remove_duplicate_players():
    """Find and remove duplicate player names, keeping the one with most data."""
    with app.app_context():
        # Group players by name (case-insensitive)
        players_by_name = defaultdict(list)
        all_players = Player.query.all()
        
        for player in all_players:
            key = player.name.lower().strip() if player.name else ""
            players_by_name[key].append(player)
        
        # Find duplicates
        duplicates = {name: players for name, players in players_by_name.items() if len(players) > 1}
        
        if not duplicates:
            print("✓ No duplicate player names found!")
            return
        
        print(f"\nFound {len(duplicates)} duplicate player names:\n")
        
        total_deleted = 0
        
        for name_key, players in duplicates.items():
            print(f"  Player name: '{players[0].name}'")
            print(f"  Found {len(players)} players with this name:")
            
            # Score each player by the amount of associated data
            players_scored = []
            for player in players:
                data_count = count_player_data(player)
                players_scored.append((player, data_count))
            
            # Sort by data count descending
            players_scored.sort(key=lambda x: x[1], reverse=True)
            
            # Keep the first one (most data)
            keeper = players_scored[0][0]
            to_delete = players_scored[1:]
            
            print(f"    • Keeping: ID={keeper.id}, Data points: {players_scored[0][1]}")
            print(f"      (Team: {keeper.team.name if keeper.team else 'Unassigned'}, Payment: {keeper.payment_status})")
            
            # Delete the rest
            for player, data_count in to_delete:
                team_name = player.team.name if player.team else 'Unassigned'
                print(f"    • Deleting: ID={player.id}, Data points: {data_count}")
                print(f"      (Team: {team_name}, Payment: {player.payment_status})")
                
                # Update match details to point to keeper player
                MatchDetail.query.filter_by(home_player1_id=player.id).update({'home_player1_id': keeper.id})
                MatchDetail.query.filter_by(home_player2_id=player.id).update({'home_player2_id': keeper.id})
                MatchDetail.query.filter_by(away_player1_id=player.id).update({'away_player1_id': keeper.id})
                MatchDetail.query.filter_by(away_player2_id=player.id).update({'away_player2_id': keeper.id})
                
                # Update game week stats to point to keeper player
                PlayerGameWeekStats.query.filter_by(player_id=player.id).update({'player_id': keeper.id})
                
                # Delete the duplicate player
                db.session.delete(player)
                total_deleted += 1
            
            print()
        
        # Commit all changes
        db.session.commit()
        print(f"✓ Successfully removed {total_deleted} duplicate player(s)!\n")

if __name__ == '__main__':
    remove_duplicate_players()
