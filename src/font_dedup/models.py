"""
Data models for font glyph deduplication.

This module defines the core data structures used throughout the
font deduplication process.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GlyphInfo:
    """
    Information about a single glyph in a font.
    
    Attributes:
        codepoint: Unicode code point for this glyph
        glyph_name: Name of the glyph in the font
        glyph_index: Index of the glyph in the font's glyph table
    """
    codepoint: int
    glyph_name: str
    glyph_index: int


@dataclass
class FontMetadata:
    """
    Metadata about a font file.
    
    Attributes:
        path: Path to the font file
        family_name: Font family name
        glyph_count: Total number of glyphs in the font
        codepoints: Set of all Unicode code points supported by the font
    """
    path: Path
    family_name: str
    glyph_count: int
    codepoints: set[int] = field(default_factory=set)


@dataclass
class DuplicateReport:
    """
    Report of duplicate glyphs found across multiple fonts.
    
    Attributes:
        fonts: List of font metadata for analyzed fonts
        duplicates: Mapping of code point to list of font paths containing it
        total_duplicate_count: Total number of duplicate code points found
    """
    fonts: list[FontMetadata] = field(default_factory=list)
    duplicates: dict[int, list[Path]] = field(default_factory=dict)
    total_duplicate_count: int = 0


@dataclass
class DeduplicationResult:
    """
    Result of the deduplication process.
    
    Attributes:
        font_glyphs: Mapping of font path to set of code points to keep
        removed_glyphs: Mapping of font path to set of code points removed
    """
    font_glyphs: dict[Path, set[int]] = field(default_factory=dict)
    removed_glyphs: dict[Path, set[int]] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    Result of font validation.
    
    Attributes:
        is_valid: Whether the font passed validation
        errors: List of error messages
        warnings: List of warning messages
    """
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
