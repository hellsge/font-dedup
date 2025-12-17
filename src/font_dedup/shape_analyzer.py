"""
Shape Analyzer module for glyph outline extraction and similarity analysis.

This module provides the ShapeAnalyzer class which handles:
- Extracting glyph outline data from TTF fonts
- Computing similarity between glyph shapes
- Detecting shape variants across multiple fonts
"""

import hashlib
from pathlib import Path
from typing import Optional

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

from .models import GlyphOutline, ShapeVariant, ShapeVariantReport, FontMetadata


class ShapeAnalyzer:
    """
    Analyzer for glyph shapes and outline data.
    
    Provides functionality to extract glyph outlines, compute shape similarity,
    and detect shape variants across multiple font files.
    """
    
    def extract_glyph_outline(self, font_path: Path, codepoint: int) -> Optional[GlyphOutline]:
        """
        Extract outline data for a specific glyph from a font.
        
        Args:
            font_path: Path to the TTF font file
            codepoint: Unicode code point of the glyph to extract
            
        Returns:
            GlyphOutline object containing outline data, or None if glyph not found
            
        Raises:
            FileNotFoundError: If the font file doesn't exist
            ValueError: If the file is not a valid TTF font
        """
        font_path = Path(font_path)
        
        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")
        
        try:
            font = TTFont(font_path)
        except Exception as e:
            raise ValueError(f"Invalid TTF font file: {font_path}") from e
        
        try:
            # Get the best cmap table
            cmap = font.getBestCmap()
            if cmap is None or codepoint not in cmap:
                return None
            
            glyph_name = cmap[codepoint]
            glyph_set = font.getGlyphSet()
            
            if glyph_name not in glyph_set:
                return None
            
            glyph = glyph_set[glyph_name]
            
            # Use RecordingPen to capture the outline data
            recording_pen = RecordingPen()
            glyph.draw(recording_pen)
            
            # Get bounding box
            bounding_box = self._calculate_bounding_box(recording_pen.value)
            
            # Serialize the outline data to bytes
            outline_data = self._serialize_outline_data(recording_pen.value)
            
            return GlyphOutline(
                codepoint=codepoint,
                font_path=font_path,
                outline_data=outline_data,
                bounding_box=bounding_box
            )
            
        finally:
            font.close()
    
    def _calculate_bounding_box(self, outline_commands: list) -> tuple[float, float, float, float]:
        """
        Calculate bounding box from outline commands.
        
        Args:
            outline_commands: List of drawing commands from RecordingPen
            
        Returns:
            Tuple of (xMin, yMin, xMax, yMax)
        """
        if not outline_commands:
            return (0.0, 0.0, 0.0, 0.0)
        
        x_coords = []
        y_coords = []
        
        for command, args in outline_commands:
            if command == 'moveTo':
                x_coords.append(args[0][0])
                y_coords.append(args[0][1])
            elif command == 'lineTo':
                x_coords.append(args[0][0])
                y_coords.append(args[0][1])
            elif command == 'curveTo':
                # Add all control points and end point
                for point in args:
                    x_coords.append(point[0])
                    y_coords.append(point[1])
            elif command == 'qCurveTo':
                # Add all control points and end point
                for point in args:
                    x_coords.append(point[0])
                    y_coords.append(point[1])
        
        if not x_coords or not y_coords:
            return (0.0, 0.0, 0.0, 0.0)
        
        return (
            float(min(x_coords)),
            float(min(y_coords)),
            float(max(x_coords)),
            float(max(y_coords))
        )
    
    def _serialize_outline_data(self, outline_commands: list) -> bytes:
        """
        Serialize outline commands to bytes for storage and comparison.
        
        Args:
            outline_commands: List of drawing commands from RecordingPen
            
        Returns:
            Serialized outline data as bytes
        """
        # Convert outline commands to a string representation
        outline_str = str(outline_commands)
        
        # Return as UTF-8 encoded bytes
        return outline_str.encode('utf-8')
    
    def calculate_similarity(self, outline1: GlyphOutline, outline2: GlyphOutline) -> float:
        """
        Calculate similarity between two glyph outlines.
        
        采用严格的相等性检查：只有轮廓数据完全相同才返回 1.0，
        否则返回 0.0。这是因为 TTF 文件中的轮廓数据是矢量数据，
        不包含抗锯齿或 hinting 等渲染时的差异。任何轮廓数据的
        不同都意味着字形设计上的真实差异。
        
        Args:
            outline1: First glyph outline
            outline2: Second glyph outline
            
        Returns:
            Similarity score: 1.0 if identical, 0.0 if different
        """
        # 轮廓数据完全相同才算相同字形
        if outline1.outline_data == outline2.outline_data:
            return 1.0
        else:
            return 0.0

    
    def find_shape_variants(
        self, 
        fonts: list[Path], 
        similarity_threshold: float = 1.0,
        codepoint_limit: int | None = None
    ) -> ShapeVariantReport:
        """
        Find shape variants across multiple fonts.
        
        Analyzes the same Unicode code points across different fonts
        to identify cases where the glyph shapes differ significantly.
        
        注意：此方法可能需要较长时间，因为需要提取和比较每个字符的轮廓数据。
        对于包含数千字符的字体，建议使用 codepoint_limit 参数限制分析范围。
        
        Args:
            fonts: List of font file paths to analyze
            similarity_threshold: Threshold below which glyphs are considered variants
                                 (注意：当前实现使用严格相等，此参数保留用于兼容性)
            codepoint_limit: Optional limit on number of codepoints to analyze
            
        Returns:
            ShapeVariantReport containing detected variants and duplicates
            
        Raises:
            ValueError: If fonts list is empty or similarity_threshold is invalid
        """
        if not fonts:
            raise ValueError("At least one font file is required")
        
        if not (0.0 <= similarity_threshold <= 1.0):
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        
        # First, get font metadata for all fonts
        from .analyzer import FontAnalyzer
        analyzer = FontAnalyzer()
        
        font_metadata_list = []
        all_codepoints = set()
        
        for font_path in fonts:
            font_path = Path(font_path)
            metadata = analyzer.parse_font(font_path)
            font_metadata_list.append(metadata)
            all_codepoints.update(metadata.codepoints)
        
        # 找出在多个字体中都存在的 codepoint
        shared_codepoints = set()
        for codepoint in all_codepoints:
            fonts_with_codepoint = [
                metadata.path for metadata in font_metadata_list
                if codepoint in metadata.codepoints
            ]
            if len(fonts_with_codepoint) > 1:
                shared_codepoints.add(codepoint)
        
        # 如果设置了限制，只分析前 N 个 codepoint
        if codepoint_limit is not None and len(shared_codepoints) > codepoint_limit:
            shared_codepoints = set(sorted(shared_codepoints)[:codepoint_limit])
        
        shape_variants = []
        unicode_duplicates = {}
        
        # 优化：一次性打开所有字体文件，避免重复打开
        from fontTools.ttLib import TTFont
        from fontTools.pens.recordingPen import RecordingPen
        
        opened_fonts = {}
        try:
            for font_path in fonts:
                opened_fonts[font_path] = TTFont(font_path)
            
            # 分析每个共享的 codepoint，检测字形变体
            for codepoint in shared_codepoints:
                fonts_with_codepoint = [
                    metadata.path for metadata in font_metadata_list
                    if codepoint in metadata.codepoints
                ]
                
                # 从所有字体中提取该 codepoint 的轮廓数据（使用已打开的字体）
                outlines = {}
                for font_path in fonts_with_codepoint:
                    font = opened_fonts[font_path]
                    cmap = font.getBestCmap()
                    
                    if cmap is None or codepoint not in cmap:
                        continue
                    
                    glyph_name = cmap[codepoint]
                    glyph_set = font.getGlyphSet()
                    
                    if glyph_name not in glyph_set:
                        continue
                    
                    glyph = glyph_set[glyph_name]
                    recording_pen = RecordingPen()
                    glyph.draw(recording_pen)
                    
                    # 直接序列化轮廓数据用于比较
                    outline_data = str(recording_pen.value).encode('utf-8')
                    
                    # 计算边界框
                    bounding_box = self._calculate_bounding_box(recording_pen.value)
                    
                    from .models import GlyphOutline
                    outlines[font_path] = GlyphOutline(
                        codepoint=codepoint,
                        font_path=font_path,
                        outline_data=outline_data,
                        bounding_box=bounding_box
                    )
                
                if len(outlines) < 2:
                    continue
                
                # 计算所有字体对之间的相似度
                # 注意：相似度现在是二元的（1.0 = 完全相同，0.0 = 不同）
                similarity_scores = {}
                font_paths = list(outlines.keys())
                
                has_variant = False
                for i in range(len(font_paths)):
                    for j in range(i + 1, len(font_paths)):
                        font1, font2 = font_paths[i], font_paths[j]
                        similarity = self.calculate_similarity(
                            outlines[font1], 
                            outlines[font2]
                        )
                        similarity_scores[(font1, font2)] = similarity
                        
                        # 如果任何一对的相似度 < 1.0（即轮廓数据不同），则为字形变体
                        if similarity < 1.0:
                            has_variant = True
                
                if has_variant:
                    # 该 codepoint 存在字形变体（不同字体中轮廓数据不同）
                    shape_variants.append(ShapeVariant(
                        codepoint=codepoint,
                        fonts=font_paths,
                        similarity_scores=similarity_scores
                    ))
                else:
                    # 该 codepoint 是真正的 Unicode 重复（所有字体中轮廓完全相同）
                    unicode_duplicates[codepoint] = font_paths
        
        finally:
            # 关闭所有打开的字体文件
            for font in opened_fonts.values():
                font.close()
        
        return ShapeVariantReport(
            fonts=font_metadata_list,
            shape_variants=shape_variants,
            unicode_duplicates=unicode_duplicates,
            total_variant_count=len(shape_variants)
        )