"""
Configuration for OCR pattern matching and text cleaning.
Contains ONLY generic OCR error patterns, NOT player-specific corrections.
"""
import re
from typing import List, Tuple, Set, Pattern


# Generic OCR character substitution patterns
# Format: (pattern, replacement, flags)
OCR_TEXT_FIXES: List[Tuple[str, str, int]] = [
    # Common letter/number confusions
    (r'(\d+)I\(', r'\g<1>1(', 0),  # "4I(+5" -> "41(+5"
    (r'\b4I\b', '41', 0),
    (r'\b5I\b', '51', 0),
    (r'\b3I\b', '31', 0),
    (r'(\d+)l(\d+)', r'\g<1>.\g<2>', 0),  # "16l1" -> "16.1"
    (r'(\d+)iL(\d+)', r'\g<1>.\g<2>', 0),  # "16iL4" -> "16.4"
    (r'iL', '11', re.IGNORECASE),  # "iL" -> "11"
    (r'(\d+)I', r'\g<1>1', 0),  # Trailing I -> 1
    
    # Handicap pattern fixes
    (r'\+iL\.', '+11.', re.IGNORECASE),
    (r'\-iL\.', '-11.', re.IGNORECASE),
    (r'([+\-]\d+)\.\s', r'\g<1>.1 ', 0),  # "+16." -> "+16.1"
    
    # Score pattern fixes
    (r'B(\d{2})\)', r'\1', 0),  # "B42)" -> "42"
    (r'GIO\s+(\d{2})\)', r'\1', 0),  # "GIO 14)" -> "14"
    
    # Remove common OCR artifacts
    (r'[|_]{2,}', ' ', 0),  # Multiple pipes/underscores -> space
    (r'^[|_\s]+', '', re.MULTILINE),  # Leading pipes/underscores
    (r'[|_\s]+$', '', re.MULTILINE),  # Trailing pipes/underscores
]

# Name cleaning patterns - remove OCR artifacts and prefixes
# Format: (pattern, replacement, flags)
NAME_CLEANING_PATTERNS: List[Tuple[str, str, int]] = [
    (r'[\[|\]|\|\\_]', '', 0),  # Remove brackets, pipes, underscores
    (r'^[0-9]+', '', 0),  # Remove leading numbers
    (r'^[|_]+', '', 0),  # Remove leading pipes/underscores
    (r'^[a-z]([A-Z][a-z]+)', r'\1', 0),  # "eBeachy" -> "Beachy"
    (r'^[RQ]([A-Z][a-z]+)', r'\1', 0),  # "RQFirstOrLast" -> "FirstOrLast"
    (r'^Tl', '', 0),  # Remove "Tl" OCR artifact prefix
    (r'^G\s*', '', 0),  # Remove "G" prefix (common in Golfzon scorecards)
]

# Words to exclude from name matching (generic terms, not player names)
EXCLUDE_WORDS: Set[str] = {
    'golfzon', 'hole', 'total', 'par', 'rank', 'in', 'out', 'round', 
    'mountain', 'west', 'east', 'north', 'south', 'pga', 
    'scorecard', 'statistics', 'rounding', 'record', 'shot', 'analysis', 
    'analy', 'analysi', 'std', 'stat', 'phoenix', 'country', 'club',
    'bay', 'bag', 'bi', 'biais', 'bay', 'beach', 'ocean', 'course',
    # OCR artifacts that look like words
    'gouzatf', 'wests', 'ggovad', 'boiciak', 'boici', 'geet', 'sano',
    'gio', 'bio', 'blo'
}

# Name pattern matching order (by priority)
# Each pattern should extract the name in group(1) where applicable
NAME_PATTERNS: List[Tuple[str, Pattern]] = [
    # Allow digits in names (e.g., "Player1", "Tcdubs21")
    ('standard', re.compile(r'([A-Z][a-z0-9]{2,})(?:\s|$|[|])')),
    ('table_format', re.compile(r'\|.*?([A-Z][a-z0-9]{2,}).*?\|')),
]

# Score patterns
SCORE_PATTERN = re.compile(r'(\d{2,3})\s*\([+\-]?\d+\)')
FRAGMENTED_SCORE_PATTERN = re.compile(r'(\d{2,3})[^0-9]{0,20}([+\-]\d+)')

# Handicap patterns (in order of preference)
HANDICAP_PATTERNS: List[Pattern] = [
    re.compile(r'([+\-]\d+\.\d+)'),  # Full decimal: "+11.4"
    re.compile(r'([+\-]\d+\.)'),  # Ends with dot: "+16."
    re.compile(r'([+\-]\d{1,2})(?![.\d])'),  # Integer: "+11"
]

# Validation ranges
MIN_GROSS_SCORE = 1
MAX_GROSS_SCORE = 200
MIN_HANDICAP = -50.0
MAX_HANDICAP = 50.0
MIN_PLAYERS = 1
MAX_PLAYERS = 6

# Minimum name length after cleaning
MIN_NAME_LENGTH = 2


def apply_text_fixes(text: str) -> str:
    """Apply all OCR text fixes to the input text."""
    for pattern, replacement, flags in OCR_TEXT_FIXES:
        text = re.sub(pattern, replacement, text, flags=flags)
    return text


def clean_name(name: str) -> str:
    """Apply all name cleaning patterns."""
    for pattern, replacement, flags in NAME_CLEANING_PATTERNS:
        name = re.sub(pattern, replacement, name, flags=flags)
    return name.strip()


def is_excluded_word(word: str) -> bool:
    """Check if a word should be excluded from name matching."""
    return word.lower() in EXCLUDE_WORDS


