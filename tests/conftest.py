"""
Pytest configuration and fixtures for testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from golfzon_ocr.models import Base
from golfzon_ocr.db import DATABASE_URL


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session using in-memory SQLite."""
    # Use in-memory database for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_league(db_session):
    """Create a sample league for testing."""
    from golfzon_ocr.db import create_league
    return create_league(db_session, "Test League")


@pytest.fixture
def sample_teams(db_session, sample_league):
    """Create sample teams for testing."""
    from golfzon_ocr.db import create_team
    team1 = create_team(db_session, sample_league.id, "Team A")
    team2 = create_team(db_session, sample_league.id, "Team B")
    return [team1, team2]


@pytest.fixture
def sample_players(db_session, sample_teams):
    """Create sample players for testing."""
    from golfzon_ocr.db import create_player
    players = []
    for team in sample_teams:
        players.append(create_player(db_session, team.id, f"Player {team.name[-1]}a"))
        players.append(create_player(db_session, team.id, f"Player {team.name[-1]}b"))
    return players


@pytest.fixture
def sample_scores(db_session, sample_league, sample_players):
    """Create sample weekly scores for testing."""
    from golfzon_ocr.db import create_weekly_score
    from datetime import datetime
    
    scores = []
    # Create scores for week 1
    for i, player in enumerate(sample_players):
        scores.append(create_weekly_score(
            db_session,
            player_id=player.id,
            league_id=sample_league.id,
            week_number=1,
            date=datetime.now(),
            gross_score=40 + i,
            handicap=10.0 + i,
            strokes_given=5.0 + i,
            net_score=35.0 + i,
            num_holes=9
        ))
    
    return scores

