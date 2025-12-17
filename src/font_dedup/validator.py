"""
Validator module for verifying generated TTF font files.

This module provides the Validator class which handles:
- Validating that output files are valid TTF format
- Verifying that all retained glyphs are accessible via cmap table
- Reporting validation errors and warnings
"""

from pathlib import Path
from fontTools.ttLib import TTFont

from .models import ValidationResult


class Validator:
    """
    Validator for TTF font files.
    
    Provides functionality to validate font file format and
    verify glyph accessibility through Unicode mappings.
    """
    
    def validate_ttf(self, font_path: Path) -> ValidationResult:
        """
        Validate that a file is a valid TTF font format.
        
        Checks that the file can be parsed by fonttools and contains
        the required tables for a valid TrueType font.
        
        Args:
            font_path: Path to the font file to validate
            
        Returns:
            ValidationResult indicating whether the font is valid
        """
        font_path = Path(font_path)
        errors: list[str] = []
        warnings: list[str] = []
        
        # Check file exists
        if not font_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"文件不存在: {font_path}"],
                warnings=[]
            )
        
        # Check file is not empty
        if font_path.stat().st_size == 0:
            return ValidationResult(
                is_valid=False,
                errors=[f"文件为空: {font_path}"],
                warnings=[]
            )
        
        # Try to parse as TTF
        try:
            font = TTFont(font_path)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"无法解析 TTF 文件: {font_path}, 错误: {str(e)}"],
                warnings=[]
            )

        try:
            # Check for required TTF tables
            required_tables = ['cmap', 'head', 'hhea', 'hmtx', 'maxp', 'name', 'post']
            missing_tables = []
            
            for table in required_tables:
                if table not in font:
                    missing_tables.append(table)
            
            if missing_tables:
                errors.append(f"缺少必需的 TTF table: {', '.join(missing_tables)}")
            
            # Check for glyf or CFF table (one is required for outlines)
            has_outlines = 'glyf' in font or 'CFF ' in font or 'CFF2' in font
            if not has_outlines:
                errors.append("缺少 glyph 轮廓数据 (glyf 或 CFF table)")
            
            # Check cmap table has valid mappings
            cmap = font.getBestCmap()
            if cmap is None:
                warnings.append("cmap table 为空或无法读取")
            elif len(cmap) == 0:
                warnings.append("cmap table 不包含任何 Unicode 映射")
            
            # Check head table for valid values
            if 'head' in font:
                head = font['head']
                if head.magicNumber != 0x5F0F3CF5:
                    errors.append(f"head table magic number 无效: {hex(head.magicNumber)}")
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
        finally:
            font.close()
    
    def validate_glyphs(
        self,
        font_path: Path,
        expected_codepoints: set[int]
    ) -> ValidationResult:
        """
        Validate that specified Unicode code points are accessible in the font.
        
        Checks that each expected code point can be mapped to a glyph
        through the font's cmap table.
        
        Args:
            font_path: Path to the font file to validate
            expected_codepoints: Set of Unicode code points that should be accessible
            
        Returns:
            ValidationResult indicating whether all glyphs are accessible
        """
        font_path = Path(font_path)
        errors: list[str] = []
        warnings: list[str] = []
        
        # First validate the TTF format
        ttf_result = self.validate_ttf(font_path)
        if not ttf_result.is_valid:
            return ttf_result
        
        # Add any warnings from TTF validation
        warnings.extend(ttf_result.warnings)
        
        try:
            font = TTFont(font_path)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"无法打开字体文件: {font_path}, 错误: {str(e)}"],
                warnings=warnings
            )
        
        try:
            cmap = font.getBestCmap()
            
            if cmap is None:
                return ValidationResult(
                    is_valid=False,
                    errors=["无法获取 cmap table"],
                    warnings=warnings
                )
            
            # Check each expected codepoint
            missing_codepoints: list[int] = []
            inaccessible_glyphs: list[tuple[int, str]] = []
            
            glyph_order = font.getGlyphOrder()
            
            for codepoint in expected_codepoints:
                if codepoint not in cmap:
                    missing_codepoints.append(codepoint)
                else:
                    # Verify the glyph name exists in the font
                    glyph_name = cmap[codepoint]
                    if glyph_name not in glyph_order:
                        inaccessible_glyphs.append((codepoint, glyph_name))
            
            # Report missing codepoints
            if missing_codepoints:
                # Group for readability if many are missing
                if len(missing_codepoints) <= 10:
                    cp_list = ', '.join(f'U+{cp:04X}' for cp in sorted(missing_codepoints))
                else:
                    first_five = ', '.join(f'U+{cp:04X}' for cp in sorted(missing_codepoints)[:5])
                    cp_list = f"{first_five} ... (共 {len(missing_codepoints)} 个)"
                errors.append(f"以下 code point 在 cmap 中不存在: {cp_list}")
            
            # Report inaccessible glyphs
            if inaccessible_glyphs:
                if len(inaccessible_glyphs) <= 5:
                    glyph_list = ', '.join(
                        f'U+{cp:04X} -> {name}' 
                        for cp, name in inaccessible_glyphs
                    )
                else:
                    first_three = ', '.join(
                        f'U+{cp:04X} -> {name}' 
                        for cp, name in inaccessible_glyphs[:3]
                    )
                    glyph_list = f"{first_three} ... (共 {len(inaccessible_glyphs)} 个)"
                errors.append(f"以下 glyph 在字体中不可访问: {glyph_list}")
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
        finally:
            font.close()
