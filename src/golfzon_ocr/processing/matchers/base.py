"""
Base matcher class for player data extraction strategies.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from ..extractors import NameExtractor, ScoreExtractor, HandicapExtractor


class BaseMatcher(ABC):
    """Abstract base class for player data matching strategies."""
    
    def __init__(self):
        """Initialize extractors used by matchers."""
        self.name_extractor = NameExtractor()
        self.score_extractor = ScoreExtractor()
        self.handicap_extractor = HandicapExtractor()
    
    @abstractmethod
    def find_players(self, text: str) -> List[Dict[str, any]]:
        """
        Find player data in OCR text using this strategy.
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            List of player dictionaries with keys: name, gross_score, handicap
        """
        pass
    
    def _create_player(
        self, 
        name: str, 
        gross_score: int, 
        handicap: float
    ) -> Dict[str, any]:
        """
        Create a player dictionary.
        
        Args:
            name: Player name (can be empty string)
            gross_score: Gross score
            handicap: Handicap value
            
        Returns:
            Player dictionary
        """
        return {
            "name": name,
            "gross_score": gross_score,
            "handicap": handicap
        }

