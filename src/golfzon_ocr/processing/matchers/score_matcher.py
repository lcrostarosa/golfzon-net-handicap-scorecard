"""
Score-based matching strategy.
Finds scores first, then looks for names and handicaps nearby.
"""
from typing import List, Dict
from .base import BaseMatcher


class ScoreMatcher(BaseMatcher):
    """
    Matches players by finding scores first, then searching for nearby names and handicaps.
    
    This strategy works well for Golfzon scorecards where the format is typically:
    Score → Handicap → Name
    """
    
    def find_players(self, text: str) -> List[Dict[str, any]]:
        """
        Find players by locating scores and matching them with nearby data.
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            List of player dictionaries
        """
        players = []
        seen_combinations = set()
        
        # Find all scores in the text
        all_scores = self.score_extractor.find_all_scores(text)
        
        for score, score_start, score_end in all_scores:
            # Look for handicap after the score (within 100 chars)
            # Limit search to before the next score to avoid matching data from other players
            next_score_start = self._find_next_score_position(text, score_end, all_scores)
            search_end = min(len(text), next_score_start)
            
            after_text = text[score_end:search_end]
            handicap = self.handicap_extractor.find_and_normalize(after_text, 0)
            
            if handicap is None:
                continue
            
            # Look for name near the score (prefer names AFTER score)
            name = self.name_extractor.find_closest_name(text, score_start, 100, 100)
            if name is None:
                name = ""
            
            # Check for duplicates
            key = (score, round(handicap, 1))
            if key not in seen_combinations:
                seen_combinations.add(key)
                players.append(self._create_player(name, score, handicap))
        
        return players
    
    def _find_next_score_position(
        self, 
        text: str, 
        current_end: int, 
        all_scores: List[tuple]
    ) -> int:
        """
        Find the position of the next score after current_end.
        
        Args:
            text: Full text
            current_end: End position of current score
            all_scores: List of all score tuples
            
        Returns:
            Position of next score, or end of text if no more scores
        """
        for score, start, end in all_scores:
            if start > current_end:
                return start
        return len(text)

