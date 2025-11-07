"""
Text cleaning module for OCR output.
Handles noise removal and common OCR misreads using generic patterns.
"""
import re
from typing import List, Optional
from sqlalchemy.orm import Session
from . import pattern_config


class TextCleaner:
    """Cleans OCR text by removing noise and fixing common OCR errors."""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the TextCleaner.
        
        Args:
            db: Optional database session for applying learned corrections
        """
        self.db = db
    
    def clean(self, text: str) -> str:
        """
        Clean OCR text to handle common misreads and noise.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text string
        """
        # Remove noisy lines
        text = self._remove_noise_lines(text)
        
        # Apply OCR character fixes
        text = pattern_config.apply_text_fixes(text)
        
        # Apply database corrections if available
        if self.db:
            text = self._apply_db_corrections(text)
        
        # Fix handicap patterns
        text = self._fix_handicap_patterns(text)
        
        # Fix score patterns
        text = self._fix_score_patterns(text)
        
        # Remove repeated character lines
        text = self._remove_repeated_char_lines(text)
        
        # Clean up whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Only spaces/tabs, not newlines
        
        return text
    
    def _apply_db_corrections(self, text: str) -> str:
        """
        Apply learned corrections from the database.
        
        Args:
            text: Text to apply corrections to
            
        Returns:
            Corrected text
        """
        try:
            from ..db import apply_corrections_to_text
            return apply_corrections_to_text(self.db, text, pattern_type='name')
        except Exception:
            # If database corrections fail, just return the original text
            return text
    
    def _remove_noise_lines(self, text: str) -> List[str]:
        """Remove lines that are mostly noise or special characters."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Count meaningful characters
            meaningful = sum(1 for c in line if c.isalnum())
            total_chars = len(line.strip())
            
            if total_chars == 0:
                continue
                
            # Keep lines that have at least 30% meaningful characters
            if meaningful / total_chars > 0.3 or meaningful >= 3:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_handicap_patterns(self, text: str) -> str:
        """Fix common handicap OCR errors."""
        # Fix handicap misreads: "-22" -> "-2.2" but only if reasonable
        # But AVOID fixing numbers inside score patterns like "43(+13)"
        # Use negative lookbehind to avoid matching numbers after "("
        def fix_handicap(match):
            sign = match.group(1)
            digit1 = match.group(2)
            digit2 = match.group(3)
            
            # Don't convert if > 50 (not a valid handicap)
            if int(digit1 + digit2) > 50:
                return match.group(0)
            
            return f'{sign}{digit1}.{digit2}'
        
        # Use negative lookbehind (?<!\() to avoid matching after opening parenthesis
        text = re.sub(r'(?<!\()([+\-])(\d)(\d)(?:\s|$|[^.\d])', fix_handicap, text)
        return text
    
    def _fix_score_patterns(self, text: str) -> str:
        """Fix common score OCR errors."""
        # Fix OCR errors in numbers: "4347)" -> "43(+7)" pattern
        # Only if it looks like a score pattern (ends with ))
        text = re.sub(r'(\d{2})(\d{2})\)(?!\d)', r'\1(+\2)', text)
        return text
    
    def _remove_repeated_char_lines(self, text: str) -> str:
        """Remove lines that are mostly single characters repeated."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if len(line.strip()) > 0:
                # Check if line is mostly the same character
                unique_chars = len(set(line.strip().replace(' ', '')))
                if unique_chars >= 2 or len(line.strip()) >= 5:
                    cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

