"""
OCR module for extracting text from Golfzon scorecard images.
"""
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
from typing import List, Dict, Tuple, Optional


def extract_columns(image) -> Dict[str, List[str]]:
    """
    Extract player data using column-based OCR for better accuracy.
    
    Golfzon scorecards have consistent column positions:
    - Names on the left (~10-22% of width)
    - Totals near right (~76-87% of width)  
    - Handicaps on far right (~87-98% of width)
    
    Args:
        image: PIL Image object
        
    Returns:
        Dict with 'names', 'totals', 'handicaps' lists
    """
    if image is None:
        raise ValueError("Image is None or invalid")
    
    img_array = np.array(image)
    h, w = img_array.shape[:2]
    
    # Convert to grayscale and apply B&W threshold (removes colored circles/boxes)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    _, bw = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
    
    # Extract score table area (roughly 36-54% of height)
    score_area = bw[int(h*0.36):int(h*0.54), :]
    sh, sw = score_area.shape
    
    # Extract columns
    names_col = score_area[:, int(sw*0.08):int(sw*0.22)]
    totals_col = score_area[:, int(sw*0.76):int(sw*0.87)]
    hcp_col = score_area[:, int(sw*0.87):int(sw*0.98)]
    
    # OCR each column
    names_raw = pytesseract.image_to_string(names_col, config='--oem 3 --psm 6')
    totals_raw = pytesseract.image_to_string(totals_col, config='--oem 3 --psm 6')
    hcp_raw = pytesseract.image_to_string(hcp_col, config='--oem 3 --psm 6')
    
    # Parse names - extract alphabetic sequences of 4+ chars
    names = []
    for line in names_raw.split('\n'):
        matches = re.findall(r'[A-Za-z]{4,}', line)
        for m in matches:
            if m.lower() not in ['hole', 'rank', 'total', 'ghcp', 'g-hcp']:
                names.append(_clean_name(m))
    
    # Parse totals
    totals = []
    for line in totals_raw.split('\n'):
        line = line.strip()
        if line:
            cleaned = _clean_total(line)
            if cleaned and '(' in cleaned:
                totals.append(cleaned)
    
    # Parse handicaps
    handicaps = []
    for line in hcp_raw.split('\n'):
        line = line.strip()
        if line and line.upper() not in ['G-HCP', 'GHCP', 'HCP']:
            cleaned = _clean_handicap(line)
            if cleaned:
                handicaps.append(cleaned)
    
    return {
        'names': names,
        'totals': totals,
        'handicaps': handicaps
    }


def _clean_name(s: str) -> str:
    """Clean OCR name errors."""
    s = s.strip()
    # Remove leading B/G from badge overlay
    if len(s) > 4 and s[0] in 'BG' and s[1:2].islower():
        s = s[1:]
    # Common corrections
    corrections = {
        'acorm': 'Acorm', 'bacorm': 'Acorm', 'racorm': 'Acorm',
        'lcrostarosa': 'Lcrostarosa', 'tcrostarosa': 'Lcrostarosa',
        'cjdyer': 'Cjdyer', 'cidyer': 'Cjdyer', 'gjdyer': 'Cjdyer',
    }
    return corrections.get(s.lower(), s.capitalize())


def _clean_total(s: str) -> str:
    """Clean OCR total score like 44048) -> 44(+8)."""
    # Pre-clean common OCR substitutions
    s = s.replace('I', '1').replace('l', '1').replace('O', '0').replace('o', '0')
    s = s.replace('a', '4').replace('e', '4').replace('s', '5').replace('S', '5')
    s = s.replace('G', '6').replace('g', '9').replace('B', '8')
    
    # Try exact pattern: DD(+D) or DD(D)
    m = re.search(r'(\d{2})\s*\(\s*[+\-]?\s*(\d)\s*\)', s)
    if m:
        return f'{m.group(1)}(+{m.group(2)})'
    
    # Pattern: 44048) - first 2 digits are score, last before ) is diff
    m = re.search(r'^[^0-9]*(\d{2})\d*(\d)\s*\)', s)
    if m:
        return f'{m.group(1)}(+{m.group(2)})'
    
    # Looser pattern: any sequence ending with )
    m = re.search(r'(\d{2})\D*(\d)\s*\)', s)
    if m:
        return f'{m.group(1)}(+{m.group(2)})'
    
    # Fallback: find all digits
    digits = re.findall(r'\d', s)
    if len(digits) >= 3:
        return f'{digits[0]}{digits[1]}(+{digits[-1]})'
    elif len(digits) == 2:
        # Assume second digit is diff (common for close games)
        return f'4{digits[0]}(+{digits[1]})'
    
    return ''


def _clean_handicap(s: str) -> str:
    """Clean OCR handicap like AL? -> -1.7."""
    # Replace common OCR errors
    s = s.replace('A', '-').replace('i', '1').replace('l', '1').replace('I', '1')
    s = s.replace('>', '2').replace('?', '7').replace('L', '1')
    s = s.replace('O', '0').replace('o', '0').replace('Z', '2')
    
    # Extract number
    m = re.search(r'([+\-]?\d+\.?\d*)', s)
    if m:
        val = m.group(1)
        # Add decimal if needed (17 -> 1.7)
        if '.' not in val and len(val.lstrip('+-')) >= 2:
            sign = val[0] if val[0] in '+-' else ''
            digits = val.lstrip('+-')
            val = sign + digits[:-1] + '.' + digits[-1]
        # Add sign if needed
        if val and val[0] not in '+-':
            try:
                val = '-' + val if float(val) < 5 else '+' + val
            except ValueError:
                pass
        return val
    return ''


def extract_text(image):
    """
    Extract text from an image using OCR.
    
    Args:
        image: PIL Image object
        
    Returns:
        str: Extracted text from the image
        
    Raises:
        ValueError: If image is invalid or cannot be processed
        Exception: If OCR fails to process the image
    """
    if image is None:
        raise ValueError("Image is None or invalid")
    
    try:
        # Convert PIL Image to numpy array for OpenCV processing
        img_array = np.array(image)
        
        if img_array.size == 0:
            raise ValueError("Image array is empty")
        
        # Handle grayscale images
        if len(img_array.shape) == 2:
            # Already grayscale
            gray = img_array
        elif len(img_array.shape) == 3:
            # Convert RGB to BGR if needed (OpenCV uses BGR)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError(f"Unsupported image format with shape: {img_array.shape}")
        
        # Optional: enhance contrast
        # Apply CLAHE for better OCR results
        try:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
        except Exception:
            # If CLAHE fails, use the grayscale image directly
            enhanced = gray
        
        # Additional preprocessing to handle Golfzon scorecard formatting
        # (circles around birdies, boxes around bogeys, etc.)
        try:
            # Apply binary threshold to clean up circles/boxes
            _, thresh = cv2.threshold(enhanced, 180, 255, cv2.THRESH_BINARY)
            
            # Morphological operations to remove thin lines (circles/boxes)
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Use cleaned version for OCR
            enhanced = cleaned
        except Exception:
            # If preprocessing fails, continue with CLAHE-enhanced version
            pass
        
        # Use pytesseract to extract text
        # PSM 6 works best for our table format
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(enhanced, config=custom_config)
        
        # Also try PSM 11 as backup for sparse text (can help with missing handicaps)
        # Store it for potential fallback lookup
        try:
            backup_text = pytesseract.image_to_string(enhanced, config=r'--oem 3 --psm 11')
            # Store in image metadata or return as tuple - for now just use main text
            # The parser can request backup if needed
        except:
            backup_text = None
        
        if not text or not text.strip():
            raise ValueError("OCR returned empty text. Image may be too blurry or contain no readable text.")
        
        return text
        
    except pytesseract.TesseractError as e:
        raise Exception(f"Tesseract OCR error: {str(e)}. Make sure Tesseract is installed and in your PATH.")
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

