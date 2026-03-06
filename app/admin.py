"""Admin dashboard blueprint for the HDA website."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.auth import role_required
from app.models import (
    Team, Player, Fixture, Result, Tournament,
    Document, Committee, User, Season, GameWeek, PlayerGameWeekStats,
    MatchDetail
)

admin_bp = Blueprint('admin', __name__, url_prefix='/dashboard')


# ---------------------------------------------------------------------------
# Team Captain Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route('/captain')
@role_required('captain')
def captain_dashboard():
    """Captain dashboard — view fixtures and submit scorecard results."""
    user_team = current_user.team
    game_weeks = GameWeek.query.order_by(GameWeek.week_number.asc()).all()
    current_gw = GameWeek.query.filter_by(status='current').first()

    pending_fixtures = []
    if user_team and user_team.team_number:
        tn = user_team.team_number
        # Query for fixtures where user's team is participating and result is needed:
        # 1. Fixture was played (is_played=True) but no result submitted yet, OR
        # 2. Result exists but not approved (pending admin approval), OR
        # 3. Gameweek date has passed but no approved result exists yet
        today = datetime.now().date()
        query = Fixture.query.outerjoin(Result).outerjoin(GameWeek).filter(
            ((Fixture.home_team_number == tn) | (Fixture.away_team_number == tn)),
            Fixture.is_bye == False,  # noqa: E712
            # Show form if: match played & no result, OR result exists but not approved, OR gameweek date passed
            db.or_(
                db.and_(
                    Fixture.is_played == True,  # noqa: E712
                    Result.id.is_(None)  # No result submitted yet
                ),
                db.and_(
                    Result.id.isnot(None),  # Result exists
                    Result.approved == False  # noqa: E712
                ),
                db.and_(
                    GameWeek.date.isnot(None),  # Has a date
                    GameWeek.date < today,  # Date is in the past
                    db.or_(
                        Result.id.is_(None),  # No result submitted yet
                        Result.approved == False  # Or result not approved
                    )
                )
            )
        ).order_by(GameWeek.week_number.desc(), Fixture.id.asc())
        pending_fixtures = query.all()

    return render_template(
        'captain_dashboard.html',
        team=user_team,
        fixtures=pending_fixtures,
        game_weeks=game_weeks,
        current_gw=current_gw
    )


@admin_bp.route('/captain/submit-score/<int:fixture_id>', methods=['POST'])
@role_required('captain')
def submit_score(fixture_id):
    """Submit a scorecard result. Allowed for captains of teams in current gameweek fixtures."""
    fixture = Fixture.query.get_or_404(fixture_id)
    user_team = Team.query.get(current_user.team_id)

    # Restriction: Only captains of teams in this fixture can submit
    if not user_team or user_team.team_number not in [fixture.home_team_number, fixture.away_team_number]:
        flash('Only captains of teams in this fixture can submit the scorecard.', 'danger')
        return redirect(url_for('admin.captain_dashboard'))

    # Totals (can be used as fallback or overrides)
    pairs_home_subtotal = request.form.get('pairs_home_subtotal', 0, type=int)
    pairs_away_subtotal = request.form.get('pairs_away_subtotal', 0, type=int)
    singles_home_total = request.form.get('singles_home_total', 0, type=int)
    singles_away_total = request.form.get('singles_away_total', 0, type=int)
    total_home = request.form.get('total_home', 0, type=int)
    total_away = request.form.get('total_away', 0, type=int)

    # 180s and highest close
    one_eighties_scored = request.form.get('one_eighties_scored', '').strip()
    highest_close = request.form.get('highest_close', 0, type=int)
    highest_close_player = request.form.get('highest_close_player', '').strip()
    notes = request.form.get('notes', '').strip()

    # Check if a result already exists (for resubmission/amendment)
    result = Result.query.filter_by(fixture_id=fixture.id).first()
    if result:
        # Update existing result
        result.pairs_home_subtotal = pairs_home_subtotal
        result.pairs_away_subtotal = pairs_away_subtotal
        result.singles_home_total = singles_home_total
        result.singles_away_total = singles_away_total
        result.total_home = total_home
        result.total_away = total_away
        result.one_eighties_scored = one_eighties_scored
        result.highest_close = highest_close
        result.highest_close_player = highest_close_player
        result.submitted_by = current_user.id
        result.approved = False
        result.status = 'pending'
        result.decline_reason = None
        result.notes = notes
        result.submitted_at = datetime.now()
        
        # Clear existing match details to resave
        MatchDetail.query.filter_by(result_id=result.id).delete()
    else:
        # Create new result
        result = Result(
            fixture_id=fixture.id,
            game_week_id=fixture.game_week_id,
            pairs_home_subtotal=pairs_home_subtotal,
            pairs_away_subtotal=pairs_away_subtotal,
            singles_home_total=singles_home_total,
            singles_away_total=singles_away_total,
            total_home=total_home,
            total_away=total_away,
            one_eighties_scored=one_eighties_scored,
            highest_close=highest_close,
            highest_close_player=highest_close_player,
            submitted_by=current_user.id,
            approved=False,
            status='pending',
            notes=notes
        )
        db.session.add(result)
    
    db.session.flush()  # To get result.id if new

    # Save Pairs MatchDetails
    for i in range(1, 4):
        p1_id = request.form.get(f'pair_{i}_home_p1', type=int)
        p2_id = request.form.get(f'pair_{i}_home_p2', type=int)
        ap1_id = request.form.get(f'pair_{i}_away_p1', type=int)
        ap2_id = request.form.get(f'pair_{i}_away_p2', type=int)
        
        # Only save if at least one player is selected
        if p1_id or p2_id or ap1_id or ap2_id:
            md = MatchDetail(
                result_id=result.id,
                match_type='pair',
                match_num=i,
                home_player1_id=p1_id if p1_id else None,
                home_player2_id=p2_id if p2_id else None,
                away_player1_id=ap1_id if ap1_id else None,
                away_player2_id=ap2_id if ap2_id else None,
                home_legs_won=request.form.get(f'pair_{i}_home_lw', 0, type=int),
                away_legs_won=request.form.get(f'pair_{i}_away_lw', 0, type=int),
                home_res=request.form.get(f'pair_{i}_home_res', 0, type=int),
                away_res=request.form.get(f'pair_{i}_away_res', 0, type=int)
            )
            db.session.add(md)

    # Save Singles MatchDetails
    for i in range(1, 7):
        p1_id = request.form.get(f'single_{i}_home_p', type=int)
        ap1_id = request.form.get(f'single_{i}_away_p', type=int)
        
        if p1_id or ap1_id:
            h_lw = request.form.get(f'single_{i}_home_tlw', 0, type=int)
            a_lw = request.form.get(f'single_{i}_away_tlw', 0, type=int)
            
            # For singles, we calculate Res (point) based on legs won
            # If no explicit Res input, we assume the one with more legs wins the game point
            h_res = 1 if h_lw > a_lw else 0
            a_res = 1 if a_lw > h_lw else 0

            md = MatchDetail(
                result_id=result.id,
                match_type='single',
                match_num=i,
                home_player1_id=p1_id if p1_id else None,
                away_player1_id=ap1_id if ap1_id else None,
                home_legs_won=h_lw,
                away_legs_won=a_lw,
                home_res=h_res,
                away_res=a_res
            )
            db.session.add(md)

    db.session.commit()

    flash('Scorecard submitted successfully! Detailed results recorded.', 'success')
    return redirect(url_for('admin.captain_dashboard'))


@admin_bp.route('/fixture-secretary/decline-result/<int:result_id>', methods=['POST'])
@role_required('fixture_secretary')
def decline_result(result_id):
    """Decline a submitted scorecard result."""
    result = Result.query.get_or_404(result_id)
    reason = request.form.get('decline_reason', '').strip()

    if result.approved:
        flash('Cannot decline an already approved result.', 'danger')
        return redirect(url_for('admin.fixture_sec_dashboard'))

    result.status = 'declined'
    result.approved = False
    result.decline_reason = reason
    db.session.commit()

    flash('Result declined and returned to captain.', 'warning')
    return redirect(url_for('admin.fixture_sec_dashboard'))


# ---------------------------------------------------------------------------
# Secretary General Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route('/secretary')
@role_required('secretary_general')
def secretary_dashboard():
    """Secretary General dashboard — manage teams, players, tournaments."""
    teams = Team.query.order_by(Team.name).all()
    players = Player.query.order_by(Player.team_id, Player.name).all()
    tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
    users = User.query.order_by(User.username).all()
    agm_minutes = Document.query.filter_by(category='agm').order_by(Document.uploaded_at.desc()).all()

    # Group players by team
    players_by_team = {}
    unassigned = []
    for p in players:
        if p.team_id and p.team:
            if p.team.name not in players_by_team:
                players_by_team[p.team.name] = []
            players_by_team[p.team.name].append(p)
        else:
            unassigned.append(p)

    return render_template(
        'secretary_dashboard.html',
        teams=teams,
        players=players,
        players_by_team=players_by_team,
        unassigned_players=unassigned,
        tournaments=tournaments,
        users=users,
        agm_minutes=agm_minutes
    )


@admin_bp.route('/secretary/add-minute', methods=['POST'])
@role_required('secretary_general')
def add_minute():
    """Add typed AGM minutes."""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    description = request.form.get('description', '').strip()

    if not title or not content:
        flash('Title and Content are required for minutes.', 'danger')
        return redirect(url_for('admin.secretary_dashboard') + '?tab=agm-minutes')

    minute = Document(
        title=title,
        category='agm',
        file_url='', # Satisfy NOT NULL constraint
        content=content,
        description=description
    )
    db.session.add(minute)
    db.session.commit()
    flash(f'Minutes "{title}" added successfully.', 'success')
    return redirect(url_for('admin.secretary_dashboard') + '?tab=agm-minutes')


@admin_bp.route('/secretary/edit-minute/<int:doc_id>', methods=['POST'])
@role_required('secretary_general')
def edit_minute(doc_id):
    """Edit existing AGM minutes."""
    minute = Document.query.get_or_404(doc_id)
    minute.title = request.form.get('title', minute.title).strip()
    minute.content = request.form.get('content', minute.content).strip()
    minute.description = request.form.get('description', minute.description).strip()
    
    db.session.commit()
    flash(f'Minutes "{minute.title}" updated.', 'success')
    return redirect(url_for('admin.secretary_dashboard') + '?tab=agm-minutes')


@admin_bp.route('/secretary/delete-minute/<int:doc_id>', methods=['POST'])
@role_required('secretary_general')
def delete_minute(doc_id):
    """Delete AGM minutes."""
    minute = Document.query.get_or_404(doc_id)
    title = minute.title
    db.session.delete(minute)
    db.session.commit()
    flash(f'Minutes "{title}" deleted.', 'success')
    return redirect(url_for('admin.secretary_dashboard') + '?tab=agm-minutes')


@admin_bp.route('/secretary/add-team', methods=['POST'])
@role_required('secretary_general')
def add_team():
    """Add a new team with venue text input."""
    name = request.form.get('name', '').strip()
    captain_name = request.form.get('captain_name', '').strip()
    venue_name = request.form.get('venue_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip()

    if not name:
        flash('Team name is required.', 'danger')
        return redirect(url_for('admin.secretary_dashboard'))

    team = Team(
        name=name,
        captain_name=captain_name,
        venue_name=venue_name,
        phone_number=phone_number
    )
    db.session.add(team)
    db.session.commit()
    flash(f'Team "{name}" added successfully.', 'success')
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/edit-team/<int:team_id>', methods=['POST'])
@role_required('secretary_general', 'fixture_secretary')
def edit_team(team_id):
    """Edit an existing team."""
    team = Team.query.get_or_404(team_id)
    team.name = request.form.get('name', team.name).strip()
    team.captain_name = request.form.get('captain_name', team.captain_name or '').strip()
    team.venue_name = request.form.get('venue_name', team.venue_name or '').strip()
    team.phone_number = request.form.get('phone_number', team.phone_number or '').strip()
    db.session.commit()
    flash(f'Team "{team.name}" updated.', 'success')
    
    if current_user.role == 'fixture_secretary':
        return redirect(url_for('admin.fixture_sec_dashboard') + '?tab=team-numbers')
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/delete-team/<int:team_id>', methods=['POST'])
@role_required('secretary_general', 'fixture_secretary')
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    flash(f'Team "{team.name}" deleted.', 'success')
    
    if current_user.role == 'fixture_secretary':
        return redirect(url_for('admin.fixture_sec_dashboard') + '?tab=team-numbers')
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/add-player', methods=['POST'])
@role_required('secretary_general')
def add_player():
    """Add multiple players with individual payment statuses in batch."""
    team_id = request.form.get('team_id', type=int)
    names = request.form.getlist('names')
    payment_statuses = request.form.getlist('payment_statuses')

    if not team_id:
        flash('Team is required for registration.', 'danger')
        return redirect(url_for('admin.secretary_dashboard'))

    amount_map = {'fully_paid': 30.0, 'half_paid': 15.0, 'not_paid': 0.0}

    added_count = 0
    # Zip names and statuses to process them in pairs
    for name, status in zip(names, payment_statuses):
        stripped_name = name.strip()
        if stripped_name:
            amount = amount_map.get(status, 0.0)
            player = Player(
                name=stripped_name,
                team_id=team_id,
                payment_status=status,
                amount_paid=amount
            )
            db.session.add(player)
            added_count += 1
    
    if added_count > 0:
        db.session.commit()
        flash(f'{added_count} player(s) registered successfully for team.', 'success')
    else:
        flash('No player names provided.', 'warning')
        
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/edit-player/<int:player_id>', methods=['POST'])
@role_required('secretary_general')
def edit_player(player_id):
    """Edit an existing player (team, payment)."""
    player = Player.query.get_or_404(player_id)
    player.name = request.form.get('name', player.name).strip()
    team_id = request.form.get('team_id', type=int)
    player.team_id = team_id if team_id else None
    payment_status = request.form.get('payment_status', player.payment_status)
    player.payment_status = payment_status

    amount_map = {'fully_paid': 30.0, 'half_paid': 15.0, 'not_paid': 0.0}
    player.amount_paid = amount_map.get(payment_status, player.amount_paid)

    db.session.commit()
    flash(f'Player "{player.name}" updated.', 'success')
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/delete-player/<int:player_id>', methods=['POST'])
@role_required('secretary_general')
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    player_name = player.name
    
    # Clear any match detail references to this player
    MatchDetail.query.filter(
        db.or_(
            MatchDetail.home_player1_id == player_id,
            MatchDetail.home_player2_id == player_id,
            MatchDetail.away_player1_id == player_id,
            MatchDetail.away_player2_id == player_id
        )
    ).update({
        MatchDetail.home_player1_id: None,
        MatchDetail.home_player2_id: None,
        MatchDetail.away_player1_id: None,
        MatchDetail.away_player2_id: None
    }, synchronize_session=False)
    
    try:
        db.session.delete(player)
        db.session.commit()
        flash(f'Player "{player_name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting player: {str(e)}', 'danger')
    
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/add-tournament', methods=['POST'])
@role_required('secretary_general')
def add_tournament():
    name = request.form.get('name', '').strip()
    date_str = request.form.get('date', '')
    venue = request.form.get('venue', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not date_str:
        flash('Tournament name and date are required.', 'danger')
        return redirect(url_for('admin.secretary_dashboard'))

    try:
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('admin.secretary_dashboard'))

    tournament = Tournament(
        name=name, date=date, venue=venue,
        description=description, is_upcoming=True
    )
    db.session.add(tournament)
    db.session.commit()
    flash(f'Tournament "{name}" added successfully.', 'success')
    return redirect(url_for('admin.secretary_dashboard'))


@admin_bp.route('/secretary/edit-tournament/<int:tournament_id>', methods=['POST'])
@role_required('secretary_general')
def edit_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    tournament.name = request.form.get('name', tournament.name).strip()
    date_str = request.form.get('date', '')
    if date_str:
        try:
            tournament.date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    tournament.venue = request.form.get('venue', tournament.venue or '').strip()
    tournament.description = request.form.get('description', tournament.description or '').strip()
    db.session.commit()
    flash(f'Tournament "{tournament.name}" updated.', 'success')
    return redirect(url_for('admin.secretary_dashboard') + '?tab=tournaments')


@admin_bp.route('/secretary/delete-tournament/<int:tournament_id>', methods=['POST'])
@role_required('secretary_general')
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    db.session.delete(tournament)
    db.session.commit()
    flash(f'Tournament "{tournament.name}" deleted.', 'success')
    return redirect(url_for('admin.secretary_dashboard') + '?tab=tournaments')


@admin_bp.route('/secretary/delete-user/<int:user_id>', methods=['POST'])
@role_required('secretary_general')
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.secretary_dashboard') + '?tab=users')
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'success')
    return redirect(url_for('admin.secretary_dashboard') + '?tab=users')


@admin_bp.route('/secretary/add-user', methods=['POST'])
@role_required('secretary_general')
def add_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'captain')
    full_name = request.form.get('full_name', '').strip()
    team_id = request.form.get('team_id', type=int)

    if not username or not password:
        flash('Username and password are required.', 'danger')
        return redirect(url_for('admin.secretary_dashboard'))

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin.secretary_dashboard'))

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        full_name=full_name,
        team_id=team_id
    )
    db.session.add(user)
    db.session.commit()
    flash(f'User "{username}" created successfully.', 'success')
    return redirect(url_for('admin.secretary_dashboard'))


# ---------------------------------------------------------------------------
# Fixture Secretary Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route('/fixture-secretary')
@role_required('fixture_secretary')
def fixture_sec_dashboard():
    """Fixture Secretary dashboard."""
    teams = Team.query.order_by(Team.name).all()
    players = Player.query.order_by(Player.name).all()
    game_weeks = GameWeek.query.order_by(GameWeek.week_number.asc()).all()

    # Pending results grouped by game week
    pending_results = Result.query.filter_by(approved=False).all()
    pending_by_gw = {}
    for r in pending_results:
        gw_num = r.game_week.week_number if r.game_week else 0
        if gw_num not in pending_by_gw:
            pending_by_gw[gw_num] = []
        pending_by_gw[gw_num].append(r)

    # Player search
    search_query = request.args.get('player_search', '').strip()
    searched_players = []
    if search_query:
        searched_players = Player.query.filter(
            Player.name.ilike(f'%{search_query}%')
        ).all()

    return render_template(
        'fixture_sec_dashboard.html',
        teams=teams,
        players=players,
        game_weeks=game_weeks,
        pending_by_gw=pending_by_gw,
        search_query=search_query,
        searched_players=searched_players
    )


@admin_bp.route('/fixture-secretary/assign-team-number/<int:team_id>', methods=['POST'])
@role_required('fixture_secretary')
def assign_team_number(team_id):
    """Assign a draw number to a team."""
    team = Team.query.get_or_404(team_id)
    number = request.form.get('team_number', type=int)

    if number is not None:
        # Check if number is already taken
        existing = Team.query.filter(Team.team_number == number, Team.id != team_id).first()
        if existing:
            flash(f'Number {number} is already assigned to {existing.name}.', 'danger')
            return redirect(url_for('admin.fixture_sec_dashboard'))
        team.team_number = number

    db.session.commit()
    flash(f'Team "{team.name}" assigned number {number}.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard'))


@admin_bp.route('/fixture-secretary/add-game-week', methods=['POST'])
@role_required('fixture_secretary')
def add_game_week():
    """Add a game week."""
    week_number = request.form.get('week_number', type=int)
    date_str = request.form.get('date', '')
    status = request.form.get('status', 'upcoming')

    if not week_number:
        flash('Week number is required.', 'danger')
        return redirect(url_for('admin.fixture_sec_dashboard'))

    existing = GameWeek.query.filter_by(week_number=week_number).first()
    if existing:
        flash(f'Game Week {week_number} already exists.', 'danger')
        return redirect(url_for('admin.fixture_sec_dashboard'))

    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # If setting as current, unset other current weeks
    if status == 'current':
        GameWeek.query.filter_by(status='current').update({'status': 'previous'})

    gw = GameWeek(week_number=week_number, date=date, status=status)
    db.session.add(gw)
    db.session.commit()
    flash(f'Game Week {week_number} added.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard'))


@admin_bp.route('/fixture-secretary/update-game-week-status/<int:gw_id>', methods=['POST'])
@role_required('fixture_secretary')
def update_game_week_status(gw_id):
    """Update game week status."""
    gw = GameWeek.query.get_or_404(gw_id)
    new_status = request.form.get('status', gw.status)

    if new_status == 'current':
        GameWeek.query.filter_by(status='current').update({'status': 'previous'})

    gw.status = new_status
    db.session.commit()
    flash(f'Game Week {gw.week_number} set to {new_status}.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard'))


@admin_bp.route('/fixture-secretary/delete-game-week/<int:gw_id>', methods=['POST'])
@role_required('fixture_secretary')
def delete_game_week(gw_id):
    gw = GameWeek.query.get_or_404(gw_id)
    db.session.delete(gw)
    db.session.commit()
    flash(f'Game Week {gw.week_number} and its fixtures deleted.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard') + '?tab=fixtures')


@admin_bp.route('/fixture-secretary/add-fixtures', methods=['POST'])
@role_required('fixture_secretary')
def add_fixtures():
    """Add fixtures for a game week using team numbers (e.g. '1v20')."""
    game_week_id = request.form.get('game_week_id', type=int)
    fixtures_text = request.form.get('fixtures_text', '').strip()

    if not game_week_id or not fixtures_text:
        flash('Game week and fixtures are required.', 'danger')
        return redirect(url_for('admin.fixture_sec_dashboard'))

    lines = [line.strip() for line in fixtures_text.split('\n') if line.strip()]
    added = 0
    for line in lines:
        line = line.lower().replace(' ', '')
        if 'vbye' in line or 'byev' in line:
            # Bye fixture
            parts = line.replace('vbye', ' ').replace('byev', ' ').strip().split()
            if parts:
                try:
                    team_num = int(parts[0])
                    f = Fixture(
                        game_week_id=game_week_id,
                        home_team_number=team_num,
                        away_team_number=None,
                        is_bye=True
                    )
                    db.session.add(f)
                    added += 1
                except ValueError:
                    pass
        elif 'v' in line:
            parts = line.split('v')
            if len(parts) == 2:
                try:
                    home = int(parts[0])
                    away = int(parts[1])
                    f = Fixture(
                        game_week_id=game_week_id,
                        home_team_number=home,
                        away_team_number=away
                    )
                    db.session.add(f)
                    added += 1
                except ValueError:
                    pass

    db.session.commit()
    flash(f'{added} fixture(s) added successfully.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard'))


@admin_bp.route('/fixture-secretary/approve-result/<int:result_id>', methods=['POST'])
@role_required('fixture_secretary')
def approve_result(result_id):
    """Approve a submitted scorecard result."""
    result = Result.query.get_or_404(result_id)
    fixture = result.fixture

    if result.approved or result.status == 'approved':
        flash('Result already approved.', 'info')
        return redirect(url_for('admin.fixture_sec_dashboard'))

    result.approved = True
    result.status = 'approved'
    fixture.is_played = True

    # Automated Standings Update
    home_team = fixture.get_home_team()
    away_team = fixture.get_away_team()

    if home_team and away_team:
        # Update Legs/Subtotals defensively
        home_team.played = (home_team.played or 0) + 1
        away_team.played = (away_team.played or 0) + 1
        home_team.doubles = (home_team.doubles or 0) + (result.pairs_home_subtotal or 0)
        away_team.doubles = (away_team.doubles or 0) + (result.pairs_away_subtotal or 0)
        home_team.singles = (home_team.singles or 0) + (result.singles_home_total or 0)
        away_team.singles = (away_team.singles or 0) + (result.singles_away_total or 0)
        home_team.scores = (home_team.scores or 0) + (result.total_home or 0)
        away_team.scores = (away_team.scores or 0) + (result.total_away or 0)

        # Determine winner and award points (Win = 3)
        if result.total_home > result.total_away:
            home_team.won = (home_team.won or 0) + 1
            home_team.points = (home_team.points or 0) + 3
            away_team.lost = (away_team.lost or 0) + 1
        elif result.total_away > result.total_home:
            away_team.won = (away_team.won or 0) + 1
            away_team.points = (away_team.points or 0) + 3
            home_team.lost = (home_team.lost or 0) + 1
        else:
            # Draw — both get 1 point
            home_team.points = (home_team.points or 0) + 1
            away_team.points = (away_team.points or 0) + 1

        # Automated Player Stats Update from MatchDetail
        gw_num = fixture.game_week.week_number if fixture.game_week else 0
        for md in result.match_details:
            # players list will store (player_id, legs_to_add)
            players_session = []
            
            # ACCUMULATION RULE: Only count TLW for singles in "Games Won" column
            if md.match_type == 'single':
                if md.home_player1_id: players_session.append((md.home_player1_id, md.home_legs_won))
                if md.away_player1_id: players_session.append((md.away_player1_id, md.away_legs_won))
            else:
                # For doubles/pairs matches, we record games played but don't add to "Games Won" TLW column
                # as per user's latest instruction ("a plyers TLW is 6 thats the number which is supposed to be put on games won")
                if md.home_player1_id: players_session.append((md.home_player1_id, 0))
                if md.home_player2_id: players_session.append((md.home_player2_id, 0))
                if md.away_player1_id: players_session.append((md.away_player1_id, 0))
                if md.away_player2_id: players_session.append((md.away_player2_id, 0))

            for p_id, legs_to_add in players_session:
                stats = PlayerGameWeekStats.query.filter_by(player_id=p_id, game_week=gw_num).first()
                if not stats:
                    stats = PlayerGameWeekStats(player_id=p_id, game_week=gw_num)
                    db.session.add(stats)
                stats.games_played = (stats.games_played or 0) + 1
                # Accumulate legs won for singles matches
                stats.games_won = (stats.games_won or 0) + (legs_to_add or 0)
        
        # Update highest checkouts from result.highest_close_player string
        # Format: "Player Name * 140, Another Player * 120"
        if result.highest_close_player:
            parts = [p.strip() for p in result.highest_close_player.split(',') if p.strip()]
            for part in parts:
                p_name_query = part
                score_val = result.highest_close or 0
                if '*' in part:
                    try:
                        p_name_query, p_score = [s.strip() for s in part.split('*')]
                        score_val = int(p_score)
                    except (ValueError, IndexError):
                        continue
                
                # Broader Fuzzy match: matches anywhere in the string
                player = Player.query.filter(
                    Player.name.ilike(f"%{p_name_query}%")
                ).first()
                
                if player:
                    stats = PlayerGameWeekStats.query.filter_by(player_id=player.id, game_week=gw_num).first()
                    if not stats:
                        stats = PlayerGameWeekStats(player_id=player.id, game_week=gw_num)
                        db.session.add(stats)
                    current_highest = stats.highest_checkout or 0
                    if score_val > current_highest:
                        stats.highest_checkout = score_val

        # Update 180s from result.one_eighties_scored string if player names match
        if result.one_eighties_scored:
            names = [n.strip().lower() for n in result.one_eighties_scored.split(',') if n.strip()]
            for name in names:
                # Broader Fuzzy match for 180s
                player = Player.query.filter(
                    Player.name.ilike(f"%{name}%")
                ).first()
                if player:
                    stats = PlayerGameWeekStats.query.filter_by(player_id=player.id, game_week=gw_num).first()
                    if not stats:
                        stats = PlayerGameWeekStats(player_id=player.id, game_week=gw_num)
                        db.session.add(stats)
                    stats.one_eighties = (stats.one_eighties or 0) + 1

    db.session.commit()
    flash('Result approved, standings and player stats updated automatically.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard'))


@admin_bp.route('/fixture-secretary/update-team/<int:team_id>', methods=['POST'])
@role_required('fixture_secretary')
def update_team_standings(team_id):
    """Update team standings (Position, Team, Played, Won, Lost, Doubles, Singles, Scores, Points)."""
    team = Team.query.get_or_404(team_id)

    played = request.form.get('played', type=int)
    won = request.form.get('won', type=int)
    lost = request.form.get('lost', type=int)
    doubles = request.form.get('doubles', type=int)
    singles = request.form.get('singles', type=int)
    scores = request.form.get('scores', type=int)
    points = request.form.get('points', type=int)

    if played is not None:
        team.played = played
    if won is not None:
        team.won = won
    if lost is not None:
        team.lost = lost
    if doubles is not None:
        team.doubles = doubles
    if singles is not None:
        team.singles = singles
    if scores is not None:
        team.scores = scores
    if points is not None:
        team.points = points

    db.session.commit()
    flash(f'Standings for "{team.name}" updated.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard'))


@admin_bp.route('/fixture-secretary/update-player-stats/<int:player_id>', methods=['POST'])
@role_required('fixture_secretary')
def update_player_stats(player_id):
    """Update player stats for a specific game week."""
    player = Player.query.get_or_404(player_id)
    game_week = request.form.get('game_week', type=int)

    if not game_week:
        flash('Game week is required.', 'danger')
        return redirect(url_for('admin.fixture_sec_dashboard'))

    games_played = request.form.get('games_played', 0, type=int)
    games_won = request.form.get('games_won', 0, type=int)
    one_eighties = request.form.get('one_eighties', 0, type=int)
    highest_checkout = request.form.get('highest_checkout', 0, type=int)

    # Find or create stats for this GW
    stats = PlayerGameWeekStats.query.filter_by(
        player_id=player.id, game_week=game_week
    ).first()

    if stats:
        stats.games_played = games_played
        stats.games_won = games_won
        stats.one_eighties = one_eighties
        stats.highest_checkout = highest_checkout
    else:
        stats = PlayerGameWeekStats(
            player_id=player.id,
            game_week=game_week,
            games_played=games_played,
            games_won=games_won,
            one_eighties=one_eighties,
            highest_checkout=highest_checkout
        )
        db.session.add(stats)

    db.session.commit()
    flash(f'GW{game_week} stats for "{player.name}" updated.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard', player_search=player.name))


@admin_bp.route('/fixture-secretary/delete-player-stats/<int:stats_id>', methods=['POST'])
@role_required('fixture_secretary')
def delete_player_stats(stats_id):
    stats = PlayerGameWeekStats.query.get_or_404(stats_id)
    player_name = stats.player.name
    db.session.delete(stats)
    db.session.commit()
    flash(f'Stats for "{player_name}" deleted.', 'success')
    return redirect(url_for('admin.fixture_sec_dashboard', player_search=player_name) + '&tab=player-stats')
