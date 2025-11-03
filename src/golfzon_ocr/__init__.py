"""
Golfzon OCR - A Python application for extracting player data from Golfzon scorecard screenshots.
"""

__version__ = "0.1.0"

# Import main modules for convenience
from . import models
from . import db
from . import processing
from . import services
from . import export

__all__ = [
    'models',
    'db',
    'processing',
    'services',
    'export',
]
