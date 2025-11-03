"""
OCR module for extracting text from Golfzon scorecard images.
"""
import pytesseract
from PIL import Image
import cv2
import numpy as np


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

