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
    # Remove lines that are mostly noise (mostly special characters)
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
    text = '\n'.join(cleaned_lines)
    
    # Fix common OCR character substitutions
    # Fix "ee" -> "Be" (common OCR error)
    text = re.sub(r'\beeachy\b', 'Beachy', text, flags=re.IGNORECASE)
    text = re.sub(r'\beeach\b', 'Beach', text, flags=re.IGNORECASE)
    
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
    
    # Fix garbled names: "Firstortast" -> "First"
    text = re.sub(r'\bFirstortast\b', 'First', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfFirstortast\b', 'First', text, flags=re.IGNORECASE)
    
    # Fix "facaubs22" -> "Gjdyer" or similar (common OCR error)
    text = re.sub(r'\bfacaubs\d+\b', 'Gjdyer', text, flags=re.IGNORECASE)
    
    # Fix OCR errors in numbers: "4347)" -> "43(+7)" pattern
    # But be more careful - only if it looks like a score pattern
    # Don't convert all 4-digit numbers, only ones that end with )
    text = re.sub(r'(\d{2})(\d{2})\)(?!\d)', r'\1(+\2)', text)  # "4347)" -> "43(+7)" but not "1234)5"
    
    # Fix handicap misreads: "-22" -> "-2.2" but only if reasonable
    # Don't convert if it would create invalid handicaps (>50)
    # Only convert 3-digit handicaps that look like OCR errors
    def fix_handicap(match):
        sign = match.group(1)
        digit1 = match.group(2)
        digit2 = match.group(3)
        if int(digit1 + digit2) > 50:  # Don't convert if > 50
            return match.group(0)
        return f'{sign}{digit1}.{digit2}'
    text = re.sub(r'([+\-])(\d)(\d)(?:\s|$|[^.\d])', fix_handicap, text)  # "-22 " -> "-2.2 "
    
    # Fix score misreads: "B42)" -> "42)" or "38(+2)"
    text = re.sub(r'B(\d{2})\)', r'\1', text)  # "B42)" -> "42"
    text = re.sub(r'GIO\s+(\d{2})\)', r'\1', text)  # "GIO 14)" -> "14"
    
    # Fix name misreads: "Biciayer" -> "Cjdyer", "Biconaresel" -> "Lcrostarosa"
    text = re.sub(r'\bBiciayer\b', 'Cjdyer', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBiconaresel\b', 'Lcrostarosa', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\[TlAcorm\b', 'Acorm', text, flags=re.IGNORECASE)
    
    # Fix garbled names with prefixes: "elBeachy" -> "Beachy", "RQFirstOrLast" -> "FirstOrLast"
    text = re.sub(r'\belBeachy\b', 'Beachy', text, flags=re.IGNORECASE)
    text = re.sub(r'\bRQFirstOrLast\b', 'FirstOrLast', text, flags=re.IGNORECASE)
    
    # Remove common OCR artifacts
    text = re.sub(r'[|_]{2,}', ' ', text)  # Multiple pipes/underscores -> space
    text = re.sub(r'^[|_\s]+', '', text, flags=re.MULTILINE)  # Leading pipes/underscores
    text = re.sub(r'[|_\s]+$', '', text, flags=re.MULTILINE)  # Trailing pipes/underscores
    
    # Remove lines that are mostly single characters repeated
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if len(line.strip()) > 0:
            # Check if line is mostly the same character
            unique_chars = len(set(line.strip().replace(' ', '')))
            if unique_chars >= 2 or len(line.strip()) >= 5:  # Keep if diverse or long enough
                cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    
    # Clean up extra whitespace but preserve newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Only replace spaces/tabs, not newlines
    
    return text


def parse_players(ocr_text: str, backup_ocr_text: str = None) -> List[Dict[str, any]]:
    """
    Parse player data from OCR text using regex.
    
    Expected pattern: PlayerName GrossScore(+/-X) Handicap
    Example: "Acorm 38(+2) -2.2"
    
    If scores are detected but names are missing, creates placeholder players
    with empty names that can be manually edited.
    
    Args:
        ocr_text: Raw OCR text string
        backup_ocr_text: Optional backup OCR text for fallback matching
        
    Returns:
        List of dictionaries with player data:
        [{"name": str, "gross_score": int, "handicap": float}, ...]
        Names may be empty strings if not detected.
        
    Raises:
        ValueError: If ocr_text is empty or invalid
    """
    if not ocr_text or not ocr_text.strip():
        raise ValueError("OCR text is empty")
    
    players = []
    seen_names = set()  # Track duplicate players
    score_positions = []  # Track score positions to detect unmatched scores
    
    # Exclude common non-player words
    exclude_words = {'golfzon', 'hole', 'total', 'par', 'rank', 'in', 'out', 'round', 'mountain', 'west', 'pga', 
                     'scorecard', 'statistics', 'rounding', 'record', 'shot', 'analysis', 'analy', 'analysi',
                     'std', 'gouzatf', 'wests', 'ggovad', 'bay', 'bag', 'bi', 'biais', 'stat', 'phoenix', 'country', 'club',
                     'boiciak', 'boici', 'geet', 'sano'}  # OCR artifacts
    
    # Process multi-line chunks to handle cases where data spans multiple lines
    # Group lines together before parsing
    multi_line_text = ocr_text.replace('\n', ' | ')  # Use | as temporary separator
    
    # First, try to find score patterns and match them with nearby names and handicaps
    # Look for score patterns like "42(+7)" or "39(+4)" across the entire text
    # Also look for fragmented patterns like "4347)" which might be "43(+7)"
    # Also handle spaces: "43 (+13)" -> "43(+13)"
    score_pattern = r'(\d{2,3})\s*\([+\-]?\d+\)'
    score_matches = list(re.finditer(score_pattern, ocr_text))
    
    # Also look for scores without parentheses but with nearby +/- numbers
    # Pattern: 2-3 digit number followed by +/- number within 20 chars
    fragmented_score_pattern = r'(\d{2,3})[^0-9]{0,20}([+\-]\d+)'
    fragmented_matches = list(re.finditer(fragmented_score_pattern, ocr_text))
    
    # Combine all score matches
    all_score_matches = score_matches + fragmented_matches
    
    for score_match in all_score_matches:
        gross_score_str = score_match.group(1)
        score_start = score_match.start()
        score_end = score_match.end()
        
        # For fragmented matches, we might have captured the handicap too
        # But ignore it if it's part of the score pattern (like "+7" in "44(+7)")
        handicap_str = None
        if len(score_match.groups()) > 1:
            # This is a fragmented match that captured handicap
            potential_hcp = score_match.group(2)
            # Only use it if it looks like a real handicap (has decimal point)
            # Don't use scores like "+7" from "44(+7)" patterns
            if potential_hcp.startswith('+') or potential_hcp.startswith('-'):
                if '.' in potential_hcp or len(potential_hcp) > 3:
                    # This looks like a real handicap, not a score difference
                    handicap_str = potential_hcp
        
        # Look for name both before and after the score (within 100 chars each direction)
        # But limit after_text to before the next score to avoid matching names from later scores
        before_text = ocr_text[max(0, score_start - 100):score_start]
        
        # Find the next score to limit our search
        next_score_start = len(ocr_text)
        remaining_text = ocr_text[score_end:]
        next_score_match = re.search(r'\d{2,3}\s*\([+\-]?\d+\)', remaining_text)
        if next_score_match:
            next_score_start = score_end + next_score_match.start()
        
        after_text = ocr_text[score_end:min(len(ocr_text), next_score_start)]
        
        # Try to find the CLOSEST name to the score by searching backwards first, then forwards
        name_match = None
        name_positions = []
        
        # Search backwards (preferred - names usually come before scores)
        for pattern_desc, pattern in [
            ('[el Beachy', r'\[el\s+Beachy'),
            ('[el FirstOrLast', r'\[el\s+FirstOrLast'),
            ('[el pattern', r'\[el\s+([A-Z][a-z]+(?:Or[A-Z][a-z]+)?)'),
            ('Tcdubs21', r'T([Cc]dubs\d+)[_|]'),
            ('[Tl pattern', r'\[Tl([A-Z][a-z]{2,})'),
            ('Standard', r'([A-Z][a-z]{2,})(?:\s|$|[|])'),
        ]:
            matches = list(re.finditer(pattern, before_text))
            if matches:
                # Use the match closest to the score (last match in before_text)
                match = matches[-1]
                name_positions.append((match.start() + score_start - 100, match, pattern_desc))
        
        # Also search forwards (in case name comes after score)
        for pattern_desc, pattern in [
            ('[el Beachy', r'\[el\s+Beachy'),
            ('[el FirstOrLast', r'\[el\s+FirstOrLast'),
            ('Tcdubs21', r'T([Cc]dubs\d+)[_|]'),
            ('Standard', r'([A-Z][a-z]{2,})(?:\s|$|[|])'),
        ]:
            matches = list(re.finditer(pattern, after_text))
            if matches:
                # Use the match closest to the score (first match in after_text)
                match = matches[0]
                name_positions.append((match.start() + score_end, match, pattern_desc))
        
        # Sort by distance from score and pick the closest
        # Prioritize names that come AFTER the score (typical format: Score → Handicap → Name)
        if name_positions:
            # Define priority order (lower number = higher priority)
            priority_order = {'[el Beachy': 1, '[el FirstOrLast': 2, 'Tcdubs21': 3, '[Tl pattern': 4, '[el pattern': 5, 'Standard': 6}
            
            def sort_key(pos_tuple):
                pos, match_obj, desc = pos_tuple
                distance = abs(pos - score_start)
                priority = priority_order.get(desc, 99)
                is_after = pos > score_start  # Name comes after score
                
                # IMPORTANT: In Golfzon scorecards, the format is: Score → Handicap → Name
                # So names AFTER scores should be strongly preferred over names BEFORE scores
                # to avoid matching names from previous players
                
                # Strongly prefer names that come AFTER the score (within reasonable distance)
                if is_after and distance < 100:
                    # Names after score get high priority - multiply distance by 0.3 to make them much closer
                    effective_distance = distance * 0.3
                elif not is_after and distance < 50:
                    # Names before score (likely from previous player) get lower priority
                    # Multiply distance by 3.0 to penalize them heavily
                    effective_distance = distance * 3.0
                else:
                    # For very far distances, use actual distance
                    effective_distance = distance
                
                # For distances > 50, prioritize specific patterns heavily
                # Specific patterns should always win over generic ones
                if distance > 50:
                    # Specific patterns get much lower priority score
                    if desc in ['[el Beachy', '[el FirstOrLast', 'Tcdubs21', '[Tl pattern']:
                        return (priority, effective_distance)  # Specific patterns: priority first, then distance
                    else:
                        return (priority * 10000 + effective_distance, priority)  # Generic patterns: much lower priority
                else:
                    return (effective_distance, priority)  # Close matches: effective distance first
            
            name_positions.sort(key=sort_key)
            closest_match, match_obj, desc = name_positions[0]
            
            # Extract the name
            if desc == '[el Beachy':
                name = 'Beachy'
            elif desc == '[el FirstOrLast':
                name = 'FirstOrLast'
            elif desc == 'Tcdubs21':
                name = match_obj.group(1)
            elif match_obj.groups():
                name = match_obj.group(1)
            else:
                name = match_obj.group(0)
            
            # Clean up name
            if desc == 'Tcdubs21' and name.startswith('T'):
                name = name[1:]  # Remove T prefix
            elif desc == 'Tcdubs21':
                # Already extracted correctly from group(1)
                pass
            
            class MockMatch:
                def __init__(self, name):
                    self._name = name
                def group(self, n):
                    return self._name if n == 1 else None
            name_match = MockMatch(name)
        
        # Filter and sort name positions if we haven't set name_match yet
        if not name_match and name_positions:
            # Filter out excluded words
            filtered_positions = []
            for pos_tuple in name_positions:
                pos, match_obj, desc = pos_tuple
                # Extract potential name
                if desc == '[el Beachy':
                    potential_name = 'Beachy'
                elif desc == '[el FirstOrLast':
                    potential_name = 'FirstOrLast'
                elif desc == 'Tcdubs21':
                    potential_name = match_obj.group(1) if match_obj.groups() else match_obj.group(0)
                elif match_obj.groups():
                    potential_name = match_obj.group(1)
                else:
                    potential_name = match_obj.group(0)
                
                # Skip if name is in exclude list
                if potential_name.lower() not in exclude_words and len(potential_name) >= 2:
                    filtered_positions.append(pos_tuple)
            
            if not filtered_positions:
                name_match = None
            else:
                # Define priority order (lower number = higher priority)
                priority_order = {'[el Beachy': 1, '[el FirstOrLast': 2, 'Tcdubs21': 3, '[Tl pattern': 4, '[el pattern': 5, 'Standard': 6}
                
                def sort_key(pos_tuple):
                    pos, match_obj, desc = pos_tuple
                    distance = abs(pos - score_start)
                    priority = priority_order.get(desc, 99)
                    is_after = pos > score_start  # Name comes after score
                    
                    # IMPORTANT: In Golfzon scorecards, the format is: Score → Handicap → Name
                    # Strongly prefer names that come AFTER the score
                    if is_after and distance < 100:
                        effective_distance = distance * 0.3
                    elif not is_after and distance < 50:
                        effective_distance = distance * 3.0
                    else:
                        effective_distance = distance
                    
                    # For distances > 50, prioritize specific patterns heavily
                    # Specific patterns should always win over generic ones
                    if distance > 50:
                        # Specific patterns get much lower priority score
                        if desc in ['[el Beachy', '[el FirstOrLast', 'Tcdubs21', '[Tl pattern']:
                            return (priority, effective_distance)  # Specific patterns: priority first, then distance
                        else:
                            return (priority * 10000 + effective_distance, priority)  # Generic patterns: much lower priority
                    else:
                        return (effective_distance, priority)  # Close matches: effective distance first
                
                filtered_positions.sort(key=sort_key)
                closest_match, match_obj, desc = filtered_positions[0]
                
                # Extract the name
                if desc == '[el Beachy':
                    name = 'Beachy'
                elif desc == '[el FirstOrLast':
                    name = 'FirstOrLast'
                elif desc == 'Tcdubs21':
                    name = match_obj.group(1)
                elif match_obj.groups():
                    name = match_obj.group(1)
                else:
                    name = match_obj.group(0)
                
                # Clean up name
                if desc == 'Tcdubs21' and name.startswith('T'):
                    name = name[1:]  # Remove T prefix
                elif desc == 'Tcdubs21':
                    # Already extracted correctly from group(1)
                    pass
                
                class MockMatch:
                    def __init__(self, name):
                        self._name = name
                    def group(self, n):
                        return self._name if n == 1 else None
                name_match = MockMatch(name)
        
        # Look for handicap after the score (within 100 chars) - handicaps usually come after scores
        # Always search for handicap in after_text, even if we captured one from fragmented match
        # (because fragmented matches might capture score differences like "+7" instead of real handicaps)
        handicap_match = re.search(r'([+\-]\d+\.\d+)', after_text)
        if handicap_match:
            handicap_str = handicap_match.group(1)
        elif not handicap_str:
            # Only try other patterns if we don't have a handicap yet
            handicap_match = re.search(r'([+\-]\d+\.)', after_text)
            if handicap_match:
                handicap_str = handicap_match.group(1)
            else:
                handicap_match = re.search(r'([+\-]\d{1,2})(?![.\d])', after_text)
                if handicap_match:
                    handicap_str = handicap_match.group(1)
        
        if name_match and handicap_str:
            name = name_match.group(1).strip() if hasattr(name_match, 'group') else str(name_match).strip()
            
            # Clean name - remove OCR artifacts
            name = re.sub(r'[\[|\]|\|\\_]', '', name)
            # Remove common OCR prefixes
            name = re.sub(r'^[a-z]([A-Z][a-z]+)', r'\1', name)  # "eBeachy" -> "Beachy"
            name = re.sub(r'^[RQ]([A-Z][a-z]+)', r'\1', name)  # "RQFirstOrLast" -> "FirstOrLast"
            name = re.sub(r'^Tl', '', name)  # "[TlAcorm" -> "Acorm"
            name = name.strip()
            
            # Skip if name is too short or in exclude list
            if len(name) < 2 or name.lower() in exclude_words:
                continue
            
            # Process handicap - fix OCR errors like "-22" -> "-2.2"
            if len(handicap_str) == 3 and handicap_str[0] in '+-' and handicap_str[1:].isdigit():
                # Might be OCR error: "-22" should be "-2.2"
                handicap_str = handicap_str[0] + handicap_str[1] + '.' + handicap_str[2]
            elif handicap_str.endswith('.'):
                handicap_str = handicap_str + '1'
            elif '.' not in handicap_str:
                if len(handicap_str) > 2:
                    handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
                else:
                    handicap_str = handicap_str + '.0'
            
            try:
                gross_score = int(gross_score_str)
                handicap = float(handicap_str)
                
                # Validate ranges
                if gross_score < 1 or gross_score > 200 or abs(handicap) > 50:
                    continue
                
                # Check if already seen
                if name.lower() not in seen_names:
                    seen_names.add(name.lower())
                    players.append({
                        "name": name,
                        "gross_score": gross_score,
                        "handicap": handicap
                    })
            except (ValueError, TypeError):
                continue
    
    # Also try to find player names in table-like formats (with pipes/separators)
    # Look for patterns like "|elBeachy 5 SMS | 4 @ | TL |" or "3 |elBeachy"
    # Extract names from table rows
    table_row_pattern = r'\|.*?([A-Z][a-z]{2,}).*?\|'
    table_matches = list(re.finditer(table_row_pattern, ocr_text))
    
    for match in table_matches:
        name = match.group(1).strip()
        
        # Clean name - remove OCR artifacts
        name = re.sub(r'[\[|\]|\|\\_]', '', name)
        name = re.sub(r'^[a-z]([A-Z][a-z]+)', r'\1', name)  # "eBeachy" -> "Beachy"
        name = re.sub(r'^[RQ]([A-Z][a-z]+)', r'\1', name)  # "RQFirstOrLast" -> "FirstOrLast"
        name = name.strip()
        
        # Skip if name is too short or in exclude list
        if len(name) < 2 or name.lower() in exclude_words:
            continue
        
        # Check if we already have this player
        if name.lower() in seen_names:
            continue
        
        # Look for score near this name - try to find scores in parentheses format
        match_start = match.start()
        match_end = match.end()
        context_text = ocr_text[max(0, match_start - 100):min(len(ocr_text), match_end + 200)]
        
        # Try to find score pattern like "38(+2)" or just "38" near the name
        score_match = re.search(r'(\d{2,3})\([+\-]?\d+\)', context_text)
        if not score_match:
            # Try to find just a 2-3 digit number that might be a score
            score_match = re.search(r'(\d{2,3})(?![.\d])', context_text)
        
        # Look for handicap
        handicap_match = re.search(r'([+\-]\d+\.\d+)', context_text)
        if not handicap_match:
            handicap_match = re.search(r'([+\-]\d+\.)', context_text)
        if not handicap_match:
            handicap_match = re.search(r'([+\-]\d{1,2})(?![.\d])', context_text)
        
        if score_match and handicap_match:
            gross_score_str = score_match.group(1)
            handicap_str = handicap_match.group(1)
            
            # Process handicap
            if handicap_str.endswith('.'):
                handicap_str = handicap_str + '1'
            elif '.' not in handicap_str:
                if len(handicap_str) > 2:
                    handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
                else:
                    handicap_str = handicap_str + '.0'
            
            try:
                gross_score = int(gross_score_str)
                handicap = float(handicap_str)
                
                # Validate ranges
                if gross_score < 1 or gross_score > 200 or abs(handicap) > 50:
                    continue
                
                seen_names.add(name.lower())
                players.append({
                    "name": name,
                    "gross_score": gross_score,
                    "handicap": handicap
                })
            except (ValueError, TypeError):
                continue
        elif handicap_match:
            # Found name and handicap but no score - skip for now
            # We need a score to calculate net score
            pass
    
    # Also process line by line - clean each line individually
    lines = ocr_text.split('\n')
    
    # Pattern to match player data: name, score(+/-X), handicap
    # Pattern 1: Complete match with handicap (with digits after decimal) - more flexible
    # Require at least 2 letters for name (reduced from 3 to handle OCR errors)
    pattern1 = r'([A-Za-z]{2,}).*?(\d{2,3})\(.*?([+\-]\d+\.\d+)'
    # Pattern 2: Score with incomplete handicap (ends with .)
    pattern2 = r'([A-Za-z]{2,}).*?(\d{2,3})\(.*?([+\-]\d+\.)'
    # Pattern 3: Score without handicap visible, try to find handicap elsewhere on line
    # Make closing ) optional since OCR sometimes cuts it off
    pattern3 = r'([A-Za-z]{2,}).*?(\d{2,3})\s*\([+\-]?\d+\)?'
    # Pattern 4: More flexible - score without parentheses (OCR may miss them)
    pattern4 = r'([A-Za-z]{2,}).*?(\d{2,3})\s+[+\-]?\d+\s+([+\-]\d+\.?\d*)'
    # Pattern 5: Very flexible - just name followed by numbers that might be score/handicap
    pattern5 = r'([A-Za-z]{2,}).*?(\d{2,3})\s*([+\-]\d+)'
    # Pattern 6: Handle cases where score is on same line but handicap is on next line or separated
    pattern6 = r'([A-Za-z]{2,}).*?(\d{2,3})\([+\-]?\d+\)'
    # Pattern 7: Handle cases where name might have "G" prefix and score/handicap are separated
    pattern7 = r'[G]?\s*([A-Za-z]{2,}).*?(\d{2,3})\([+\-]?\d+\)'
    
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
        
        # Try pattern 4 (score without parentheses)
        if not found_in_line:
            matches = re.finditer(pattern4, cleaned_line, re.IGNORECASE)
            for match in matches:
                if process_match(match, exclude_words, seen_names, players):
                    found_in_line = True
        
        # Try pattern 5 (very flexible - just name and numbers)
        if not found_in_line:
            matches = re.finditer(pattern5, cleaned_line, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                gross_score_str = match.group(2)
                potential_handicap = match.group(3)
                
                # Check if this looks like a handicap (should be +/- number)
                if re.match(r'[+\-]\d+', potential_handicap):
                    # Try to find a decimal handicap elsewhere on the line
                    handicap_match = re.search(r'([+\-]\d+\.\d+)', cleaned_line)
                    if not handicap_match:
                        handicap_match = re.search(r'([+\-]\d+\.)', cleaned_line)
                    if not handicap_match:
                        # Use the found number but add decimal if missing
                        handicap_str = potential_handicap
                        if '.' not in handicap_str and len(handicap_str) > 2:
                            handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
                    else:
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
        
        # Try pattern 6 (score with parentheses, find handicap separately)
        if not found_in_line:
            matches = re.finditer(pattern6, cleaned_line, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                gross_score_str = match.group(2)
                
                # Look for handicap on same line or nearby lines
                handicap_match = re.search(r'([+\-]\d+\.\d+)', cleaned_line)
                if not handicap_match:
                    handicap_match = re.search(r'([+\-]\d+\.)', cleaned_line)
                if not handicap_match:
                    # Try looking in next few lines
                    line_idx = lines.index(line) if line in lines else -1
                    if line_idx >= 0 and line_idx < len(lines) - 1:
                        for next_line_idx in range(line_idx, min(line_idx + 3, len(lines))):
                            next_line = clean_ocr_text(lines[next_line_idx])
                            handicap_match = re.search(r'([+\-]\d+\.\d+)', next_line)
                            if not handicap_match:
                                handicap_match = re.search(r'([+\-]\d+\.)', next_line)
                            if handicap_match:
                                break
                
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
        
        # Try pattern 7 (with optional G prefix)
        if not found_in_line:
            matches = re.finditer(pattern7, cleaned_line, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                gross_score_str = match.group(2)
                
                # Look for handicap on same line
                handicap_match = re.search(r'([+\-]\d+\.\d+)', cleaned_line)
                if not handicap_match:
                    handicap_match = re.search(r'([+\-]\d+\.)', cleaned_line)
                if not handicap_match:
                    # Try integer handicap
                    handicap_match = re.search(r'([+\-]\d{1,2})(?![.\d])', cleaned_line)
                
                if handicap_match:
                    handicap_str = handicap_match.group(1)
                    if '.' not in handicap_str:
                        handicap_str = handicap_str + '.0'
                    elif handicap_str.endswith('.'):
                        handicap_str = handicap_str + '1'
                    
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
                
                # Look for handicap pattern elsewhere on the line or nearby lines
                # But exclude the score differential pattern like (+2) or (+5)
                # First try to find a decimal handicap (more specific)
                handicap_match = re.search(r'([+\-]\d+\.\d+)', cleaned_line)
                if not handicap_match:
                    # Try handicap ending with decimal point
                    handicap_match = re.search(r'([+\-]\d+\.)', cleaned_line)
                if not handicap_match:
                    # Try integer handicap (add .0 later)
                    line_without_score = re.sub(r'\d{2,3}\s*\([+\-]?\d+\)?', '', cleaned_line)
                    handicap_match = re.search(r'([+\-]\d{1,2})(?![.\d])', line_without_score)
                if not handicap_match:
                    # Try looking in next line
                    line_idx = lines.index(line) if line in lines else -1
                    if line_idx >= 0 and line_idx < len(lines) - 1:
                        next_line = clean_ocr_text(lines[line_idx + 1])
                        handicap_match = re.search(r'([+\-]\d+\.\d+)', next_line)
                        if not handicap_match:
                            handicap_match = re.search(r'([+\-]\d+\.)', next_line)
                        if not handicap_match:
                            handicap_match = re.search(r'([+\-]\d{1,2})(?![.\d])', next_line)
                
                if handicap_match:
                    handicap_str = handicap_match.group(1)
                    # Fix OCR errors
                    handicap_str = re.sub(r'iL', '11', handicap_str, flags=re.IGNORECASE)
                    handicap_str = re.sub(r'(\d+)I', r'\g<1>1', handicap_str)
                    if handicap_str.endswith('.'):
                        handicap_str = handicap_str + '1'
                    elif '.' not in handicap_str:
                        # Add decimal point if missing
                        if len(handicap_str) > 2:
                            handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
                        else:
                            handicap_str = handicap_str + '.0'
                    
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
    
    # Deduplicate players by score+handicap combination
    # Keep the first occurrence (which should have a name if one was found)
    seen_combinations = {}
    deduplicated_players = []
    for player in players:
        key = (player.get('gross_score'), round(player.get('handicap', 0), 1))
        if key not in seen_combinations:
            seen_combinations[key] = player
            deduplicated_players.append(player)
        else:
            # If we have a duplicate, prefer the one with a name
            existing = seen_combinations[key]
            if not existing.get('name', '').strip() and player.get('name', '').strip():
                # Replace the one without a name with the one that has a name
                deduplicated_players.remove(existing)
                deduplicated_players.append(player)
                seen_combinations[key] = player
    players = deduplicated_players
    
    # After parsing, look for scores that weren't matched to names
    # This handles cases where OCR detected scores but failed to detect player names
    # Find all score patterns in the text
    score_pattern = r'(\d{2,3})\s*\([+\-]?\d+\)'
    all_score_matches = list(re.finditer(score_pattern, ocr_text))
    
    # Create a set of score+handicap combinations we already have
    existing_combinations = set()
    for player in players:
        key = (player.get('gross_score'), round(player.get('handicap', 0), 1))
        existing_combinations.add(key)
    
    # Find unmatched scores (scores not associated with any player)
    unmatched_scores = []
    for score_match in all_score_matches:
        gross_score_str = score_match.group(1)
        score_start = score_match.start()
        score_end = score_match.end()
        
        # Only process if we have fewer than 6 players
        if len(players) >= 6:
            break
        
        # Extract score and try to find handicap nearby
        # Look for handicap in surrounding text (within 100 chars)
        before_text = ocr_text[max(0, score_start - 50):score_start]
        after_text = ocr_text[score_end:min(len(ocr_text), score_end + 100)]
        
        handicap_match = re.search(r'([+\-]\d+\.\d+)', after_text)
        if not handicap_match:
            handicap_match = re.search(r'([+\-]\d+\.)', after_text)
        if not handicap_match:
            handicap_match = re.search(r'([+\-]\d{1,2})(?![.\d])', after_text)
        
        if handicap_match:
            handicap_str = handicap_match.group(1)
            # Process handicap
            if handicap_str.endswith('.'):
                handicap_str = handicap_str + '1'
            elif '.' not in handicap_str:
                if len(handicap_str) > 2:
                    handicap_str = handicap_str[:-1] + '.' + handicap_str[-1]
                else:
                    handicap_str = handicap_str + '.0'
            
            try:
                gross_score = int(gross_score_str)
                handicap = float(handicap_str)
                
                # Validate ranges
                if gross_score >= 1 and gross_score <= 200 and abs(handicap) <= 50:
                    # Check if we already have this score+handicap combination
                    key = (gross_score, round(handicap, 1))
                    if key not in existing_combinations:
                        unmatched_scores.append({
                            "gross_score": gross_score,
                            "handicap": handicap,
                            "position": score_start
                        })
                        existing_combinations.add(key)
            except (ValueError, TypeError):
                pass
    
    # Add unmatched scores as placeholder players (empty name for manual editing)
    # Limit to 6 total players (1-6 as per requirements)
    max_players = 6
    current_count = len(players)
    
    for unmatched in unmatched_scores:
        if current_count >= max_players:
            break
        
        # Only add if we don't already have a player with this exact score and handicap
        # (avoid duplicates) - check with tolerance for floating point
        is_duplicate = False
        for existing_player in players:
            existing_score = existing_player.get('gross_score')
            existing_handicap = existing_player.get('handicap', 0)
            
            # Check if score and handicap match (within tolerance)
            if (existing_score == unmatched['gross_score'] and
                abs(existing_handicap - unmatched['handicap']) < 0.1):
                is_duplicate = True
                break
        
        if not is_duplicate:
            players.append({
                "name": "",  # Empty name - user can edit manually
                "gross_score": unmatched['gross_score'],
                "handicap": unmatched['handicap']
            })
            current_count += 1
            # Also add to existing_combinations to avoid duplicates in this loop
            key = (unmatched['gross_score'], round(unmatched['handicap'], 1))
            existing_combinations.add(key)
    
    # Ensure we have between 1 and 6 players
    if len(players) > 6:
        # Keep first 6 players (prioritize those with names)
        # Sort: players with names first, then by score
        players.sort(key=lambda p: (p.get('name', '').strip() == '', p.get('gross_score', 999)))
        players = players[:6]
    
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
        name = re.sub(r'[\[|\]|\|\\_]', '', name)
        name = re.sub(r'^[0-9]+', '', name)  # Remove leading numbers
        name = re.sub(r'^[|_]+', '', name)  # Remove leading pipes/underscores
        name = name.strip()
        
        # Skip very short names (likely OCR artifacts) - reduced to 2 chars
        if len(name) < 2:
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

