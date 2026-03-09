"""Remove duplicate team names from the database, keeping the team with the most data."""
import sys
import os
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Team, Player, User, Fixture, MatchDetail

app = create_app()

def count_team_data(team):
    """Count the amount of data associated with a team."""
    count = 0
    count += len(team.players)
    count += User.query.filter_by(team_id=team.id).count()
    count += MatchDetail.query.filter(
        db.or_(
            MatchDetail.home_team_id == team.id,
            MatchDetail.away_team_id == team.id
        )
    ).count()
    count += Fixture.query.filter(
        db.or_(
            Fixture.home_team_number == team.team_number,
            Fixture.away_team_number == team.team_number
        )
    ).count()
    return count

def remove_duplicate_teams():
    """Find and remove duplicate team names, keeping the one with most data."""
    with app.app_context():
        # Group teams by name (case-insensitive)
        teams_by_name = defaultdict(list)
        all_teams = Team.query.all()
        
        for team in all_teams:
            key = team.name.lower().strip() if team.name else ""
            teams_by_name[key].append(team)
        
        # Find duplicates
        duplicates = {name: teams for name, teams in teams_by_name.items() if len(teams) > 1}
        
        if not duplicates:
            print("✓ No duplicate team names found!")
            return
        
        print(f"\nFound {len(duplicates)} duplicate team names:\n")
        
        total_deleted = 0
        
        for name_key, teams in duplicates.items():
            print(f"  Team name: '{teams[0].name}'")
            print(f"  Found {len(teams)} teams with this name:")
            
            # Score each team by the amount of associated data
            teams_scored = []
            for team in teams:
                data_count = count_team_data(team)
                teams_scored.append((team, data_count))
            
            # Sort by data count descending
            teams_scored.sort(key=lambda x: x[1], reverse=True)
            
            # Keep the first one (most data)
            keeper = teams_scored[0][0]
            to_delete = teams_scored[1:]
            
            print(f"    • Keeping: ID={keeper.id}, Data points: {teams_scored[0][1]}")
            print(f"      (Team#{keeper.team_number}, Captain: {keeper.captain_name})")
            
            # Delete the rest
            for team, data_count in to_delete:
                print(f"    • Deleting: ID={team.id}, Data points: {data_count}")
                print(f"      (Team#{team.team_number}, Captain: {team.captain_name})")
                
                # Clean up foreign key references
                # Update players to point to keeper team
                Player.query.filter_by(team_id=team.id).update({'team_id': keeper.id})
                
                # Update users to point to keeper team
                User.query.filter_by(team_id=team.id).update({'team_id': keeper.id})
                
                # Delete the duplicate team
                db.session.delete(team)
                total_deleted += 1
            
            print()
        
        # Commit all changes
        db.session.commit()
        print(f"✓ Successfully removed {total_deleted} duplicate team(s)!\n")

if __name__ == '__main__':
    remove_duplicate_teams()

