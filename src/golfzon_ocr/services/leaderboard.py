"""
Leaderboard calculation and display functions.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ..db import (
    get_league, list_teams, get_all_weeks,
    get_top_two_scores_per_team, calculate_team_score_for_week,
    get_scores_by_week
)
from ..models import Team


def calculate_weekly_standings(db: Session, league_id: int, week_number: int) -> List[Dict]:
    """
    Calculate standings for a specific week.
    Returns a list of dictionaries with team info and score, sorted by score (lowest first).
    """
    # Get all teams in the league
    teams = list_teams(db, league_id=league_id)
    
    # Get top 2 scores per team for this week
    top_scores = get_top_two_scores_per_team(db, league_id, week_number)
    
    standings = []
    for team in teams:
        team_score = None
        top_two_scores = top_scores.get(team.id, [])
        
        if len(top_two_scores) >= 2:
            # Team has 2+ scores - sum of top 2
            team_score = sum(score.net_score for score in top_two_scores[:2])
        elif len(top_two_scores) == 1:
            # Team has only 1 score - show partial score
            team_score = top_two_scores[0].net_score
        
        standings.append({
            'team_id': team.id,
            'team_name': team.name,
            'score': team_score,
            'top_two_scores': [
                {'player_name': score.player.name, 'net_score': score.net_score}
                for score in top_two_scores[:2]
            ],
            'player_count': len(top_two_scores),
            'is_complete': len(top_two_scores) >= 2
        })
    
    # Sort by score (lowest first), incomplete teams (with 1 score) go before teams with no scores
    standings.sort(key=lambda x: (
        x['score'] is None,  # Teams with no scores go last
        not x.get('is_complete', False),  # Incomplete teams go before complete teams
        x['score'] or float('inf')
    ))
    
    return standings


def calculate_cumulative_standings(db: Session, league_id: int) -> List[Dict]:
    """
    Calculate cumulative standings across all weeks.
    Returns a list of dictionaries with team info and cumulative score.
    """
    # Get all teams in the league
    teams = list_teams(db, league_id=league_id)
    
    # Get all weeks with scores
    weeks = get_all_weeks(db, league_id)
    
    # Initialize team totals
    team_totals = {team.id: {'team': team, 'total_score': 0.0, 'weeks_played': 0, 'weekly_scores': []} 
                   for team in teams}
    
    # Calculate score for each week
    for week_number in weeks:
        standings = calculate_weekly_standings(db, league_id, week_number)
        for standing in standings:
            # Include incomplete scores (single score) in cumulative
            if standing['score'] is not None:
                team_id = standing['team_id']
                team_totals[team_id]['total_score'] += standing['score']
                team_totals[team_id]['weeks_played'] += 1
                team_totals[team_id]['weekly_scores'].append({
                    'week': week_number,
                    'score': standing['score'],
                    'is_complete': standing.get('is_complete', False)
                })
    
    # Convert to list and sort
    cumulative_standings = []
    for team_id, data in team_totals.items():
        cumulative_standings.append({
            'team_id': team_id,
            'team_name': data['team'].name,
            'total_score': data['total_score'],
            'weeks_played': data['weeks_played'],
            'average_score': data['total_score'] / data['weeks_played'] if data['weeks_played'] > 0 else None,
            'weekly_scores': data['weekly_scores']
        })
    
    # Sort by total score (lowest first)
    cumulative_standings.sort(key=lambda x: x['total_score'])
    
    return cumulative_standings


def get_week_by_week_breakdown(db: Session, league_id: int) -> Dict[int, List[Dict]]:
    """
    Get standings for each week.
    Returns a dictionary mapping week_number to standings list.
    """
    weeks = get_all_weeks(db, league_id)
    breakdown = {}
    
    for week_number in weeks:
        breakdown[week_number] = calculate_weekly_standings(db, league_id, week_number)
    
    return breakdown


def get_leaderboard_summary(db: Session, league_id: int) -> Dict:
    """
    Get a complete leaderboard summary including current week and cumulative standings.
    """
    league = get_league(db, league_id)
    if not league:
        return None
    
    weeks = get_all_weeks(db, league_id)
    current_week = max(weeks) if weeks else None
    
    summary = {
        'league_id': league_id,
        'league_name': league.name,
        'current_week': current_week,
        'total_weeks': len(weeks),
        'weeks': weeks
    }
    
    if current_week:
        summary['current_week_standings'] = calculate_weekly_standings(db, league_id, current_week)
    
    summary['cumulative_standings'] = calculate_cumulative_standings(db, league_id)
    summary['week_by_week'] = get_week_by_week_breakdown(db, league_id)
    
    return summary

