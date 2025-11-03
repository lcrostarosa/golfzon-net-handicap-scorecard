"""
Calculator module for computing net scores based on handicaps.
"""
from typing import List, Dict
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

