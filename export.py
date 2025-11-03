"""
CSV export functions for league data.
"""
import csv
import io
from typing import List, Dict
from sqlalchemy.orm import Session

from database import (
    get_league, list_teams, list_players, get_all_weeks,
    get_scores_by_week
)
from leaderboard import calculate_weekly_standings, calculate_cumulative_standings


def export_full_league_data(db: Session, league_id: int) -> str:
    """
    Export complete league data as CSV.
    Returns CSV string with all teams, players, and scores.
    """
    league = get_league(db, league_id)
    if not league:
        raise ValueError(f"League with id {league_id} not found")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['League', league.name])
    writer.writerow([])
    
    # Teams and Players section
    writer.writerow(['Teams and Players'])
    writer.writerow(['Team', 'Player'])
    teams = list_teams(db, league_id=league_id)
    for team in teams:
        players = list_players(db, team_id=team.id)
        for i, player in enumerate(players):
            if i == 0:
                writer.writerow([team.name, player.name])
            else:
                writer.writerow(['', player.name])
        if not players:
            writer.writerow([team.name, '(no players)'])
    
    writer.writerow([])
    
    # Weekly Scores section
    writer.writerow(['Weekly Scores'])
    writer.writerow(['Week', 'Team', 'Player', 'Gross Score', 'Handicap', 'Strokes Given', 'Net Score', 'Holes', 'Date'])
    
    weeks = get_all_weeks(db, league_id)
    for week_number in weeks:
        scores = get_scores_by_week(db, league_id, week_number)
        for score in scores:
            writer.writerow([
                week_number,
                score.player.team.name,
                score.player.name,
                score.gross_score,
                score.handicap,
                score.strokes_given,
                score.net_score,
                score.num_holes,
                score.date.strftime('%Y-%m-%d')
            ])
    
    writer.writerow([])
    
    # Leaderboard section
    writer.writerow(['Weekly Standings'])
    for week_number in weeks:
        standings = calculate_weekly_standings(db, league_id, week_number)
        writer.writerow(['Week', week_number])
        writer.writerow(['Rank', 'Team', 'Score', 'Top Two Players'])
        for rank, standing in enumerate(standings, 1):
            if standing['score'] is not None:
                players_str = ', '.join([f"{s['player_name']} ({s['net_score']})" 
                                        for s in standing['top_two_scores']])
                writer.writerow([rank, standing['team_name'], standing['score'], players_str])
            else:
                writer.writerow([rank, standing['team_name'], 'Incomplete', ''])
        writer.writerow([])
    
    # Cumulative standings
    writer.writerow(['Cumulative Standings'])
    writer.writerow(['Rank', 'Team', 'Total Score', 'Weeks Played', 'Average Score'])
    cumulative = calculate_cumulative_standings(db, league_id)
    for rank, standing in enumerate(cumulative, 1):
        avg_score = standing['average_score'] if standing['average_score'] else ''
        writer.writerow([
            rank,
            standing['team_name'],
            standing['total_score'],
            standing['weeks_played'],
            avg_score
        ])
    
    return output.getvalue()


def export_weekly_summary(db: Session, league_id: int, week_number: int) -> str:
    """
    Export summary for a specific week as CSV.
    """
    league = get_league(db, league_id)
    if not league:
        raise ValueError(f"League with id {league_id} not found")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['League', league.name])
    writer.writerow(['Week', week_number])
    writer.writerow([])
    
    # Standings
    writer.writerow(['Standings'])
    writer.writerow(['Rank', 'Team', 'Score', 'Top Two Players'])
    
    standings = calculate_weekly_standings(db, league_id, week_number)
    for rank, standing in enumerate(standings, 1):
        if standing['score'] is not None:
            players_str = ', '.join([f"{s['player_name']} ({s['net_score']})" 
                                    for s in standing['top_two_scores']])
            writer.writerow([rank, standing['team_name'], standing['score'], players_str])
        else:
            writer.writerow([rank, standing['team_name'], 'Incomplete', ''])
    
    writer.writerow([])
    
    # All scores for the week
    writer.writerow(['All Scores'])
    writer.writerow(['Team', 'Player', 'Gross Score', 'Handicap', 'Strokes Given', 'Net Score', 'Holes'])
    
    scores = get_scores_by_week(db, league_id, week_number)
    for score in scores:
        writer.writerow([
            score.player.team.name,
            score.player.name,
            score.gross_score,
            score.handicap,
            score.strokes_given,
            score.net_score,
            score.num_holes
        ])
    
    return output.getvalue()


def export_team_roster(db: Session, league_id: int) -> str:
    """
    Export team rosters as CSV.
    """
    league = get_league(db, league_id)
    if not league:
        raise ValueError(f"League with id {league_id} not found")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['League', league.name])
    writer.writerow(['Team Rosters'])
    writer.writerow([])
    
    # Teams and players
    writer.writerow(['Team', 'Player'])
    teams = list_teams(db, league_id=league_id)
    for team in teams:
        players = list_players(db, team_id=team.id)
        for i, player in enumerate(players):
            if i == 0:
                writer.writerow([team.name, player.name])
            else:
                writer.writerow(['', player.name])
        if not players:
            writer.writerow([team.name, '(no players)'])
    
    return output.getvalue()

