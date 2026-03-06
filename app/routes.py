"""Public routes for the HDA website."""
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from app.models import (
    Tournament, Team, Fixture, Player, Document, Committee,
    GameWeek, PlayerGameWeekStats
)
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Homepage with upcoming tournament countdown."""
    tournaments = Tournament.query.filter_by(is_upcoming=True).order_by(Tournament.date.asc()).all()
    return render_template('home.html', tournaments=tournaments)


@main_bp.route('/standings')
def standings():
    """League standings table — Position, Team, Played, Won, Lost, Doubles, Singles, Scores, Points."""
    teams = Team.query.filter(Team.team_number.isnot(None)).order_by(
        Team.points.desc(),
        Team.scores.desc(),
        Team.won.desc()
    ).all()
    return render_template('standings.html', teams=teams, now=datetime.now())


@main_bp.route('/fixtures')
def fixtures():
    """Fixtures page with team key and game week dropdown."""
    # All teams with assigned numbers for the key
    teams = Team.query.filter(Team.team_number.isnot(None)).order_by(Team.team_number.asc()).all()

    # Get all game weeks
    game_weeks = GameWeek.query.order_by(GameWeek.week_number.asc()).all()

    # Determine which GW to show based on filter
    gw_filter = request.args.get('gw', 'current')
    today = datetime.now().date()

    if gw_filter == 'current':
        # Automated current week: find first gameweek >= today
        current_gw = GameWeek.query.filter(GameWeek.date >= today).order_by(GameWeek.date.asc()).first()
        if not current_gw:
            # If all are in the past, show the very last one
            current_gw = GameWeek.query.order_by(GameWeek.date.desc()).first()
        
        selected_weeks = [current_gw] if current_gw else []
    elif gw_filter == 'previous':
        selected_weeks = GameWeek.query.filter(GameWeek.date < today).order_by(
            GameWeek.week_number.asc()
        ).all()
    elif gw_filter == 'upcoming':
        selected_weeks = GameWeek.query.filter(GameWeek.date >= today).order_by(
            GameWeek.week_number.asc()
        ).all()
    else:
        # Specific week number
        try:
            wk = int(gw_filter)
            gw = GameWeek.query.filter_by(week_number=wk).first()
            selected_weeks = [gw] if gw else []
        except (ValueError, TypeError):
            selected_weeks = []

    # Build fixtures data per week
    weeks_data = []
    for gw in selected_weeks:
        gw_fixtures = Fixture.query.filter_by(game_week_id=gw.id).order_by(Fixture.id.asc()).all()
        weeks_data.append({
            'game_week': gw,
            'fixtures': gw_fixtures
        })

    return render_template(
        'fixtures.html',
        teams=teams,
        game_weeks=game_weeks,
        weeks_data=weeks_data,
        gw_filter=gw_filter,
        today=today
    )


@main_bp.route('/player-stats')
def player_stats():
    """Wall of Fame — per game week stats with dropdown."""
    stat_type = request.args.get('stat', 'games_won')  # games_won, highest_checkout, most_180s
    max_gw = 20

    if stat_type == 'highest_checkout':
        # Aggregate best checkout per player across all GWs
        from app import db
        # We use outerjoin to include players without stats
        stats_query = db.session.query(
            Player.name,
            Team.name.label('team_name'),
            func.coalesce(func.max(PlayerGameWeekStats.highest_checkout), 0).label('best_checkout'),
            func.coalesce(func.sum(PlayerGameWeekStats.games_played), 0).label('total_games')
        ).outerjoin(
            PlayerGameWeekStats, Player.id == PlayerGameWeekStats.player_id
        ).outerjoin(
            Team, Player.team_id == Team.id
        ).group_by(
            Player.id, Player.name, Team.name
        ).order_by(
            func.max(PlayerGameWeekStats.highest_checkout).desc(),
            func.sum(PlayerGameWeekStats.games_played).desc(),
            Player.name.asc()
        ).all()

        stats = []
        for row in stats_query:
            # use None for players with no games so we can push them after numeric values
            if row.total_games > 0:
                best_co = row.best_checkout
            else:
                best_co = None
            stats.append({
                'name': row.name,
                'team_name': row.team_name,
                'best_checkout': best_co
            })

        # sort: have numeric values first (descending) then blanks; tie-break on name
        def sort_key(entry):
            # numeric entries: has_value = 0, blanks: has_value = 1
            has_value = 0 if entry['best_checkout'] is not None else 1
            # for numeric we want reverse sort by value; for blanks value doesn't matter
            val = entry['best_checkout'] if entry['best_checkout'] is not None else -1
            return (has_value, -val, entry['name'])

        stats.sort(key=sort_key)

        return render_template(
            'player_stats.html',
            stat_type=stat_type,
            checkout_stats=stats,
            max_gw=max_gw,
            now=datetime.now()
        )

    elif stat_type == 'most_180s':
        # Get all players to ensure inclusive list
        all_players = Player.query.all()

        player_data = []
        for p in all_players:
            gw_data = {}
            total = 0
            games_played_total = 0
            for s in p.game_week_stats:
                if s.games_played > 0:
                    gw_data[s.game_week] = s.one_eighties
                    total += s.one_eighties
                    games_played_total += s.games_played
            
            # If a player hasn't played at all, make their total blank to match the template empty logic for visual blanks
            display_total = total if games_played_total > 0 else ''
            
            player_data.append({
                'name': p.name,
                'team_name': p.team.name if p.team else '',
                'gw_data': gw_data,
                'total': total,
                'display_total': display_total,
                'games_played': games_played_total
            })
        player_data.sort(key=lambda x: (-x['total'], -x['games_played'], x['name']))

        return render_template(
            'player_stats.html',
            stat_type=stat_type,
            player_data=player_data,
            max_gw=max_gw,
            now=datetime.now()
        )

    else:
        # games_won (default) — per GW
        all_players = Player.query.all()

        player_data = []
        for p in all_players:
            gw_data = {}
            total = 0
            games_played_total = 0
            for s in p.game_week_stats:
                if s.games_played > 0:
                    gw_data[s.game_week] = s.games_won
                    total += s.games_won
                    games_played_total += s.games_played
            
            # If a player hasn't played at all, make their total blank
            display_total = total if games_played_total > 0 else ''
            
            player_data.append({
                'name': p.name,
                'team_name': p.team.name if p.team else '',
                'gw_data': gw_data,
                'total': total,
                'display_total': display_total,
                'games_played': games_played_total
            })
        # Sort by total desc, then games_played desc, then name asc
        player_data.sort(key=lambda x: (-x['total'], -x['games_played'], x['name']))

        return render_template(
            'player_stats.html',
            stat_type=stat_type,
            player_data=player_data,
            max_gw=max_gw,
            now=datetime.now()
        )


@main_bp.route('/venues')
def venues():
    """Venue directory — simple list from team data."""
    teams = Team.query.order_by(Team.name.asc()).all()
    return render_template('venues.html', teams=teams)


@main_bp.route('/documents')
def documents():
    """Documents and rules page — rulebook and AGM only."""
    docs = Document.query.order_by(Document.uploaded_at.desc()).all()
    categories = {
        'rulebook': [d for d in docs if d.category == 'rulebook'],
        'agm': [d for d in docs if d.category == 'agm'],
    }
    return render_template('documents.html', categories=categories)


@main_bp.route('/about')
def about():
    """About page with committee information."""
    members = Committee.query.order_by(Committee.display_order.asc()).all()
    return render_template('about.html', members=members)
@main_bp.route('/view-minute/<int:doc_id>')
def view_minute(doc_id):
    """View typed AGM minutes."""
    minute = Document.query.get_or_404(doc_id)
    if minute.category != 'agm' or not minute.content:
        return redirect(url_for('main.documents'))
    return render_template('minute_view.html', minute=minute)
