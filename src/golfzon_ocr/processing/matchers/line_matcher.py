"""
Line-by-line matching strategy.
Processes each line individually looking for complete player data.
"""
import re
from typing import List, Dict, Optional
from .base import BaseMatcher


class LineMatcher(BaseMatcher):
    """
    Matches players by processing text line-by-line.
    
    This strategy works well when player data is on a single line or spans few lines.
    """
    
    # Regex patterns for matching player data on a line
    PATTERNS = [
        # Complete match with decimal handicap (allow camelCase and digits in names)
        re.compile(r'([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*).*?(\d{2,3})\(.*?([+\-]\d+\.\d+)', re.IGNORECASE),
        # Score with incomplete handicap (ends with .)
        re.compile(r'([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*).*?(\d{2,3})\(.*?([+\-]\d+\.)', re.IGNORECASE),
        # Score without parentheses
        re.compile(r'([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*).*?(\d{2,3})\s+[+\-]?\d+\s+([+\-]\d+\.?\d*)', re.IGNORECASE),
        # Very flexible - just name and numbers
        re.compile(r'([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*).*?(\d{2,3})\s*([+\-]\d+)', re.IGNORECASE),
        # Score with parentheses, find handicap separately
        re.compile(r'([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*).*?(\d{2,3})\s*\([+\-]?\d+\)?', re.IGNORECASE),
    ]
    
    def find_players(self, text: str) -> List[Dict[str, any]]:
        """
        Find players by processing text line-by-line.
        
        Args:
            text: Cleaned OCR text
            
        Returns:
            List of player dictionaries
        """
        players = []
        seen_names = set()
        lines = text.split('\n')
        
        for line_idx, line in enumerate(lines):
            player = self._process_line(line, lines, line_idx)
            if player:
                name_lower = player['name'].lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    players.append(player)
        
        return players
    
    def _process_line(
        self, 
        line: str, 
        all_lines: List[str], 
        line_idx: int
    ) -> Optional[Dict[str, any]]:
        """
        Try to extract a player from a single line.
        
        Args:
            line: Current line to process
            all_lines: All lines (for looking ahead)
            line_idx: Index of current line
            
        Returns:
            Player dictionary if found, None otherwise
        """
        for pattern in self.PATTERNS:
            matches = list(pattern.finditer(line))
            for match in matches:
                player = self._extract_from_match(match, line, all_lines, line_idx)
                if player:
                    return player
        
        return None
    
    def _extract_from_match(
        self, 
        match: re.Match, 
        line: str, 
        all_lines: List[str], 
        line_idx: int
    ) -> Optional[Dict[str, any]]:
        """
        Extract player data from a regex match.
        
        Args:
            match: Regex match object
            line: Current line
            all_lines: All lines
            line_idx: Current line index
            
        Returns:
            Player dictionary if valid, None otherwise
        """
        try:
            name = match.group(1).strip()
            gross_score_str = match.group(2)
            
            # Clean and validate name
            name = self.name_extractor.clean_name(name)
            if not self.name_extractor._is_valid_name(name):
                return None
            
            # Parse score
            gross_score = self.score_extractor.parse_score(gross_score_str)
            if gross_score is None:
                return None
            
            # Try to get handicap from match
            handicap = None
            if len(match.groups()) >= 3:
                handicap_str = match.group(3)
                try:
                    handicap = self.handicap_extractor.normalize(handicap_str)
                except ValueError:
                    handicap = None
            
            # If no handicap in match, look elsewhere on line or nearby lines
            if handicap is None:
                handicap = self.handicap_extractor.find_and_normalize(line)
            
            # Try next few lines if still no handicap
            if handicap is None and line_idx < len(all_lines) - 1:
                for next_idx in range(line_idx + 1, min(line_idx + 3, len(all_lines))):
                    handicap = self.handicap_extractor.find_and_normalize(all_lines[next_idx])
                    if handicap is not None:
                        break
            
            # Must have a handicap to create a player
            if handicap is None:
                return None
            
            return self._create_player(name, gross_score, handicap)
            
        except (ValueError, IndexError, AttributeError):
            return None

