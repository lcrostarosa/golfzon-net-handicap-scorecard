"""
CRUD operations for OCR corrections.
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..models import OcrCorrection


def create_correction(
    db: Session,
    ocr_text: str,
    corrected_text: str,
    pattern_type: str = 'name'
) -> OcrCorrection:
    """
    Create a new OCR correction or update frequency if it already exists.
    
    Args:
        db: Database session
        ocr_text: The malformed OCR text
        corrected_text: The correct text
        pattern_type: Type of correction ('name', 'score', 'handicap')
        
    Returns:
        OcrCorrection object
    """
    # Check if this correction already exists
    existing = db.query(OcrCorrection).filter(
        OcrCorrection.ocr_text == ocr_text,
        OcrCorrection.corrected_text == corrected_text,
        OcrCorrection.pattern_type == pattern_type
    ).first()
    
    if existing:
        # Update frequency and last_used_at
        existing.frequency += 1
        existing.last_used_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new correction
    correction = OcrCorrection(
        ocr_text=ocr_text,
        corrected_text=corrected_text,
        pattern_type=pattern_type,
        frequency=1
    )
    db.add(correction)
    db.commit()
    db.refresh(correction)
    return correction


def get_all_corrections(
    db: Session,
    pattern_type: Optional[str] = None
) -> List[OcrCorrection]:
    """
    Get all OCR corrections, optionally filtered by pattern type.
    
    Args:
        db: Database session
        pattern_type: Optional filter by pattern type
        
    Returns:
        List of OcrCorrection objects, ordered by frequency (most used first)
    """
    query = db.query(OcrCorrection)
    
    if pattern_type:
        query = query.filter(OcrCorrection.pattern_type == pattern_type)
    
    # Order by frequency descending (most frequently used first)
    return query.order_by(OcrCorrection.frequency.desc()).all()


def get_correction(
    db: Session,
    correction_id: int
) -> Optional[OcrCorrection]:
    """
    Get a specific OCR correction by ID.
    
    Args:
        db: Database session
        correction_id: The correction ID
        
    Returns:
        OcrCorrection object or None
    """
    return db.query(OcrCorrection).filter(OcrCorrection.id == correction_id).first()


def find_correction_for_text(
    db: Session,
    ocr_text: str,
    pattern_type: str = 'name'
) -> Optional[OcrCorrection]:
    """
    Find a correction for specific OCR text.
    
    Args:
        db: Database session
        ocr_text: The OCR text to find a correction for
        pattern_type: Type of correction to search for
        
    Returns:
        OcrCorrection object or None
    """
    return db.query(OcrCorrection).filter(
        OcrCorrection.ocr_text == ocr_text,
        OcrCorrection.pattern_type == pattern_type
    ).order_by(OcrCorrection.frequency.desc()).first()


def increment_correction_usage(
    db: Session,
    correction_id: int
) -> Optional[OcrCorrection]:
    """
    Increment the usage count for a correction.
    
    Args:
        db: Database session
        correction_id: The correction ID
        
    Returns:
        Updated OcrCorrection object or None
    """
    correction = get_correction(db, correction_id)
    if correction:
        correction.frequency += 1
        correction.last_used_at = datetime.utcnow()
        db.commit()
        db.refresh(correction)
    return correction


def apply_corrections_to_text(
    db: Session,
    text: str,
    pattern_type: str = 'name'
) -> str:
    """
    Apply all stored OCR corrections to a text string.
    
    This function retrieves all corrections of a given type and applies them
    to the input text, ordered by frequency (most common corrections first).
    
    Args:
        db: Database session
        text: The text to apply corrections to
        pattern_type: Type of corrections to apply
        
    Returns:
        Corrected text
    """
    corrections = get_all_corrections(db, pattern_type=pattern_type)
    
    corrected_text = text
    for correction in corrections:
        if correction.ocr_text in corrected_text:
            corrected_text = corrected_text.replace(
                correction.ocr_text,
                correction.corrected_text
            )
            # Update last_used_at
            correction.last_used_at = datetime.utcnow()
    
    # Commit any last_used_at updates
    if corrections:
        db.commit()
    
    return corrected_text


def delete_correction(
    db: Session,
    correction_id: int
) -> bool:
    """
    Delete an OCR correction.
    
    Args:
        db: Database session
        correction_id: The correction ID
        
    Returns:
        True if deleted, False if not found
    """
    correction = get_correction(db, correction_id)
    if correction:
        db.delete(correction)
        db.commit()
        return True
    return False


def get_correction_stats(db: Session) -> Dict[str, int]:
    """
    Get statistics about OCR corrections.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with correction statistics
    """
    total_corrections = db.query(func.count(OcrCorrection.id)).scalar()
    name_corrections = db.query(func.count(OcrCorrection.id)).filter(
        OcrCorrection.pattern_type == 'name'
    ).scalar()
    
    return {
        'total': total_corrections or 0,
        'name': name_corrections or 0,
        'score': db.query(func.count(OcrCorrection.id)).filter(
            OcrCorrection.pattern_type == 'score'
        ).scalar() or 0,
        'handicap': db.query(func.count(OcrCorrection.id)).filter(
            OcrCorrection.pattern_type == 'handicap'
        ).scalar() or 0,
    }

