"""
Table-based matching strategy.
Processes OCR output that's in table format with pipes and separators.
"""
import re
from typing import List, Dict, Optional
from .base import BaseMatcher


class TableMatcher(BaseMatcher):
    """
    Matches players from table-like formatted text.
    
    This strategy looks for table rows with pipes/separators and extracts data.
    """
    
    # Pattern for finding table rows (allow digits in names)
    TABLE_ROW_PATTERN = re.compile(r'\|.*?([A-Z][a-z0-9]{2,}).*?\|')
    
    def find_players(self, text: str) -> List[Dict[str, any]]:
        """
        Find players by parsing table-formatted text.
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            List of player dictionaries
        """
        players = []
        seen_names = set()
        
        for match in self.TABLE_ROW_PATTERN.finditer(text):
            player = self._process_table_row(match, text)
            if player:
                name_lower = player['name'].lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    players.append(player)
        
        return players
    
    def _process_table_row(
        self, 
        match: re.Match, 
        text: str
    ) -> Optional[Dict[str, any]]:
        """
        Process a table row match to extract player data.
        
        Args:
            match: Regex match for table row
            text: Full text
            
        Returns:
            Player dictionary if valid data found, None otherwise
        """
        name = match.group(1).strip()
        
        # Clean and validate name
        name = self.name_extractor.clean_name(name)
        if not self.name_extractor._is_valid_name(name):
            return None
        
        # Get context around this match (100 chars before and 200 after)
        match_start = match.start()
        match_end = match.end()
        context_start = max(0, match_start - 100)
        context_end = min(len(text), match_end + 200)
        context_text = text[context_start:context_end]
        
        # Look for score in context
        score_info = self.score_extractor.find_score(context_text)
        if not score_info:
            # Try to find just a 2-3 digit number
            score_match = re.search(r'(\d{2,3})(?![.\d])', context_text)
            if score_match:
                gross_score = self.score_extractor.parse_score(score_match.group(1))
            else:
                return None
        else:
            gross_score, _, _ = score_info
        
        if gross_score is None:
            return None
        
        # Look for handicap in context
        handicap = self.handicap_extractor.find_and_normalize(context_text)
        if handicap is None:
            return None
        
        return self._create_player(name, gross_score, handicap)

