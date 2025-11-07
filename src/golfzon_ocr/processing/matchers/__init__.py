"""
Matcher modules for extracting player data using different strategies.
"""
from .base import BaseMatcher
from .score_matcher import ScoreMatcher
from .line_matcher import LineMatcher
from .table_matcher import TableMatcher

__all__ = ['BaseMatcher', 'ScoreMatcher', 'LineMatcher', 'TableMatcher']

