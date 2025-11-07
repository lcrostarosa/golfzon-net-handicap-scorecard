"""
Player data validation and deduplication module.
"""
from typing import List, Dict, Set
from .. import pattern_config
from ..extractors import ScoreExtractor, HandicapExtractor


class PlayerValidator:
    """Validates and deduplicates player data."""
    
    def __init__(self):
        """Initialize extractors for validation."""
        self.score_extractor = ScoreExtractor()
        self.handicap_extractor = HandicapExtractor()
    
    def validate_and_deduplicate(
        self, 
        players: List[Dict[str, any]], 
        add_placeholders: bool = True,
        ocr_text: str = ""
    ) -> List[Dict[str, any]]:
        """
        Validate, deduplicate, and optionally add placeholders for unmatched scores.
        
        Args:
            players: List of player dictionaries
            add_placeholders: Whether to add placeholder players for unmatched scores
            ocr_text: Original OCR text (needed for placeholder creation)
            
        Returns:
            Cleaned and validated list of players
        """
        # First pass: deduplicate by score+handicap combination
        players = self._deduplicate_by_combination(players)
        
        # Second pass: prefer players with names over empty names
        players = self._prefer_named_players(players)
        
        # Add placeholders for unmatched scores if requested
        if add_placeholders and ocr_text:
            players = self._add_placeholders_for_unmatched_scores(players, ocr_text)
        
        # Limit to max players
        players = self._limit_to_max_players(players)
        
        return players
    
    def _deduplicate_by_combination(
        self, 
        players: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Remove duplicate players based on score+handicap combination.
        
        Args:
            players: List of player dictionaries
            
        Returns:
            Deduplicated list
        """
        seen_combinations = {}
        deduplicated = []
        
        for player in players:
            key = (player.get('gross_score'), round(player.get('handicap', 0), 1))
            if key not in seen_combinations:
                seen_combinations[key] = player
                deduplicated.append(player)
        
        return deduplicated
    
    def _prefer_named_players(
        self, 
        players: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        When duplicates exist, prefer the one with a name.
        
        Args:
            players: List of player dictionaries
            
        Returns:
            List with named players preferred
        """
        seen_combinations = {}
        result = []
        
        for player in players:
            key = (player.get('gross_score'), round(player.get('handicap', 0), 1))
            
            if key not in seen_combinations:
                seen_combinations[key] = player
                result.append(player)
            else:
                # If current player has a name and existing doesn't, replace it
                existing = seen_combinations[key]
                if not existing.get('name', '').strip() and player.get('name', '').strip():
                    result.remove(existing)
                    result.append(player)
                    seen_combinations[key] = player
        
        return result
    
    def _add_placeholders_for_unmatched_scores(
        self, 
        players: List[Dict[str, any]], 
        ocr_text: str
    ) -> List[Dict[str, any]]:
        """
        Find scores in OCR text that weren't matched to players and add them as placeholders.
        
        Args:
            players: Existing players
            ocr_text: Original OCR text
            
        Returns:
            Players with placeholders added
        """
        # Get all score+handicap combinations we already have
        existing_combinations = set()
        for player in players:
            key = (player.get('gross_score'), round(player.get('handicap', 0), 1))
            existing_combinations.add(key)
        
        # Find all scores in the text
        all_scores = self.score_extractor.find_all_scores(ocr_text)
        
        # Try to match each score with a handicap
        unmatched = []
        for score, score_start, score_end in all_scores:
            # Stop if we already have max players
            if len(players) + len(unmatched) >= pattern_config.MAX_PLAYERS:
                break
            
            # Look for handicap after this score
            after_text = ocr_text[score_end:min(len(ocr_text), score_end + 100)]
            handicap = self.handicap_extractor.find_and_normalize(after_text)
            
            if handicap is not None:
                key = (score, round(handicap, 1))
                if key not in existing_combinations:
                    # Found an unmatched score+handicap
                    unmatched.append({
                        "name": "",  # Empty name for manual editing
                        "gross_score": score,
                        "handicap": handicap
                    })
                    existing_combinations.add(key)
        
        return players + unmatched
    
    def _limit_to_max_players(
        self, 
        players: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Limit players to maximum allowed, preferring those with names.
        
        Args:
            players: List of player dictionaries
            
        Returns:
            Limited list
        """
        if len(players) <= pattern_config.MAX_PLAYERS:
            return players
        
        # Sort: players with names first, then by score
        players.sort(key=lambda p: (
            p.get('name', '').strip() == '', 
            p.get('gross_score', 999)
        ))
        
        return players[:pattern_config.MAX_PLAYERS]
    
    def is_valid_player(self, player: Dict[str, any]) -> bool:
        """
        Check if a player dictionary has valid data.
        
        Args:
            player: Player dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Must have score and handicap
        if 'gross_score' not in player or 'handicap' not in player:
            return False
        
        # Validate score range
        score = player['gross_score']
        if not self.score_extractor.is_valid_score(score):
            return False
        
        # Validate handicap range
        handicap = player['handicap']
        if handicap < pattern_config.MIN_HANDICAP or handicap > pattern_config.MAX_HANDICAP:
            return False
        
        return True

