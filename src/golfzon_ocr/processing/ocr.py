"""
OCR module for extracting text from Golfzon scorecard images.
"""
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

# Register HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    # pillow-heif not installed, HEIC files won't be supported
    pass


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
        
        # Enhance image for better OCR results
        # Step 1: Upscale image if it's too small (improves OCR accuracy)
        height, width = gray.shape
        if height < 1000 or width < 1000:
            scale_factor = max(1000 / height, 1000 / width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Step 2: Apply gentle contrast enhancement with CLAHE (less aggressive)
        try:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_gray = clahe.apply(gray)
        except Exception:
            enhanced_gray = gray
        
        # Step 3: Apply gentle denoising (only if needed)
        try:
            denoised = cv2.bilateralFilter(enhanced_gray, 5, 50, 50)  # More gentle
        except Exception:
            denoised = enhanced_gray
        
        # Step 4: Try multiple preprocessing approaches - start with simpler ones
        # Approach 1: Simple grayscale (no thresholding - best for photos)
        thresh_simple = denoised
        
        # Approach 2: Otsu's thresholding (adaptive but less aggressive)
        try:
            _, thresh_otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        except Exception:
            thresh_otsu = denoised
        
        # Approach 3: Adaptive thresholding (for comparison, but less aggressive)
        try:
            thresh_adaptive = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 10  # Larger block size, more offset for gentler thresholding
            )
        except Exception:
            thresh_adaptive = denoised
        
        # Approach 4: Inverted threshold (sometimes works better)
        try:
            _, thresh_inv = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        except Exception:
            thresh_inv = denoised
        
        # Try OCR on multiple preprocessing approaches and PSM modes
        # PSM modes to try: 6 (uniform block), 11 (sparse text), 4 (single column), 12 (sparse with OSD)
        # Start with simpler PSM modes first
        psm_modes = [
            (11, 'sparse text'),  # Try 11 first as it found scores in testing
            (6, 'uniform block'),
            (12, 'sparse with OSD'),  # Also found scores
            (4, 'single column'),
            (3, 'fully automatic'),
        ]
        
        # Preprocessing approaches in order of preference (simpler first)
        preprocessing_approaches = [
            (thresh_simple, 'simple'),  # Try simplest first
            (thresh_otsu, 'otsu'),
            (thresh_adaptive, 'adaptive'),
            (thresh_inv, 'inverted'),
        ]
        
        results = []
        for img_prep, prep_name in preprocessing_approaches:
            for psm, desc in psm_modes:
                try:
                    config = f'--oem 3 --psm {psm}'
                    ocr_result = pytesseract.image_to_string(img_prep, config=config)
                    if ocr_result and ocr_result.strip():
                        # Count meaningful characters (letters, numbers, common symbols)
                        meaningful_chars = sum(1 for c in ocr_result if c.isalnum() or c in '()+-.,')
                        if meaningful_chars > 10:  # Only keep results with substantial meaningful content
                            results.append((ocr_result, meaningful_chars, psm, prep_name))
                except Exception:
                    pass
        
        # Sort by meaningful character count (better quality metric)
        results.sort(key=lambda x: x[1], reverse=True)

        # Prioritize results that contain score patterns or handicap patterns
        # Score pattern: "38(+2)" or "43(+7)" or "43 (+13)" (with spaces)
        # Handicap pattern: "+11.4" or "-2.2"
        score_pattern = re.compile(r'\d{2,3}\s*\([+\-]?\d+\)')
        handicap_pattern = re.compile(r'[+\-]\d+\.\d+')
        name_pattern = re.compile(r'\b(Beachy|FirstOrLast|elBeachy|RQFirstOrLast|Acorm|Cjdyer|Lcrostarosa)\b', re.IGNORECASE)
        
        def score_quality(text):
            """Score text quality: higher is better"""
            score_matches = len(score_pattern.findall(text))
            handicap_matches = len(handicap_pattern.findall(text))
            name_matches = len(name_pattern.findall(text))
            meaningful_chars = sum(1 for c in text if c.isalnum() or c in '()+-.,')
            # Prioritize results with score/handicap patterns AND player names
            return score_matches * 1000 + handicap_matches * 500 + name_matches * 200 + meaningful_chars
        
        # Re-sort by quality score
        results.sort(key=lambda x: score_quality(x[0]), reverse=True)
        
        # Use the best result
        text = results[0][0] if results else ""
        backup_text = results[1][0] if len(results) > 1 else None
        
        # If we have multiple good results, try to combine them intelligently
        # Prioritize combining results that have player names
        if len(results) > 1:
            combined_text = text
            seen_lines = set(text.split('\n'))
            # Look for results with player names that might be missing from the best result
            for result_text, char_count, psm, prep_name in results[1:6]:  # Check more results
                if char_count > 20:  # Only combine if substantial
                    # Check if this result has names not in the main result
                    result_names = set(name_pattern.findall(result_text))
                    main_names = set(name_pattern.findall(combined_text))
                    has_new_names = bool(result_names - main_names)
                    
                    # Also check for scores/handicaps
                    result_scores = score_pattern.findall(result_text)
                    result_handicaps = handicap_pattern.findall(result_text)
                    main_scores = score_pattern.findall(combined_text)
                    main_handicaps = handicap_pattern.findall(combined_text)
                    has_new_data = len(result_scores) > len(main_scores) or len(result_handicaps) > len(main_handicaps)
                    
                    if has_new_names or has_new_data:
                        # Add unique lines from this result
                        for line in result_text.split('\n'):
                            line_clean = line.strip()
                            if line_clean and line_clean not in seen_lines and len(line_clean) > 3:
                                combined_text += "\n" + line_clean
                                seen_lines.add(line_clean)
            
            if len(combined_text.strip()) > len(text.strip()):
                text = combined_text
        
        if not text or not text.strip():
            raise ValueError("OCR returned empty text. Image may be too blurry or contain no readable text.")
        
        return text
        
    except pytesseract.TesseractError as e:
        raise Exception(f"Tesseract OCR error: {str(e)}. Make sure Tesseract is installed and in your PATH.")
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")

