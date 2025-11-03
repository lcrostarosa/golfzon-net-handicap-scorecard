"""
Integration tests for the full application flow.
"""
import pytest
from datetime import datetime

from database import create_league, create_team, create_player, create_weekly_score
from teams import match_ocr_players_to_existing
from leaderboard import calculate_weekly_standings, calculate_cumulative_standings


def test_full_flow_ocr_to_leaderboard(db_session):
    """Test the full flow from OCR to leaderboard."""
    # 1. Create league
    league = create_league(db_session, "Test League")
    
    # 2. Create teams
    team1 = create_team(db_session, league.id, "Team A")
    team2 = create_team(db_session, league.id, "Team B")
    
    # 3. Create players
    player1a = create_player(db_session, team1.id, "Player 1A")
    player1b = create_player(db_session, team1.id, "Player 1B")
    player2a = create_player(db_session, team2.id, "Player 2A")
    player2b = create_player(db_session, team2.id, "Player 2B")
    
    # 4. Simulate OCR results
    ocr_players = [
        {"name": "Player 1A", "gross_score": 40, "handicap": 10.0},
        {"name": "Player 1B", "gross_score": 41, "handicap": 10.0},
        {"name": "Player 2A", "gross_score": 42, "handicap": 10.0},
        {"name": "Player 2B", "gross_score": 43, "handicap": 10.0},
    ]
    
    # 5. Match OCR players
    matches = match_ocr_players_to_existing(db_session, ocr_players, league.id)
    assert len(matches) == 4
    assert all(m['action'] == 'matched' for m in matches)
    
    # 6. Create scores (simulating calculated net scores)
    week = 1
    net_scores = [35.0, 36.0, 37.0, 38.0]  # Calculated net scores
    
    for match, net_score in zip(matches, net_scores):
        player = match['player']
        ocr_data = match['ocr_data']
        create_weekly_score(
            db_session,
            player_id=player.id,
            league_id=league.id,
            week_number=week,
            date=datetime.now(),
            gross_score=ocr_data['gross_score'],
            handicap=ocr_data['handicap'],
            strokes_given=5.0,
            net_score=net_score,
            num_holes=9
        )
    
    # 7. Calculate standings
    standings = calculate_weekly_standings(db_session, league.id, week)
    assert len(standings) == 2
    
    # Team 1 should win (35 + 36 = 71 vs 37 + 38 = 75)
    team1_standing = next(s for s in standings if s['team_id'] == team1.id)
    team2_standing = next(s for s in standings if s['team_id'] == team2.id)
    assert team1_standing['score'] < team2_standing['score']


def test_multi_week_scenario(db_session):
    """Test multiple weeks scenario."""
    league = create_league(db_session, "Test League")
    team = create_team(db_session, league.id, "Team A")
    player1 = create_player(db_session, team.id, "Player 1")
    player2 = create_player(db_session, team.id, "Player 2")
    
    # Week 1 scores
    create_weekly_score(db_session, player1.id, league.id, 1, datetime.now(), 40, 10.0, 5.0, 35.0, 9)
    create_weekly_score(db_session, player2.id, league.id, 1, datetime.now(), 41, 10.0, 5.0, 36.0, 9)
    
    # Week 2 scores
    create_weekly_score(db_session, player1.id, league.id, 2, datetime.now(), 39, 10.0, 5.0, 34.0, 9)
    create_weekly_score(db_session, player2.id, league.id, 2, datetime.now(), 42, 10.0, 5.0, 37.0, 9)
    
    # Check cumulative standings
    cumulative = calculate_cumulative_standings(db_session, league.id)
    team_standing = next(s for s in cumulative if s['team_id'] == team.id)
    assert team_standing['total_score'] == 142.0  # 71 + 71
    assert team_standing['weeks_played'] == 2

