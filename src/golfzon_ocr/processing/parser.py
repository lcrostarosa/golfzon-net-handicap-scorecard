"""
Parser module for extracting player data from OCR text.

This module provides a clean facade over the parsing pipeline:
1. Text cleaning (OCR error correction)
2. Player matching (using multiple strategies)
3. Validation and deduplication

Public API:
    - parse_players(ocr_text, backup_ocr_text, db) -> List[Dict]
    - clean_ocr_text(text) -> str (for backwards compatibility)
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from .text_cleaner import TextCleaner
from .matchers import ScoreMatcher, LineMatcher, TableMatcher
from .validators import PlayerValidator


def clean_ocr_text(text: str, db: Optional[Session] = None) -> str:
    """
    Clean OCR text to handle common misreads and noise.
    
    This function is maintained for backwards compatibility.
    
    Args:
        text: Raw OCR text
        db: Optional database session for applying learned corrections
        
    Returns:
        Cleaned text string
    """
    cleaner = TextCleaner(db)
    return cleaner.clean(text)


def parse_players(
    ocr_text: str,
    backup_ocr_text: str = None,  # noqa: ARG001 - kept for compatibility
    db: Optional[Session] = None
) -> List[Dict[str, any]]:
    """
    Parse player data from OCR text using multiple matching strategies.
    
    Expected pattern: PlayerName GrossScore(+/-X) Handicap
    Example: "Acorm 38(+2) -2.2"
    
    If scores are detected but names are missing, creates placeholder players
    with empty names that can be manually edited.
    
    Args:
        ocr_text: Raw OCR text string
        backup_ocr_text: Optional backup OCR text (currently unused, kept for compatibility)
        db: Optional database session for applying learned corrections
        
    Returns:
        List of dictionaries with player data:
        [{"name": str, "gross_score": int, "handicap": float}, ...]
        Names may be empty strings if not detected.
        
    Raises:
        ValueError: If ocr_text is empty or invalid
    """
    if not ocr_text or not ocr_text.strip():
        raise ValueError("OCR text is empty")
    
    # Step 1: Clean the OCR text
    cleaner = TextCleaner(db)
    cleaned_text = cleaner.clean(ocr_text)
    
    # Step 2: Apply multiple matching strategies
    all_players = []
    
    # Strategy 1: Score-based matching (find scores first, then names/handicaps)
    score_matcher = ScoreMatcher(db)
    all_players.extend(score_matcher.find_players(cleaned_text))
    
    # Strategy 2: Line-by-line matching
    line_matcher = LineMatcher(db)
    all_players.extend(line_matcher.find_players(cleaned_text))
    
    # Strategy 3: Table-based matching
    table_matcher = TableMatcher(db)
    all_players.extend(table_matcher.find_players(cleaned_text))
    
    # Step 3: Validate, deduplicate, and add placeholders
    validator = PlayerValidator()
    players = validator.validate_and_deduplicate(
        all_players,
        add_placeholders=True,
        ocr_text=cleaned_text
    )
    
    return players


# Legacy function for backwards compatibility (used in old code)
def process_match(
    match,
    exclude_words,  # noqa: ARG001 - kept for compatibility
    seen_names,
    players
):
    """
    Legacy helper function maintained for backwards compatibility.
    
    This function is no longer used internally but may be called by external code.
    It attempts to extract player data from a regex match.
    
    Args:
        match: Regex match object
        exclude_words: Set of words to exclude
        seen_names: Set of already seen names
        players: List to append valid players to
        
    Returns:
        True if a valid player was added, False otherwise
    """
    from .extractors import NameExtractor, ScoreExtractor, HandicapExtractor
    from . import pattern_config
    
    try:
        name = match.group(1).strip()
        gross_score_str = match.group(2)
        handicap_str = match.group(3)
        
        # Validate name
        name_extractor = NameExtractor()
        name = name_extractor.clean_name(name)
        
        if not name or len(name) < pattern_config.MIN_NAME_LENGTH:
            return False
        
        if pattern_config.is_excluded_word(name):
            return False
        
        if name.isupper() and len(name) < 4:
            return False
        
        if len(name) == 1:
            return False
        
        # Parse score
        score_extractor = ScoreExtractor()
        gross_score = score_extractor.parse_score(gross_score_str)
        if gross_score is None:
            return False
        
        # Parse handicap
        handicap_extractor = HandicapExtractor()
        try:
            handicap = handicap_extractor.normalize(handicap_str)
        except ValueError:
            return False
        
        # Check for duplicates
        if name.lower() in seen_names:
            return False
        
        seen_names.add(name.lower())
        players.append({
            "name": name,
            "gross_score": gross_score,
            "handicap": handicap
        })
        
        return True
        
    except (ValueError, IndexError, TypeError):
        return False
