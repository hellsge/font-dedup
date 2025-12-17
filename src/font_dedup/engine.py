"""
Deduplication Engine for font glyph deduplication.

This module provides the DeduplicationEngine class which handles:
- Priority-based glyph deduplication across multiple fonts
- Unicode range filtering for targeted deduplication
- Exclusion range protection for preserving specific glyphs
"""

from pathlib import Path

from .models import DeduplicationResult, ShapeAwareDeduplicationResult
from .analyzer import FontAnalyzer
from .shape_analyzer import ShapeAnalyzer


class DeduplicationEngine:
    """
    Engine for deduplicating glyphs across multiple fonts.
    
    Uses a priority-based strategy where higher priority fonts retain
    all their glyphs, while lower priority fonts have duplicates removed.
    
    Supports shape-aware deduplication to preserve glyph variants.
    """
    
    def __init__(
        self,
        priority: list[Path] | None = None,
        shape_analysis_enabled: bool = False,
        similarity_threshold: float = 1.0
    ):
        """
        Initialize the deduplication engine.
        
        Args:
            priority: Optional list of font paths in priority order.
                     First font has highest priority. If None, input
                     order will be used as priority.
            shape_analysis_enabled: Whether to enable shape-aware deduplication.
                                   When enabled, glyphs with different shapes
                                   are preserved even if they share the same
                                   Unicode code point.
            similarity_threshold: Threshold for shape similarity (0.0-1.0).
                                 Glyphs with similarity below this threshold
                                 are considered shape variants and preserved.
                                 Only used when shape_analysis_enabled is True.
        """
        self._priority = [Path(p) for p in priority] if priority else None
        self._analyzer = FontAnalyzer()
        self._shape_analysis_enabled = shape_analysis_enabled
        self._similarity_threshold = similarity_threshold
        
        # 仅在启用字形分析时初始化 ShapeAnalyzer
        if self._shape_analysis_enabled:
            self._shape_analyzer = ShapeAnalyzer()
        else:
            self._shape_analyzer = None
    
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
    
    def deduplicate_with_shape_analysis(
        self,
        fonts: list[Path],
        unicode_ranges: list[tuple[int, int]] | None = None,
        exclude_ranges: list[tuple[int, int]] | None = None
    ) -> ShapeAwareDeduplicationResult:
        """
        Execute shape-aware deduplication on the given fonts.
        
        This method analyzes glyph shapes to distinguish between true Unicode
        duplicates (same code point, same shape) and shape variants (same code
        point, different shapes). Shape variants are preserved across fonts.
        
        Args:
            fonts: List of font file paths to process
            unicode_ranges: Optional list of (start, end) tuples defining
                          Unicode ranges to consider for deduplication.
                          If None, all glyphs are considered.
            exclude_ranges: Optional list of (start, end) tuples defining
                          Unicode ranges to exclude from deduplication.
                          Glyphs in these ranges are always preserved.
        
        Returns:
            ShapeAwareDeduplicationResult containing the glyphs to keep and remove
            for each font, along with preserved shape variants.
            
        Raises:
            ValueError: If fonts list is empty or shape analysis is not enabled
        """
        if not fonts:
            raise ValueError("At least one font file is required")
        
        if not self._shape_analysis_enabled:
            raise ValueError(
                "Shape analysis is not enabled. Initialize DeduplicationEngine "
                "with shape_analysis_enabled=True to use this method."
            )
        
        fonts = [Path(p) for p in fonts]
        
        # Determine priority order
        priority_order = self._get_priority_order(fonts)
        
        # Parse all fonts and get their codepoints
        font_codepoints: dict[Path, set[int]] = {}
        for font_path in fonts:
            metadata = self._analyzer.parse_font(font_path)
            font_codepoints[font_path] = metadata.codepoints.copy()
        
        # 找出在多个字体中都存在的 codepoint（可能的重复或变体）
        all_codepoints = set()
        for codepoints in font_codepoints.values():
            all_codepoints.update(codepoints)
        
        shared_codepoints = set()
        for codepoint in all_codepoints:
            fonts_with_codepoint = [
                font_path for font_path in fonts
                if codepoint in font_codepoints[font_path]
            ]
            if len(fonts_with_codepoint) > 1:
                shared_codepoints.add(codepoint)
        
        # 使用 ShapeAnalyzer 分析共享的 codepoint，识别字形变体
        # 注意：这里我们只分析共享的 codepoint 以提高性能
        from .models import ShapeVariant
        
        shape_variants_map: dict[int, ShapeVariant] = {}
        similarity_data: dict[int, dict[tuple[Path, Path], float]] = {}
        
        # 批量分析字形变体
        if shared_codepoints:
            variant_report = self._shape_analyzer.find_shape_variants(
                fonts=fonts,
                similarity_threshold=self._similarity_threshold,
                codepoint_limit=None  # 分析所有共享的 codepoint
            )
            
            # 构建字形变体映射
            for variant in variant_report.shape_variants:
                shape_variants_map[variant.codepoint] = variant
                similarity_data[variant.codepoint] = variant.similarity_scores
        
        # Initialize result structures
        font_glyphs: dict[Path, set[int]] = {p: set() for p in fonts}
        removed_glyphs: dict[Path, set[int]] = {p: set() for p in fonts}
        preserved_variants: list[ShapeVariant] = []
        
        # Track which codepoints have been claimed by higher priority fonts
        # 对于字形变体，我们不将其标记为 claimed，因为每个字体都应保留其独特的字形
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
                elif codepoint in shape_variants_map:
                    # 这是一个字形变体，保留它（不同字体中的字形不同）
                    font_glyphs[font_path].add(codepoint)
                    
                    # 记录被保护的字形变体（只记录一次）
                    if shape_variants_map[codepoint] not in preserved_variants:
                        preserved_variants.append(shape_variants_map[codepoint])
                elif codepoint not in claimed_codepoints:
                    # First font to claim this codepoint keeps it (真正的 Unicode 重复)
                    font_glyphs[font_path].add(codepoint)
                    claimed_codepoints.add(codepoint)
                else:
                    # Codepoint already claimed by higher priority font (真正的重复)
                    removed_glyphs[font_path].add(codepoint)
        
        return ShapeAwareDeduplicationResult(
            font_glyphs=font_glyphs,
            removed_glyphs=removed_glyphs,
            preserved_variants=preserved_variants,
            similarity_data=similarity_data
        )
