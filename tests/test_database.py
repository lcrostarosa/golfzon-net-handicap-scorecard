"""
Tests for database operations.
"""
import pytest
from datetime import datetime

from golfzon_ocr.db import (
    create_league, get_league, get_league_by_name, list_leagues, delete_league,
    create_team, get_team, list_teams, delete_team,
    create_player, get_player, find_player_by_name, list_players, delete_player,
    create_weekly_score, get_weekly_score, get_scores_by_week,
    get_player_scores_by_week, get_top_two_scores_per_team,
    calculate_team_score_for_week, get_all_weeks
)


def test_create_and_get_league(db_session):
    """Test creating and retrieving a league."""
    league = create_league(db_session, "Test League")
    assert league.id is not None
    assert league.name == "Test League"
    
    retrieved = get_league(db_session, league.id)
    assert retrieved.id == league.id
    assert retrieved.name == league.name


def test_get_league_by_name(db_session):
    """Test retrieving a league by name."""
    create_league(db_session, "Test League")
    league = get_league_by_name(db_session, "Test League")
    assert league is not None
    assert league.name == "Test League"
    
    # Test non-existent league
    assert get_league_by_name(db_session, "Non-existent") is None


def test_list_leagues(db_session):
    """Test listing all leagues."""
    create_league(db_session, "League 1")
    create_league(db_session, "League 2")
    
    leagues = list_leagues(db_session)
    assert len(leagues) == 2
    assert all(league.name in ["League 1", "League 2"] for league in leagues)


def test_delete_league(db_session):
    """Test deleting a league."""
    league = create_league(db_session, "Test League")
    assert delete_league(db_session, league.id) is True
    assert get_league(db_session, league.id) is None


def test_create_and_get_team(db_session, sample_league):
    """Test creating and retrieving a team."""
    team = create_team(db_session, sample_league.id, "Team A")
    assert team.id is not None
    assert team.name == "Team A"
    assert team.league_id == sample_league.id
    
    retrieved = get_team(db_session, team.id)
    assert retrieved.id == team.id


def test_list_teams(db_session, sample_league):
    """Test listing teams."""
    create_team(db_session, sample_league.id, "Team A")
    create_team(db_session, sample_league.id, "Team B")
    
    teams = list_teams(db_session, league_id=sample_league.id)
    assert len(teams) == 2


def test_create_and_get_player(db_session, sample_teams):
    """Test creating and retrieving a player."""
    team = sample_teams[0]
    player = create_player(db_session, team.id, "Player 1")
    assert player.id is not None
    assert player.name == "Player 1"
    assert player.team_id == team.id
    
    retrieved = get_player(db_session, player.id)
    assert retrieved.id == player.id


def test_find_player_by_name(db_session, sample_players):
    """Test finding a player by name."""
    player = sample_players[0]
    found = find_player_by_name(db_session, player.name)
    assert found is not None
    assert found.id == player.id
    
    # Test case insensitive
    found = find_player_by_name(db_session, player.name.upper())
    assert found is not None


def test_list_players(db_session, sample_players, sample_teams):
    """Test listing players."""
    team = sample_teams[0]
    players = list_players(db_session, team_id=team.id)
    assert len(players) == 2  # Two players per team in fixture


def test_create_weekly_score(db_session, sample_league, sample_players):
    """Test creating a weekly score."""
    player = sample_players[0]
    score = create_weekly_score(
        db_session,
        player_id=player.id,
        league_id=sample_league.id,
        week_number=1,
        date=datetime.now(),
        gross_score=40,
        handicap=10.0,
        strokes_given=5.0,
        net_score=35.0,
        num_holes=9
    )
    assert score.id is not None
    assert score.net_score == 35.0


def test_get_scores_by_week(db_session, sample_league, sample_scores):
    """Test retrieving scores for a specific week."""
    scores = get_scores_by_week(db_session, sample_league.id, 1)
    assert len(scores) == len(sample_scores)


def test_get_top_two_scores_per_team(db_session, sample_league, sample_teams, sample_players):
    """Test getting top 2 scores per team."""
    from golfzon_ocr.db import create_weekly_score
    from datetime import datetime
    
    # Create scores for week 1
    for i, player in enumerate(sample_players):
        create_weekly_score(
            db_session,
            player_id=player.id,
            league_id=sample_league.id,
            week_number=1,
            date=datetime.now(),
            gross_score=40 + i,
            handicap=10.0,
            strokes_given=5.0,
            net_score=35.0 + i,  # Different net scores
            num_holes=9
        )
    
    top_scores = get_top_two_scores_per_team(db_session, sample_league.id, 1)
    
    # Each team should have 2 players with 2 scores each
    for team in sample_teams:
        assert team.id in top_scores
        assert len(top_scores[team.id]) == 2
        # Verify they're sorted (lowest net_score first)
        scores = top_scores[team.id]
        assert scores[0].net_score <= scores[1].net_score


def test_calculate_team_score_for_week(db_session, sample_league, sample_teams, sample_players):
    """Test calculating team score for a week."""
    from golfzon_ocr.db import create_weekly_score
    from datetime import datetime
    
    team = sample_teams[0]
    # Create scores for team players
    team_players = [p for p in sample_players if p.team_id == team.id]
    
    for i, player in enumerate(team_players):
        create_weekly_score(
            db_session,
            player_id=player.id,
            league_id=sample_league.id,
            week_number=1,
            date=datetime.now(),
            gross_score=40 + i,
            handicap=10.0,
            strokes_given=5.0,
            net_score=35.0 + i,
            num_holes=9
        )
    
    team_score = calculate_team_score_for_week(db_session, sample_league.id, 1, team.id)
    assert team_score is not None
    # Should be sum of top 2 scores (35.0 + 36.0 = 71.0)
    assert team_score == 71.0


def test_get_all_weeks(db_session, sample_league, sample_scores):
    """Test getting all weeks with scores."""
    weeks = get_all_weeks(db_session, sample_league.id)
    assert 1 in weeks

