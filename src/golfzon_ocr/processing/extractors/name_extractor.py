"""
Name extraction module for finding player names in OCR text.
"""
import re
from typing import Optional, List, Tuple
from .. import pattern_config


class NameExtractor:
    """Extracts and cleans player names from OCR text."""
    
    def find_closest_name(
        self, 
        text: str, 
        position: int, 
        search_before: int = 100, 
        search_after: int = 100
    ) -> Optional[str]:
        """
        Find the closest name to a given position in text.
        
        Searches both before and after the position, with preference for names
        that appear AFTER the position (typical Golfzon format: Score → Handicap → Name).
        
        Args:
            text: Text to search
            position: Reference position (e.g., score position)
            search_before: Characters to search before position
            search_after: Characters to search after position
            
        Returns:
            Cleaned name if found, None otherwise
        """
        before_text = text[max(0, position - search_before):position]
        after_text = text[position:min(len(text), position + search_after)]
        
        candidates = []
        
        # Search backwards (before position)
        for match in self._find_name_matches(before_text):
            name = self._extract_name_from_match(match)
            if name and self._is_valid_name(name):
                # Calculate distance (negative because it's before)
                distance = len(before_text) - match.end()
                candidates.append((name, distance, False))  # False = before position
        
        # Search forwards (after position) - preferred direction
        for match in self._find_name_matches(after_text):
            name = self._extract_name_from_match(match)
            if name and self._is_valid_name(name):
                # Calculate distance
                distance = match.start()
                candidates.append((name, distance, True))  # True = after position
        
        if not candidates:
            return None
        
        # Sort by effective distance, strongly preferring names AFTER position
        def sort_key(candidate):
            name, distance, is_after = candidate
            if is_after and distance < 100:
                # Names after score get high priority (multiply by 0.3)
                effective_distance = distance * 0.3
            elif not is_after and distance < 50:
                # Names before score get lower priority (multiply by 3.0)
                effective_distance = distance * 3.0
            else:
                effective_distance = distance
            return effective_distance
        
        candidates.sort(key=sort_key)
        closest_name, _, _ = candidates[0]
        
        return self.clean_name(closest_name)
    
    def _find_name_matches(self, text: str) -> List[re.Match]:
        """Find all potential name matches in text."""
        matches = []
        
        # Add special patterns for common OCR artifacts
        # Pattern for names with [el prefix (common in Golfzon OCR)
        special_patterns = [
            re.compile(r'\[el\s+([A-Z][a-z0-9]+)'),
            re.compile(r'\[Tl([A-Z][a-z0-9]+)'),
            re.compile(r'T([Cc]dubs\d+)'),
        ]
        
        for pattern in special_patterns:
            matches.extend(pattern.finditer(text))
        
        # Add standard patterns
        for pattern_name, pattern in pattern_config.NAME_PATTERNS:
            matches.extend(pattern.finditer(text))
        
        return matches
    
    def _extract_name_from_match(self, match: re.Match) -> Optional[str]:
        """Extract name string from a regex match."""
        try:
            if match.groups():
                return match.group(1)
            else:
                return match.group(0)
        except (IndexError, AttributeError):
            return None
    
    def _is_valid_name(self, name: str) -> bool:
        """
        Check if a name is valid (not too short, not an excluded word).
        
        Args:
            name: Name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name or len(name) < pattern_config.MIN_NAME_LENGTH:
            return False
        
        if pattern_config.is_excluded_word(name):
            return False
        
        # Skip if all uppercase and too short (likely not a player name)
        if name.isupper() and len(name) < 4:
            return False
        
        # Skip single letters
        if len(name) == 1:
            return False
        
        return True
    
    def clean_name(self, name: str) -> str:
        """
        Clean a name by removing OCR artifacts and applying fixes.
        
        Args:
            name: Raw name string
            
        Returns:
            Cleaned name string
        """
        return pattern_config.clean_name(name)
    
    def find_all_names(self, text: str) -> List[str]:
        """
        Find all valid names in text.
        
        Args:
            text: Text to search
            
        Returns:
            List of cleaned, valid names
        """
        names = []
        seen = set()
        
        for match in self._find_name_matches(text):
            name = self._extract_name_from_match(match)
            if name and self._is_valid_name(name):
                cleaned = self.clean_name(name)
                if cleaned.lower() not in seen:
                    names.append(cleaned)
                    seen.add(cleaned.lower())
        
        return names

