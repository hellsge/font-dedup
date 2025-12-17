"""
Deduplication Engine for font glyph deduplication.

This module provides the DeduplicationEngine class which handles:
- Priority-based glyph deduplication across multiple fonts
- Unicode range filtering for targeted deduplication
- Exclusion range protection for preserving specific glyphs
"""

from pathlib import Path

from .models import DeduplicationResult
from .analyzer import FontAnalyzer


class DeduplicationEngine:
    """
    Engine for deduplicating glyphs across multiple fonts.
    
    Uses a priority-based strategy where higher priority fonts retain
    all their glyphs, while lower priority fonts have duplicates removed.
    """
    
    def __init__(self, priority: list[Path] | None = None):
        """
        Initialize the deduplication engine.
        
        Args:
            priority: Optional list of font paths in priority order.
                     First font has highest priority. If None, input
                     order will be used as priority.
        """
        self._priority = [Path(p) for p in priority] if priority else None
        self._analyzer = FontAnalyzer()
    
    def deduplicate(
        self,
        fonts: list[Path],
        unicode_ranges: list[tuple[int, int]] | None = None,
        exclude_ranges: list[tuple[int, int]] | None = None
    ) -> DeduplicationResult:
        """
        Execute deduplication on the given fonts.
        
        Args:
            fonts: List of font file paths to process
            unicode_ranges: Optional list of (start, end) tuples defining
                          Unicode ranges to consider for deduplication.
                          If None, all glyphs are considered.
            exclude_ranges: Optional list of (start, end) tuples defining
                          Unicode ranges to exclude from deduplication.
                          Glyphs in these ranges are always preserved.
        
        Returns:
            DeduplicationResult containing the glyphs to keep and remove
            for each font.
            
        Raises:
            ValueError: If fonts list is empty
        """
        if not fonts:
            raise ValueError("At least one font file is required")
        
        fonts = [Path(p) for p in fonts]
        
        # Determine priority order
        priority_order = self._get_priority_order(fonts)
        
        # Parse all fonts and get their codepoints
        font_codepoints: dict[Path, set[int]] = {}
        for font_path in fonts:
            metadata = self._analyzer.parse_font(font_path)
            font_codepoints[font_path] = metadata.codepoints.copy()
        
        # Initialize result structures
        font_glyphs: dict[Path, set[int]] = {p: set() for p in fonts}
        removed_glyphs: dict[Path, set[int]] = {p: set() for p in fonts}
        
        # Track which codepoints have been claimed by higher priority fonts
        claimed_codepoints: set[int] = set()
        
        # Process fonts in priority order
        for font_path in priority_order:
            original_codepoints = font_codepoints[font_path]
            
            for codepoint in original_codepoints:
                # Check if this codepoint should be considered for deduplication
                in_dedup_range = self._is_in_dedup_range(codepoint, unicode_ranges)
                in_exclude_range = self._is_in_exclude_range(codepoint, exclude_ranges)
                
                # Determine if we should keep this glyph
                if in_exclude_range:
                    # Always keep glyphs in exclude ranges
                    font_glyphs[font_path].add(codepoint)
                elif not in_dedup_range:
                    # Keep glyphs outside dedup range (not subject to deduplication)
                    font_glyphs[font_path].add(codepoint)
                elif codepoint not in claimed_codepoints:
                    # First font to claim this codepoint keeps it
                    font_glyphs[font_path].add(codepoint)
                    claimed_codepoints.add(codepoint)
                else:
                    # Codepoint already claimed by higher priority font
                    removed_glyphs[font_path].add(codepoint)
        
        return DeduplicationResult(
            font_glyphs=font_glyphs,
            removed_glyphs=removed_glyphs
        )
    
    def _get_priority_order(self, fonts: list[Path]) -> list[Path]:
        """
        Get the priority order for fonts.
        
        If explicit priority was set, use that order (only for fonts in the list).
        Otherwise, use the input order.
        
        Args:
            fonts: List of font paths to order
            
        Returns:
            List of font paths in priority order (highest first)
        """
        if self._priority is None:
            return fonts
        
        # Use explicit priority order, but only include fonts that are in the input
        font_set = set(fonts)
        ordered = [p for p in self._priority if p in font_set]
        
        # Add any fonts not in priority list at the end (lowest priority)
        for font in fonts:
            if font not in ordered:
                ordered.append(font)
        
        return ordered
    
    def _is_in_dedup_range(
        self,
        codepoint: int,
        unicode_ranges: list[tuple[int, int]] | None
    ) -> bool:
        """
        Check if a codepoint should be considered for deduplication.
        
        Args:
            codepoint: Unicode codepoint to check
            unicode_ranges: List of (start, end) tuples defining dedup ranges.
                          If None, all codepoints are considered for deduplication.
        
        Returns:
            True if codepoint should be considered for deduplication.
        """
        if unicode_ranges is None:
            return True
        
        for start, end in unicode_ranges:
            if start <= codepoint <= end:
                return True
        
        return False
    
    def _is_in_exclude_range(
        self,
        codepoint: int,
        exclude_ranges: list[tuple[int, int]] | None
    ) -> bool:
        """
        Check if a codepoint is in an exclusion range (should be preserved).
        
        Args:
            codepoint: Unicode codepoint to check
            exclude_ranges: List of (start, end) tuples defining exclusion ranges.
                          If None, no codepoints are excluded.
        
        Returns:
            True if codepoint should be excluded from deduplication (preserved).
        """
        if exclude_ranges is None:
            return False
        
        for start, end in exclude_ranges:
            if start <= codepoint <= end:
                return True
        
        return False
