"""
Handicap extraction and normalization module.
"""
import re
from typing import Optional
from .. import pattern_config


class HandicapExtractor:
    """Extracts and normalizes handicap values from OCR text."""
    
    def find_handicap(self, text: str, start_pos: int = 0) -> Optional[str]:
        """
        Find a handicap value in text starting from start_pos.
        
        Args:
            text: Text to search
            start_pos: Position to start searching from
            
        Returns:
            Handicap string if found, None otherwise
        """
        search_text = text[start_pos:]
        
        for pattern in pattern_config.HANDICAP_PATTERNS:
            match = pattern.search(search_text)
            if match:
                return match.group(1)
        
        return None
    
    def normalize(self, handicap_str: str) -> float:
        """
        Normalize a handicap string to a float value.
        
        Handles common OCR errors like:
        - Missing decimal point: "+16" -> "+16.0"
        - Incomplete decimal: "+16." -> "+16.1"
        - Misread decimal: "-22" might be "-2.2"
        
        Args:
            handicap_str: Raw handicap string
            
        Returns:
            Normalized handicap as float
            
        Raises:
            ValueError: If handicap cannot be parsed
        """
        # Fix common OCR errors in the string
        handicap_str = re.sub(r'iL', '11', handicap_str, flags=re.IGNORECASE)
        handicap_str = re.sub(r'(\d+)I', r'\g<1>1', handicap_str)
        handicap_str = re.sub(r'(\d+)l(\d+)', r'\g<1>.\g<2>', handicap_str)
        handicap_str = re.sub(r'(\d+)i(\d+)', r'\g<1>.\g<2>', handicap_str)
        
        # Fix incomplete or missing decimal point
        if handicap_str.endswith('.'):
            handicap_str = handicap_str + '1'
        elif '.' not in handicap_str:
            # For 3+ character handicaps without decimal, insert decimal point
            if len(handicap_str) > 2:
                # "-22" -> "-2.2"
                handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
            else:
                # "+5" -> "+5.0"
                handicap_str = handicap_str + '.0'
        
        try:
            handicap = float(handicap_str)
            
            # Validate range
            if handicap < pattern_config.MIN_HANDICAP or handicap > pattern_config.MAX_HANDICAP:
                raise ValueError(f"Handicap {handicap} out of valid range")
            
            return handicap
        except ValueError as e:
            raise ValueError(f"Cannot parse handicap '{handicap_str}': {e}")
    
    def find_and_normalize(self, text: str, start_pos: int = 0) -> Optional[float]:
        """
        Find and normalize a handicap in one step.
        
        Args:
            text: Text to search
            start_pos: Position to start searching from
            
        Returns:
            Normalized handicap as float, or None if not found/invalid
        """
        handicap_str = self.find_handicap(text, start_pos)
        if handicap_str:
            try:
                return self.normalize(handicap_str)
            except ValueError:
                return None
        return None

