"""
Tests for leaderboard calculations.
"""
import pytest

from golfzon_ocr.services import (
    calculate_weekly_standings, calculate_cumulative_standings,
    get_week_by_week_breakdown, get_leaderboard_summary
)


def test_calculate_weekly_standings(db_session, sample_league, sample_teams, sample_players):
    """Test calculating weekly standings."""
    from golfzon_ocr.db import create_weekly_score
    from datetime import datetime
    
    # Create scores for week 1
    team = sample_teams[0]
    team_players = [p for p in sample_players if p.team_id == team.id]
    
    # Create 2 scores for team (top 2 will count)
    create_weekly_score(
        db_session,
        player_id=team_players[0].id,
        league_id=sample_league.id,
        week_number=1,
        date=datetime.now(),
        gross_score=40,
        handicap=10.0,
        strokes_given=5.0,
        net_score=35.0,
        num_holes=9
    )
    create_weekly_score(
        db_session,
        player_id=team_players[1].id,
        league_id=sample_league.id,
        week_number=1,
        date=datetime.now(),
        gross_score=41,
        handicap=10.0,
        strokes_given=5.0,
        net_score=36.0,
        num_holes=9
    )
    
    standings = calculate_weekly_standings(db_session, sample_league.id, 1)
    assert len(standings) == 2  # Two teams
    
    # Find team's standing
    team_standing = next(s for s in standings if s['team_id'] == team.id)
    assert team_standing['score'] == 71.0  # 35.0 + 36.0


def test_calculate_cumulative_standings(db_session, sample_league, sample_teams, sample_players):
    """Test calculating cumulative standings."""
    from golfzon_ocr.db import create_weekly_score
    from datetime import datetime
    
    # Create scores for multiple weeks
    team = sample_teams[0]
    team_players = [p for p in sample_players if p.team_id == team.id]
    
    # Week 1: scores 35 and 36
    create_weekly_score(
        db_session,
        player_id=team_players[0].id,
        league_id=sample_league.id,
        week_number=1,
        date=datetime.now(),
        gross_score=40,
        handicap=10.0,
        strokes_given=5.0,
        net_score=35.0,
        num_holes=9
    )
    create_weekly_score(
        db_session,
        player_id=team_players[1].id,
        league_id=sample_league.id,
        week_number=1,
        date=datetime.now(),
        gross_score=41,
        handicap=10.0,
        strokes_given=5.0,
        net_score=36.0,
        num_holes=9
    )
    
    # Week 2: scores 34 and 37
    create_weekly_score(
        db_session,
        player_id=team_players[0].id,
        league_id=sample_league.id,
        week_number=2,
        date=datetime.now(),
        gross_score=39,
        handicap=10.0,
        strokes_given=5.0,
        net_score=34.0,
        num_holes=9
    )
    create_weekly_score(
        db_session,
        player_id=team_players[1].id,
        league_id=sample_league.id,
        week_number=2,
        date=datetime.now(),
        gross_score=42,
        handicap=10.0,
        strokes_given=5.0,
        net_score=37.0,
        num_holes=9
    )
    
    cumulative = calculate_cumulative_standings(db_session, sample_league.id)
    assert len(cumulative) == 2
    
    team_standing = next(s for s in cumulative if s['team_id'] == team.id)
    # Week 1: 35 + 36 = 71, Week 2: 34 + 37 = 71, Total = 142
    assert team_standing['total_score'] == 142.0
    assert team_standing['weeks_played'] == 2


def test_get_leaderboard_summary(db_session, sample_league, sample_scores):
    """Test getting leaderboard summary."""
    summary = get_leaderboard_summary(db_session, sample_league.id)
    
    assert summary['league_id'] == sample_league.id
    assert summary['league_name'] == sample_league.name
    assert 'weeks' in summary
    assert 'cumulative_standings' in summary

