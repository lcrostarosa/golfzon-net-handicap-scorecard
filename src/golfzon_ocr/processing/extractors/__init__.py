"""
Extractor modules for parsing names, scores, and handicaps from OCR text.
"""
from .name_extractor import NameExtractor
from .score_extractor import ScoreExtractor
from .handicap_extractor import HandicapExtractor

__all__ = ['NameExtractor', 'ScoreExtractor', 'HandicapExtractor']

