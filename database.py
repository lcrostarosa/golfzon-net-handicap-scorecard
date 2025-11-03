"""
Database connection and session management.
"""
import os
from typing import List, Optional
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from datetime import datetime

from models import Base, League, Team, Player, WeeklyScore

# Database file path
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///golfzon_league.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Enable foreign keys for SQLite
if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here - let caller manage


@contextmanager
def get_db_context():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize the database (create tables)."""
    Base.metadata.create_all(bind=engine)


def get_engine():
    """Get the database engine."""
    return engine


# ============================================================================
# CRUD Operations for Leagues
# ============================================================================

def create_league(db: Session, name: str) -> League:
    """Create a new league."""
    league = League(name=name)
    db.add(league)
    db.commit()
    db.refresh(league)
    return league


def get_league(db: Session, league_id: int) -> Optional[League]:
    """Get a league by ID."""
    return db.query(League).filter(League.id == league_id).first()


def get_league_by_name(db: Session, name: str) -> Optional[League]:
    """Get a league by name."""
    return db.query(League).filter(League.name == name).first()


def list_leagues(db: Session) -> List[League]:
    """List all leagues."""
    return db.query(League).order_by(League.name).all()


def delete_league(db: Session, league_id: int) -> bool:
    """Delete a league."""
    league = get_league(db, league_id)
    if league:
        db.delete(league)
        db.commit()
        return True
    return False


# ============================================================================
# CRUD Operations for Teams
# ============================================================================

def create_team(db: Session, league_id: int, name: str) -> Team:
    """Create a new team."""
    team = Team(league_id=league_id, name=name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def get_team(db: Session, team_id: int) -> Optional[Team]:
    """Get a team by ID."""
    return db.query(Team).filter(Team.id == team_id).first()


def list_teams(db: Session, league_id: Optional[int] = None) -> List[Team]:
    """List teams, optionally filtered by league."""
    query = db.query(Team)
    if league_id:
        query = query.filter(Team.league_id == league_id)
    return query.order_by(Team.name).all()


def delete_team(db: Session, team_id: int) -> bool:
    """Delete a team."""
    team = get_team(db, team_id)
    if team:
        db.delete(team)
        db.commit()
        return True
    return False


# ============================================================================
# CRUD Operations for Players
# ============================================================================

def create_player(db: Session, team_id: int, name: str) -> Player:
    """Create a new player."""
    player = Player(team_id=team_id, name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def get_player(db: Session, player_id: int) -> Optional[Player]:
    """Get a player by ID."""
    return db.query(Player).filter(Player.id == player_id).first()


def find_player_by_name(db: Session, name: str, league_id: Optional[int] = None) -> Optional[Player]:
    """Find a player by name, optionally within a specific league."""
    query = db.query(Player).filter(func.lower(Player.name) == name.lower())
    if league_id:
        query = query.join(Team).filter(Team.league_id == league_id)
    return query.first()


def list_players(db: Session, team_id: Optional[int] = None, league_id: Optional[int] = None) -> List[Player]:
    """List players, optionally filtered by team or league."""
    query = db.query(Player)
    if team_id:
        query = query.filter(Player.team_id == team_id)
    elif league_id:
        query = query.join(Team).filter(Team.league_id == league_id)
    return query.order_by(Player.name).all()


def delete_player(db: Session, player_id: int) -> bool:
    """Delete a player."""
    player = get_player(db, player_id)
    if player:
        db.delete(player)
        db.commit()
        return True
    return False


# ============================================================================
# CRUD Operations for Weekly Scores
# ============================================================================

def create_weekly_score(
    db: Session,
    player_id: int,
    league_id: int,
    week_number: int,
    date: datetime,
    gross_score: int,
    handicap: float,
    strokes_given: float,
    net_score: float,
    num_holes: int
) -> WeeklyScore:
    """Create a new weekly score."""
    score = WeeklyScore(
        player_id=player_id,
        league_id=league_id,
        week_number=week_number,
        date=date,
        gross_score=gross_score,
        handicap=handicap,
        strokes_given=strokes_given,
        net_score=net_score,
        num_holes=num_holes
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def get_weekly_score(db: Session, score_id: int) -> Optional[WeeklyScore]:
    """Get a weekly score by ID."""
    return db.query(WeeklyScore).filter(WeeklyScore.id == score_id).first()


def get_scores_by_week(db: Session, league_id: int, week_number: int) -> List[WeeklyScore]:
    """Get all scores for a specific week in a league."""
    return db.query(WeeklyScore).filter(
        WeeklyScore.league_id == league_id,
        WeeklyScore.week_number == week_number
    ).order_by(WeeklyScore.net_score).all()


def get_player_scores_by_week(db: Session, player_id: int, week_number: int) -> Optional[WeeklyScore]:
    """Get a player's score for a specific week."""
    return db.query(WeeklyScore).filter(
        WeeklyScore.player_id == player_id,
        WeeklyScore.week_number == week_number
    ).first()


def get_top_two_scores_per_team(db: Session, league_id: int, week_number: int) -> dict:
    """
    Get the top 2 net scores per team for a specific week.
    Returns a dictionary mapping team_id to a list of the top 2 WeeklyScore objects.
    """
    scores = get_scores_by_week(db, league_id, week_number)
    
    # Group scores by team
    team_scores = {}
    for score in scores:
        team_id = score.player.team_id
        if team_id not in team_scores:
            team_scores[team_id] = []
        team_scores[team_id].append(score)
    
    # Sort each team's scores by net_score (ascending) and take top 2
    result = {}
    for team_id, scores_list in team_scores.items():
        sorted_scores = sorted(scores_list, key=lambda x: x.net_score)
        result[team_id] = sorted_scores[:2]
    
    return result


def calculate_team_score_for_week(db: Session, league_id: int, week_number: int, team_id: int) -> Optional[float]:
    """
    Calculate a team's score for a week (sum of top 2 net scores).
    Returns None if team has fewer than 2 scores.
    """
    top_scores = get_top_two_scores_per_team(db, league_id, week_number)
    if team_id in top_scores and len(top_scores[team_id]) >= 2:
        return sum(score.net_score for score in top_scores[team_id][:2])
    return None


def get_all_weeks(db: Session, league_id: int) -> List[int]:
    """Get all week numbers that have scores in a league."""
    weeks = db.query(WeeklyScore.week_number).filter(
        WeeklyScore.league_id == league_id
    ).distinct().order_by(WeeklyScore.week_number).all()
    return [w[0] for w in weeks]


def delete_weekly_score(db: Session, score_id: int) -> bool:
    """Delete a weekly score."""
    score = get_weekly_score(db, score_id)
    if score:
        db.delete(score)
        db.commit()
        return True
    return False

