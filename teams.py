"""
Team management functions.
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from database import (
    create_team, get_team, list_teams, delete_team,
    create_player, get_player, find_player_by_name, list_players, delete_player,
    get_league
)
from models import Team, Player


def create_team_with_players(db: Session, league_id: int, team_name: str, player_names: List[str]) -> Team:
    """Create a team and add players to it."""
    # Verify league exists
    league = get_league(db, league_id)
    if not league:
        raise ValueError(f"League with id {league_id} not found")
    
    # Create team
    team = create_team(db, league_id, team_name)
    
    # Add players
    for player_name in player_names:
        if player_name.strip():
            create_player(db, team.id, player_name.strip())
    
    return team


def add_player_to_team(db: Session, team_id: int, player_name: str) -> Player:
    """Add a player to a team."""
    team = get_team(db, team_id)
    if not team:
        raise ValueError(f"Team with id {team_id} not found")
    
    # Check if player already exists in this team
    existing_player = find_player_by_name(db, player_name, league_id=team.league_id)
    if existing_player and existing_player.team_id == team_id:
        raise ValueError(f"Player '{player_name}' already exists in team '{team.name}'")
    
    return create_player(db, team_id, player_name)


def move_player_to_team(db: Session, player_id: int, new_team_id: int) -> Player:
    """Move a player to a different team."""
    player = get_player(db, player_id)
    if not player:
        raise ValueError(f"Player with id {player_id} not found")
    
    new_team = get_team(db, new_team_id)
    if not new_team:
        raise ValueError(f"Team with id {new_team_id} not found")
    
    # Verify both teams are in the same league
    if player.team.league_id != new_team.league_id:
        raise ValueError("Cannot move player between teams in different leagues")
    
    player.team_id = new_team_id
    db.commit()
    db.refresh(player)
    return player


def get_team_roster(db: Session, team_id: int) -> List[Player]:
    """Get all players on a team."""
    return list_players(db, team_id=team_id)


def match_ocr_players_to_existing(
    db: Session,
    ocr_players: List[Dict],
    league_id: int,
    default_team_id: Optional[int] = None
) -> List[Dict]:
    """
    Match OCR players to existing players in the database.
    Returns a list of dictionaries with 'player' (Player object or None),
    'ocr_data' (original OCR data), and 'action' ('matched', 'new', 'needs_team').
    """
    results = []
    
    for ocr_player in ocr_players:
        player_name = ocr_player.get('name', '').strip()
        if not player_name:
            continue
        
        # Try to find existing player in this league
        existing_player = find_player_by_name(db, player_name, league_id=league_id)
        
        if existing_player:
            results.append({
                'player': existing_player,
                'ocr_data': ocr_player,
                'action': 'matched'
            })
        elif default_team_id:
            # Create new player in default team
            new_player = create_player(db, default_team_id, player_name)
            results.append({
                'player': new_player,
                'ocr_data': ocr_player,
                'action': 'new'
            })
        else:
            # Player not found, needs team assignment
            results.append({
                'player': None,
                'ocr_data': ocr_player,
                'action': 'needs_team'
            })
    
    return results


def get_team_summary(db: Session, team_id: int) -> Dict:
    """Get a summary of a team including player count."""
    team = get_team(db, team_id)
    if not team:
        return None
    
    players = get_team_roster(db, team_id)
    
    return {
        'id': team.id,
        'name': team.name,
        'league_id': team.league_id,
        'player_count': len(players),
        'players': [{'id': p.id, 'name': p.name} for p in players]
    }

