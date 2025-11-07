"""
Score extraction and validation module.
"""
from typing import Optional, Tuple
from .. import pattern_config


class ScoreExtractor:
    """Extracts and validates gross score values from OCR text."""
    
    def find_score(self, text: str, start_pos: int = 0) -> Optional[Tuple[int, int, int]]:
        """
        Find a score pattern in text starting from start_pos.
        
        Args:
            text: Text to search
            start_pos: Position to start searching from
            
        Returns:
            Tuple of (score, match_start, match_end) if found, None otherwise
        """
        search_text = text[start_pos:]
        
        # Try main score pattern first
        match = pattern_config.SCORE_PATTERN.search(search_text)
        if match:
            try:
                score = int(match.group(1))
                if self.is_valid_score(score):
                    return (score, start_pos + match.start(), start_pos + match.end())
            except ValueError:
                pass
        
        return None
    
    def find_all_scores(self, text: str) -> list:
        """
        Find all score patterns in text.
        
        Args:
            text: Text to search
            
        Returns:
            List of tuples: [(score, start_pos, end_pos), ...]
        """
        scores = []
        
        for match in pattern_config.SCORE_PATTERN.finditer(text):
            try:
                score = int(match.group(1))
                if self.is_valid_score(score):
                    scores.append((score, match.start(), match.end()))
            except ValueError:
                continue
        
        return scores
    
    def is_valid_score(self, score: int) -> bool:
        """
        Check if a score is within valid range.
        
        Args:
            score: Score to validate
            
        Returns:
            True if valid, False otherwise
        """
        return pattern_config.MIN_GROSS_SCORE <= score <= pattern_config.MAX_GROSS_SCORE
    
    def parse_score(self, score_str: str) -> Optional[int]:
        """
        Parse a score string to integer with validation.
        
        Args:
            score_str: String representation of score
            
        Returns:
            Score as integer if valid, None otherwise
        """
        try:
            score = int(score_str)
            return score if self.is_valid_score(score) else None
        except ValueError:
            return None

