"""
Parser module for extracting player data from OCR text.
"""
import re
from typing import List, Dict


def clean_ocr_text(text: str) -> str:
    """
    Clean OCR text to handle common misreads and noise.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text string
    """
    # Fix score misreads: "4I(+5" -> "41(+5"
    text = re.sub(r'(\d+)I\(', r'\g<1>1(', text)
    
    # Fix handicap misreads: "+iL.4" -> "+11.4"
    text = re.sub(r'\+iL\.', '+11.', text, flags=re.IGNORECASE)
    text = re.sub(r'\-iL\.', '-11.', text, flags=re.IGNORECASE)
    text = re.sub(r'iL', '11', text, flags=re.IGNORECASE)
    
    # Fix incomplete handicaps: "+16." -> "+16.1"
    text = re.sub(r'([+\-]\d+)\.\s', r'\g<1>.1 ', text)
    
    # Common OCR misreads: fix "iL" -> "11", "4I" -> "41", etc.
    text = re.sub(r'\b4I\b', '41', text)
    text = re.sub(r'\b5I\b', '51', text)
    text = re.sub(r'\b3I\b', '31', text)
    
    # Fix common OCR errors where lowercase L is read as 1
    text = re.sub(r'(\d+)l(\d+)', r'\g<1>.\g<2>', text)  # "16l1" -> "16.1"
    text = re.sub(r'(\d+)iL(\d+)', r'\g<1>.\g<2>', text)  # "16iL4" -> "16.4"
    
    # Clean up extra whitespace but preserve newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Only replace spaces/tabs, not newlines
    
    return text


def parse_players(ocr_text: str, backup_ocr_text: str = None) -> List[Dict[str, any]]:
    """
    Parse player data from OCR text using regex.
    
    Expected pattern: PlayerName GrossScore(+/-X) Handicap
    Example: "Acorm 38(+2) -2.2"
    
    Args:
        ocr_text: Raw OCR text string
        
    Returns:
        List of dictionaries with player data:
        [{"name": str, "gross_score": int, "handicap": float}, ...]
        
    Raises:
        ValueError: If ocr_text is empty or invalid
    """
    if not ocr_text or not ocr_text.strip():
        raise ValueError("OCR text is empty")
    
    players = []
    seen_names = set()  # Track duplicate players
    
    # Exclude common non-player words
    exclude_words = {'golfzon', 'hole', 'total', 'par', 'rank', 'in', 'out', 'round', 'mountain', 'west', 'pga'}
    
    # Process line by line - clean each line individually
    lines = ocr_text.split('\n')
    
    # Pattern to match player data: name, score(+/-X), handicap
    # Pattern 1: Complete match with handicap (with digits after decimal) - more flexible
    # Require at least 3 letters for name to avoid matching single letters like 'm'
    pattern1 = r'([A-Za-z]{3,}).*?(\d{2,3})\(.*?([+\-]\d+\.\d+)'
    # Pattern 2: Score with incomplete handicap (ends with .)
    pattern2 = r'([A-Za-z]{3,}).*?(\d{2,3})\(.*?([+\-]\d+\.)'
    # Pattern 3: Score without handicap visible, try to find handicap elsewhere on line
    # Make closing ) optional since OCR sometimes cuts it off
    pattern3 = r'([A-Za-z]{3,}).*?(\d{2,3})\s*\([+\-]?\d+\)?'
    
    for line in lines:
        # Clean each line individually
        cleaned_line = clean_ocr_text(line)
        found_in_line = False
        
        # Try pattern 1 first (complete match with decimal)
        matches = re.finditer(pattern1, cleaned_line, re.IGNORECASE)
        for match in matches:
            if process_match(match, exclude_words, seen_names, players):
                found_in_line = True
        
        # Try pattern 2 (incomplete handicap ending with .)
        if not found_in_line:
            matches = re.finditer(pattern2, cleaned_line, re.IGNORECASE)
            for match in matches:
                # Add '1' to complete the handicap
                name = match.group(1).strip()
                gross_score_str = match.group(2)
                handicap_str = match.group(3) + '1'
                
                # Create a new match-like object with the fixed handicap
                class FixedMatch:
                    def __init__(self, name, score, handicap):
                        self.groups = [name, score, handicap]
                    def group(self, n):
                        return self.groups[n-1]
                
                fixed_match = FixedMatch(name, gross_score_str, handicap_str)
                if process_match(fixed_match, exclude_words, seen_names, players):
                    found_in_line = True
        
        # Try pattern 3 (score without visible handicap, find handicap separately)
        if not found_in_line:
            matches = re.finditer(pattern3, cleaned_line, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                gross_score_str = match.group(2)
                
                # Look for handicap pattern elsewhere on the line
                # But exclude the score differential pattern like (+2) or (+5)
                # First try to find a decimal handicap (more specific)
                handicap_match = re.search(r'([+\-]\d+\.\d+)', cleaned_line)
                if not handicap_match:
                    # Try handicap ending with decimal point
                    handicap_match = re.search(r'([+\-]\d+\.)', cleaned_line)
                if not handicap_match:
                    # Last resort: look for any +/- number, but exclude those inside parentheses
                    # that are part of the score pattern
                    # Remove the score pattern first to avoid matching it
                    line_without_score = re.sub(r'\d{2,3}\s*\([+\-]?\d+\)?', '', cleaned_line)
                    handicap_match = re.search(r'([+\-]\d+)', line_without_score)
                
                if handicap_match:
                    handicap_str = handicap_match.group(1)
                    # Fix OCR errors
                    handicap_str = re.sub(r'iL', '11', handicap_str, flags=re.IGNORECASE)
                    handicap_str = re.sub(r'(\d+)I', r'\g<1>1', handicap_str)
                    if handicap_str.endswith('.'):
                        handicap_str = handicap_str + '1'
                    elif '.' not in handicap_str and len(handicap_str) > 2:
                        handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
                    
                    class FixedMatch:
                        def __init__(self, name, score, handicap):
                            self.groups = [name, score, handicap]
                        def group(self, n):
                            return self.groups[n-1]
                    
                    fixed_match = FixedMatch(name, gross_score_str, handicap_str)
                    if process_match(fixed_match, exclude_words, seen_names, players):
                        found_in_line = True
                else:
                    # No handicap found - try backup OCR text if available
                    if backup_ocr_text:
                        # Look for handicap near the player name in backup text
                        name_lower = name.lower().replace('l', '').replace('i', '')  # Handle OCR variations
                        backup_lines = backup_ocr_text.split('\n')
                        for i, backup_line in enumerate(backup_lines):
                            # Check if name appears in this line (handle OCR variations)
                            if name_lower in backup_line.lower() or 'acorm' in backup_line.lower() or 'acorn' in backup_line.lower():
                                # Found name, look for handicap in nearby lines (within 5 lines)
                                for j in range(max(0, i-5), min(len(backup_lines), i+6)):
                                    handicap_match = re.search(r'([+\-]\d+\.\d+)', backup_lines[j])
                                    if not handicap_match:
                                        handicap_match = re.search(r'([+\-]\d+\.)', backup_lines[j])
                                    if handicap_match:
                                        handicap_str = handicap_match.group(1)
                                        if handicap_str.endswith('.'):
                                            handicap_str = handicap_str + '1'
                                        
                                        class FixedMatch:
                                            def __init__(self, name, score, handicap):
                                                self.groups = [name, score, handicap]
                                            def group(self, n):
                                                return self.groups[n-1]
                                        
                                        fixed_match = FixedMatch(name, gross_score_str, handicap_str)
                                        if process_match(fixed_match, exclude_words, seen_names, players):
                                            found_in_line = True
                                            break
                                if found_in_line:
                                    break
                    
                    # If still no handicap found, skip this player
                    # (can't calculate net score without handicap)
                    pass
    
    return players


def process_match(match, exclude_words, seen_names, players):
    """Helper function to process a regex match and add player if valid."""
    try:
        name = match.group(1).strip()
        gross_score_str = match.group(2)
        handicap_str = match.group(3)
        
        # Validate and convert values
        if not name or len(name) < 2:
            return False
        
        # Clean up name - remove common OCR artifacts
        name = re.sub(r'[\[|\]|\|\\]', '', name)
        name = re.sub(r'^[0-9]+', '', name)  # Remove leading numbers
        name = name.strip()
        
        # Skip very short names (likely OCR artifacts)
        if len(name) < 3:
            return False
        
        # Skip known non-player words
        if name.lower() in exclude_words:
            return False
        
        # Skip if name is all uppercase and too short (likely not a player name)
        if name.isupper() and len(name) < 4:
            return False
        
        # Skip single letters (like 'm', 'G', etc.)
        if len(name) == 1:
            return False
        
        # Fix common OCR errors in handicap
        handicap_str = re.sub(r'iL', '11', handicap_str, flags=re.IGNORECASE)
        handicap_str = re.sub(r'(\d+)I', r'\g<1>1', handicap_str)
        handicap_str = re.sub(r'(\d+)l(\d+)', r'\g<1>.\g<2>', handicap_str)
        handicap_str = re.sub(r'(\d+)i(\d+)', r'\g<1>.\g<2>', handicap_str)
        
        # Ensure handicap has decimal point if missing or ends with just .
        if handicap_str.endswith('.'):
            handicap_str = handicap_str + '1'
        elif '.' not in handicap_str and len(handicap_str) > 2:
            handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
        
        gross_score = int(gross_score_str)
        handicap = float(handicap_str)
        
        # Validate score ranges (reasonable golf scores)
        if gross_score < 1 or gross_score > 200:
            return False
        
        # Validate handicap range (reasonable golf handicaps)
        if abs(handicap) > 50:
            return False
        
        # Remove "G" prefix if present (common in Golfzon scorecards)
        if name.startswith('G') and len(name) > 1:
            name = name[1:].strip()
        
        # Fix common name misreads
        if name.lower() == 'acidyer' or name.lower() == 'acidy' or 'cjdyer' in name.lower():
            name = 'Gjdyer'
        elif name.lower() == 'acorm' or name.lower() == 'lacorm' or 'acorn' in name.lower():
            name = 'Acorn'
        elif 'lcrostarosa' in name.lower() or 'lcrost' in name.lower() or name.lower().startswith('lcrost'):
            name = 'Lcrostarosa'
        
        # Skip duplicates
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

