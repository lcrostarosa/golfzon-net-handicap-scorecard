"""
Calculator module for computing net scores based on handicaps.
"""
from typing import List, Dict, Optional
import math


def calculate_net_scores(players: List[Dict[str, any]], num_holes: int = 9) -> List[Dict[str, any]]:
    """
    Calculate net scores for each player based on their handicap.
    
    For 9-hole rounds: strokes_given = handicap / 2
    For 18-hole rounds: strokes_given = handicap
    
    Args:
        players: List of player dictionaries with "name", "gross_score", "handicap"
        num_holes: Number of holes (9 or 18)
        
    Returns:
        List of player dictionaries with added "strokes_given" and "net_score" fields
        
    Raises:
        ValueError: If players list is empty or contains invalid data
    """
    if not players:
        raise ValueError("Players list is empty")
    
    if num_holes not in [9, 18]:
        raise ValueError(f"Invalid number of holes: {num_holes}. Must be 9 or 18.")
    
    results = []
    
    for player in players:
        # Validate required fields
        if "name" not in player:
            continue
        if "gross_score" not in player or "handicap" not in player:
            continue
        
        try:
            handicap = float(player["handicap"])
            gross_score = int(player["gross_score"])
            
            # Validate score ranges
            if gross_score < 1 or gross_score > 200:
                continue
            
            # Calculate strokes given based on number of holes
            if num_holes == 9:
                strokes_given = handicap / 2
            elif num_holes == 18:
                strokes_given = handicap
            else:
                # Default to 9-hole calculation for other values
                strokes_given = handicap / 2
            
            # Calculate net score
            net_score = gross_score - strokes_given
            
            # Create result dictionary with all fields
            result = {
                "name": str(player["name"]),
                "gross_score": gross_score,
                "handicap": handicap,
                "strokes_given": math.ceil(strokes_given * 100) / 100,  # Round up to 2 decimal places
                "net_score": math.ceil(net_score * 100) / 100  # Round up to 2 decimal places
            }
            
            results.append(result)
            
        except (ValueError, TypeError, KeyError) as e:
            # Skip players with invalid data
            continue
    
    if not results:
        raise ValueError("No valid player data found after calculation")
    
    # Sort by net score (lowest wins)
    results.sort(key=lambda x: x["net_score"])
    
    return results


def recalculate_net_scores(players: List[Dict[str, any]], num_holes: int = 9, auto_calculate_strokes: bool = True) -> List[Dict[str, any]]:
    """
    Recalculate net scores for players, handling manual strokes_given values.
    
    This function is used when players have already been calculated and may have
    manual edits to handicap, gross_score, or strokes_given.
    
    Args:
        players: List of player dictionaries with "name", "gross_score", "handicap", 
                 and optionally "strokes_given" (if manual)
        num_holes: Number of holes (9 or 18)
        auto_calculate_strokes: If True, calculate strokes_given from handicap.
                               If False, use existing strokes_given value.
        
    Returns:
        List of player dictionaries with updated "strokes_given" and "net_score" fields
        
    Raises:
        ValueError: If players list is empty or contains invalid data
    """
    if not players:
        raise ValueError("Players list is empty")
    
    if num_holes not in [9, 18]:
        raise ValueError(f"Invalid number of holes: {num_holes}. Must be 9 or 18.")
    
    results = []
    
    for player in players:
        # Validate required fields
        if "name" not in player:
            continue
        if "gross_score" not in player or "handicap" not in player:
            continue
        
        try:
            handicap = float(player["handicap"])
            gross_score = int(player["gross_score"])
            
            # Validate score ranges
            if gross_score < 1 or gross_score > 200:
                continue
            
            # Calculate or use existing strokes_given
            if auto_calculate_strokes or "strokes_given" not in player:
                # Calculate strokes given based on number of holes
                if num_holes == 9:
                    strokes_given = handicap / 2
                elif num_holes == 18:
                    strokes_given = handicap
                else:
                    # Default to 9-hole calculation for other values
                    strokes_given = handicap / 2
            else:
                # Use existing strokes_given value (manual edit)
                strokes_given = float(player["strokes_given"])
            
            # Calculate net score
            net_score = gross_score - strokes_given
            
            # Create result dictionary with all fields
            result = {
                "name": str(player["name"]),
                "gross_score": gross_score,
                "handicap": handicap,
                "strokes_given": math.ceil(strokes_given * 100) / 100,  # Round up to 2 decimal places
                "net_score": math.ceil(net_score * 100) / 100  # Round up to 2 decimal places
            }
            
            results.append(result)
            
        except (ValueError, TypeError, KeyError) as e:
            # Skip players with invalid data
            continue
    
    if not results:
        raise ValueError("No valid player data found after calculation")
    
    # Sort by net score (lowest wins)
    results.sort(key=lambda x: x["net_score"])
    
    return results


def calculate_gross_from_holes(hole_scores: List[Optional[int]]) -> Optional[int]:
    """
    Calculate gross score from hole-by-hole scores.
    
    Args:
        hole_scores: List of scores for each hole (None for missing scores)
        
    Returns:
        Total gross score, or None if no valid scores
    """
    if not hole_scores:
        return None
    
    # Filter out None values and sum
    valid_scores = [s for s in hole_scores if s is not None]
    if not valid_scores:
        return None
    
    return sum(valid_scores)


def recalculate_from_hole_scores(
    player_name: str,
    hole_scores: List[Optional[int]],
    handicap: float,
    num_holes: int = 9,
    auto_calculate_strokes: bool = True,
    strokes_given: Optional[float] = None
) -> Dict[str, any]:
    """
    Recalculate player totals from hole-by-hole scores.
    
    Args:
        player_name: Player's name
        hole_scores: List of scores for each hole
        handicap: Player's handicap
        num_holes: Number of holes (9 or 18)
        auto_calculate_strokes: If True, calculate strokes from handicap
        strokes_given: Manual strokes_given value (used if auto_calculate_strokes=False)
        
    Returns:
        Dictionary with player data including recalculated gross and net scores
    """
    # Calculate gross score from holes
    gross_score = calculate_gross_from_holes(hole_scores)
    
    if gross_score is None:
        # No valid hole scores, return minimal data
        return {
            "name": player_name,
            "gross_score": 0,
            "handicap": handicap,
            "strokes_given": 0.0,
            "net_score": 0.0,
            "hole_scores": hole_scores
        }
    
    # Calculate strokes given
    if auto_calculate_strokes:
        if num_holes == 9:
            calc_strokes = handicap / 2
        else:
            calc_strokes = handicap
    else:
        calc_strokes = strokes_given if strokes_given is not None else handicap
    
    # Calculate net score
    net_score = gross_score - calc_strokes
    
    return {
        "name": player_name,
        "gross_score": gross_score,
        "handicap": handicap,
        "strokes_given": math.ceil(calc_strokes * 100) / 100,
        "net_score": math.ceil(net_score * 100) / 100,
        "hole_scores": hole_scores
    }
