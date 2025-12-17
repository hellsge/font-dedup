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
class GlyphOutline:
    """
    Glyph outline data for shape analysis.
    
    Attributes:
        codepoint: Unicode code point for this glyph
        font_path: Path to the font containing this glyph
        outline_data: Binary outline data of the glyph
        bounding_box: Bounding box coordinates (xMin, yMin, xMax, yMax)
    """
    codepoint: int
    font_path: Path
    outline_data: bytes
    bounding_box: tuple[float, float, float, float]


@dataclass
class ShapeVariant:
    """
    Information about shape variants of the same Unicode code point.
    
    Attributes:
        codepoint: Unicode code point that has variants
        fonts: List of font paths containing this variant
        similarity_scores: Similarity scores between font pairs for this codepoint
    """
    codepoint: int
    fonts: list[Path] = field(default_factory=list)
    similarity_scores: dict[tuple[Path, Path], float] = field(default_factory=dict)


@dataclass
class ShapeVariantReport:
    """
    Report of shape variant analysis across multiple fonts.
    
    Attributes:
        fonts: List of font metadata for analyzed fonts
        shape_variants: List of detected shape variants
        unicode_duplicates: Pure Unicode duplicates (high similarity)
        total_variant_count: Total number of shape variants found
    """
    fonts: list[FontMetadata] = field(default_factory=list)
    shape_variants: list[ShapeVariant] = field(default_factory=list)
    unicode_duplicates: dict[int, list[Path]] = field(default_factory=dict)
    total_variant_count: int = 0


@dataclass
class ShapeAwareDeduplicationResult:
    """
    Result of shape-aware deduplication process.
    
    Attributes:
        font_glyphs: Mapping of font path to set of code points to keep
        removed_glyphs: Mapping of font path to set of code points removed
        preserved_variants: List of shape variants that were preserved
        similarity_data: Similarity data for each codepoint between font pairs
    """
    font_glyphs: dict[Path, set[int]] = field(default_factory=dict)
    removed_glyphs: dict[Path, set[int]] = field(default_factory=dict)
    preserved_variants: list[ShapeVariant] = field(default_factory=list)
    similarity_data: dict[int, dict[tuple[Path, Path], float]] = field(default_factory=dict)


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
