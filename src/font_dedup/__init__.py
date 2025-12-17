"""
Font Glyph Deduplication Tool

A TTF font optimization tool that analyzes multiple font files,
identifies duplicate glyphs, and removes them based on priority settings.
"""

__version__ = "0.1.0"

from .models import (
    GlyphInfo,
    FontMetadata,
    DuplicateReport,
    DeduplicationResult,
    ValidationResult,
    GlyphOutline,
    ShapeVariant,
    ShapeVariantReport,
    ShapeAwareDeduplicationResult,
)
from .analyzer import FontAnalyzer
from .shape_analyzer import ShapeAnalyzer
from .engine import DeduplicationEngine
from .generator import FontGenerator
from .validator import Validator
from .reporter import Reporter
from .utils import (
    analyze_and_report,
    deduplicate_and_report,
    generate_and_validate,
    get_file_size_report,
)
from .cli import main

__all__ = [
    "GlyphInfo",
    "FontMetadata",
    "DuplicateReport",
    "DeduplicationResult",
    "ValidationResult",
    "GlyphOutline",
    "ShapeVariant",
    "ShapeVariantReport",
    "ShapeAwareDeduplicationResult",
    "FontAnalyzer",
    "ShapeAnalyzer",
    "DeduplicationEngine",
    "FontGenerator",
    "Validator",
    "Reporter",
    "analyze_and_report",
    "deduplicate_and_report",
    "generate_and_validate",
    "get_file_size_report",
    "main",
]
