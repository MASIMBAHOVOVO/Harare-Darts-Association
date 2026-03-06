"""Database models for the Harare Darts Association."""
from datetime import datetime, timezone
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# User & Authentication
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='captain')
    full_name = db.Column(db.String(120), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    team = db.relationship('Team', backref='users', lazy=True)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


# ---------------------------------------------------------------------------
# Season
# ---------------------------------------------------------------------------
class Season(db.Model):
    __tablename__ = 'seasons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_current = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Season {self.name}>'


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------
class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    team_number = db.Column(db.Integer, nullable=True, unique=True)
    captain_name = db.Column(db.String(120), nullable=True)
    venue_name = db.Column(db.String(200), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)

    # Standings fields
    played = db.Column(db.Integer, default=0)
    won = db.Column(db.Integer, default=0)
    lost = db.Column(db.Integer, default=0)
    doubles = db.Column(db.Integer, default=0)
    singles = db.Column(db.Integer, default=0)
    scores = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)

    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=True)

    players = db.relationship('Player', backref='team', lazy=True)

    def __repr__(self):
        return f'<Team {self.name}>'


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------
class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    payment_status = db.Column(db.String(20), default='not_paid')  # fully_paid, half_paid, not_paid
    amount_paid = db.Column(db.Float, default=0.0)

    game_week_stats = db.relationship('PlayerGameWeekStats', backref='player', lazy=True,
                                       cascade='all, delete-orphan')

    @property
    def is_eligible(self):
        return self.amount_paid >= 15

    @property
    def total_games_played(self):
        return sum(s.games_played for s in self.game_week_stats)

    @property
    def total_games_won(self):
        return sum(s.games_won for s in self.game_week_stats)

    @property
    def total_one_eighties(self):
        return sum(s.one_eighties for s in self.game_week_stats)

    @property
    def best_highest_checkout(self):
        checkouts = [s.highest_checkout for s in self.game_week_stats if s.highest_checkout and s.highest_checkout > 0]
        return max(checkouts) if checkouts else 0

    def __repr__(self):
        return f'<Player {self.name}>'


# ---------------------------------------------------------------------------
# Game Weeks
# ---------------------------------------------------------------------------
class GameWeek(db.Model):
    __tablename__ = 'game_weeks'
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False, unique=True)
    date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='upcoming')  # previous, current, upcoming

    fixtures = db.relationship('Fixture', backref='game_week', lazy=True)
    results = db.relationship('Result', backref='game_week', lazy=True)

    def __repr__(self):
        return f'<GameWeek {self.week_number}>'


# ---------------------------------------------------------------------------
# Player Game Week Stats
# ---------------------------------------------------------------------------
class PlayerGameWeekStats(db.Model):
    __tablename__ = 'player_game_week_stats'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    game_week = db.Column(db.Integer, nullable=False)
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    one_eighties = db.Column(db.Integer, default=0)
    highest_checkout = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<PlayerGWStats P{self.player_id} GW{self.game_week}>'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
class Fixture(db.Model):
    __tablename__ = 'fixtures'
    id = db.Column(db.Integer, primary_key=True)
    game_week_id = db.Column(db.Integer, db.ForeignKey('game_weeks.id'), nullable=True)
    home_team_number = db.Column(db.Integer, nullable=False)
    away_team_number = db.Column(db.Integer, nullable=True)  # nullable for Bye
    is_played = db.Column(db.Boolean, default=False)
    is_bye = db.Column(db.Boolean, default=False)

    def get_home_team(self):
        return Team.query.filter_by(team_number=self.home_team_number).first()

    def get_away_team(self):
        if self.is_bye or self.away_team_number is None:
            return None
        return Team.query.filter_by(team_number=self.away_team_number).first()

    def __repr__(self):
        away = self.away_team_number if self.away_team_number else 'Bye'
        return f'<Fixture {self.home_team_number}v{away}>'


# ---------------------------------------------------------------------------
# Results (Scorecard Format)
# ---------------------------------------------------------------------------
class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('fixtures.id'), nullable=False)
    game_week_id = db.Column(db.Integer, db.ForeignKey('game_weeks.id'), nullable=True)

    # Pairs section
    pairs_home_lw = db.Column(db.Integer, default=0)
    pairs_home_res = db.Column(db.Integer, default=0)
    pairs_away_lw = db.Column(db.Integer, default=0)
    pairs_away_res = db.Column(db.Integer, default=0)
    pairs_home_subtotal = db.Column(db.Integer, default=0)
    pairs_away_subtotal = db.Column(db.Integer, default=0)

    # Singles section
    singles_home_total = db.Column(db.Integer, default=0)
    singles_away_total = db.Column(db.Integer, default=0)

    # Overall scores
    total_home = db.Column(db.Integer, default=0)
    total_away = db.Column(db.Integer, default=0)

    # 180s and highest close
    one_eighties_scored = db.Column(db.Text, nullable=True)
    highest_close = db.Column(db.Integer, default=0)
    highest_close_player = db.Column(db.String(120), nullable=True)

    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, declined
    decline_reason = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text, nullable=True)

    fixture = db.relationship('Fixture', backref=db.backref('result', uselist=False))
    submitter = db.relationship('User', backref='submitted_results', lazy=True)
    match_details = db.relationship('MatchDetail', backref='result', lazy=True, cascade='all, delete-orphan')

    @property
    def overall_winner(self):
        if self.total_home > self.total_away:
            return 'home'
        elif self.total_away > self.total_home:
            return 'away'
        return 'draw'

    def __repr__(self):
        return f'<Result {self.total_home}-{self.total_away}>'


# ---------------------------------------------------------------------------
# Match Details (Detailed Scorecard Entries)
# ---------------------------------------------------------------------------
class MatchDetail(db.Model):
    __tablename__ = 'match_details'
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('results.id'), nullable=False)
    
    match_type = db.Column(db.String(20), nullable=False)  # 'pair', 'single'
    match_num = db.Column(db.Integer, nullable=False)
    
    home_player1_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    home_player2_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    away_player1_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    away_player2_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    
    home_legs_won = db.Column(db.Integer, default=0)
    away_legs_won = db.Column(db.Integer, default=0)
    
    # Optional fields for recording results specifically (e.g. 1-0 for match win)
    home_res = db.Column(db.Integer, default=0)
    away_res = db.Column(db.Integer, default=0)

    # Relationships to access player names easily
    home_player1 = db.relationship('Player', foreign_keys=[home_player1_id])
    home_player2 = db.relationship('Player', foreign_keys=[home_player2_id])
    away_player1 = db.relationship('Player', foreign_keys=[away_player1_id])
    away_player2 = db.relationship('Player', foreign_keys=[away_player2_id])

    def __repr__(self):
        return f'<MatchDetail {self.match_type} #{self.match_num} R{self.result_id}>'


# ---------------------------------------------------------------------------
# Tournaments
# ---------------------------------------------------------------------------
class Tournament(db.Model):
    __tablename__ = 'tournaments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_upcoming = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Tournament {self.name}>'


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # rulebook, agm
    file_url = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Document {self.title}>'


# ---------------------------------------------------------------------------
# Committee Members
# ---------------------------------------------------------------------------
class Committee(db.Model):
    __tablename__ = 'committee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Committee {self.name} - {self.role}>'
