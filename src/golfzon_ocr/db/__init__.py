"""
Database package for Golfzon OCR.
"""
from .database import (
    get_db, get_db_context, init_db, get_engine,
    create_league, get_league, get_league_by_name, list_leagues, delete_league,
    create_team, get_team, list_teams, delete_team,
    create_player, get_player, find_player_by_name, list_players, delete_player,
    create_weekly_score, get_weekly_score, get_scores_by_week,
    get_player_scores_by_week, get_top_two_scores_per_team,
    calculate_team_score_for_week, get_all_weeks, delete_weekly_score,
    DATABASE_URL
)
from .corrections import (
    create_correction, get_all_corrections, get_correction,
    find_correction_for_text, increment_correction_usage,
    apply_corrections_to_text, delete_correction, get_correction_stats
)

__all__ = [
    'get_db', 'get_db_context', 'init_db', 'get_engine',
    'create_league', 'get_league', 'get_league_by_name', 'list_leagues', 'delete_league',
    'create_team', 'get_team', 'list_teams', 'delete_team',
    'create_player', 'get_player', 'find_player_by_name', 'list_players', 'delete_player',
    'create_weekly_score', 'get_weekly_score', 'get_scores_by_week',
    'get_player_scores_by_week', 'get_top_two_scores_per_team',
    'calculate_team_score_for_week', 'get_all_weeks', 'delete_weekly_score',
    'DATABASE_URL',
    'create_correction', 'get_all_corrections', 'get_correction',
    'find_correction_for_text', 'increment_correction_usage',
    'apply_corrections_to_text', 'delete_correction', 'get_correction_stats'
]

