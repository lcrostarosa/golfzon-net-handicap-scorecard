"""
Tests for team management functions.
"""
import pytest

from teams import (
    create_team_with_players, add_player_to_team, move_player_to_team,
    get_team_roster, match_ocr_players_to_existing, get_team_summary
)


def test_create_team_with_players(db_session, sample_league):
    """Test creating a team with players."""
    team = create_team_with_players(
        db_session,
        sample_league.id,
        "Team A",
        ["Player 1", "Player 2"]
    )
    assert team.name == "Team A"
    
    players = get_team_roster(db_session, team.id)
    assert len(players) == 2
    assert all(p.name in ["Player 1", "Player 2"] for p in players)


def test_add_player_to_team(db_session, sample_teams):
    """Test adding a player to a team."""
    team = sample_teams[0]
    player = add_player_to_team(db_session, team.id, "New Player")
    assert player.name == "New Player"
    assert player.team_id == team.id
    
    # Test adding duplicate player
    with pytest.raises(ValueError):
        add_player_to_team(db_session, team.id, "New Player")


def test_move_player_to_team(db_session, sample_teams, sample_players):
    """Test moving a player to a different team."""
    player = sample_players[0]
    original_team_id = player.team_id
    new_team = sample_teams[1]
    
    moved_player = move_player_to_team(db_session, player.id, new_team.id)
    assert moved_player.team_id == new_team.id
    assert moved_player.team_id != original_team_id


def test_get_team_roster(db_session, sample_teams, sample_players):
    """Test getting team roster."""
    team = sample_teams[0]
    roster = get_team_roster(db_session, team.id)
    assert len(roster) == 2  # From fixture


def test_match_ocr_players_to_existing(db_session, sample_league, sample_teams, sample_players):
    """Test matching OCR players to existing players."""
    ocr_players = [
        {"name": "Player Aa", "gross_score": 40, "handicap": 10.0},
        {"name": "New Player", "gross_score": 42, "handicap": 12.0},
    ]
    
    default_team = sample_teams[0]
    matches = match_ocr_players_to_existing(
        db_session,
        ocr_players,
        sample_league.id,
        default_team_id=default_team.id
    )
    
    assert len(matches) == 2
    # First should be matched
    assert matches[0]['action'] == 'matched'
    # Second should be new (created)
    assert matches[1]['action'] == 'new'


def test_get_team_summary(db_session, sample_teams, sample_players):
    """Test getting team summary."""
    team = sample_teams[0]
    summary = get_team_summary(db_session, team.id)
    
    assert summary['id'] == team.id
    assert summary['name'] == team.name
    assert summary['player_count'] == 2

