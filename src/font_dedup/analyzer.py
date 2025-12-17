"""
Font Analyzer module for parsing TTF files and extracting glyph information.

This module provides the FontAnalyzer class which handles:
- Parsing TTF font files using fonttools
- Extracting glyph information and Unicode mappings from cmap tables
- Detecting duplicate glyphs across multiple fonts
"""

from pathlib import Path
from fontTools.ttLib import TTFont

from .models import FontMetadata, GlyphInfo, DuplicateReport


class FontAnalyzer:
    """
    Analyzer for TTF font files.
    
    Provides functionality to parse fonts, extract glyph information,
    and detect duplicates across multiple font files.
    """
    
    def parse_font(self, font_path: Path) -> FontMetadata:
        """
        Parse a single font file and return its metadata.
        
        Args:
            font_path: Path to the TTF font file
            
        Returns:
            FontMetadata containing font information
            
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
            # Extract family name from name table
            family_name = self._get_family_name(font)
            
            # Extract codepoints from cmap table
            codepoints = self._get_codepoints(font)
            
            # Get total glyph count
            glyph_count = len(font.getGlyphOrder())
            
            return FontMetadata(
                path=font_path,
                family_name=family_name,
                glyph_count=glyph_count,
                codepoints=codepoints
            )
        finally:
            font.close()
    
    def extract_glyphs(self, font_path: Path) -> list[GlyphInfo]:
        """
        Extract all glyph information from a font file.
        
        Args:
            font_path: Path to the TTF font file
            
        Returns:
            List of GlyphInfo objects for each glyph with Unicode mapping
            
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
            glyphs = []
            cmap = font.getBestCmap()
            
            if cmap is None:
                return glyphs
            
            for codepoint, glyph_name in cmap.items():
                glyph_index = font.getGlyphID(glyph_name)
                glyphs.append(GlyphInfo(
                    codepoint=codepoint,
                    glyph_name=glyph_name,
                    glyph_index=glyph_index
                ))
            
            return glyphs
        finally:
            font.close()

    
    def find_duplicates(self, fonts: list[Path]) -> DuplicateReport:
        """
        Analyze multiple fonts and find duplicate glyphs.
        
        A glyph is considered duplicate if its Unicode code point
        appears in more than one font.
        
        Args:
            fonts: List of paths to TTF font files
            
        Returns:
            DuplicateReport containing analysis results
            
        Raises:
            ValueError: If fonts list is empty
        """
        if not fonts:
            raise ValueError("At least one font file is required")
        
        # Parse all fonts and collect metadata
        font_metadata_list = []
        codepoint_to_fonts: dict[int, list[Path]] = {}
        
        for font_path in fonts:
            font_path = Path(font_path)
            metadata = self.parse_font(font_path)
            font_metadata_list.append(metadata)
            
            # Track which fonts contain each codepoint
            for codepoint in metadata.codepoints:
                if codepoint not in codepoint_to_fonts:
                    codepoint_to_fonts[codepoint] = []
                codepoint_to_fonts[codepoint].append(font_path)
        
        # Find duplicates (codepoints in more than one font)
        duplicates = {
            cp: font_list
            for cp, font_list in codepoint_to_fonts.items()
            if len(font_list) > 1
        }
        
        return DuplicateReport(
            fonts=font_metadata_list,
            duplicates=duplicates,
            total_duplicate_count=len(duplicates)
        )
    
    def _get_family_name(self, font: TTFont) -> str:
        """Extract family name from font's name table."""
        name_table = font.get('name')
        if name_table is None:
            return "Unknown"
        
        # Try to get family name (nameID 1) from name table
        # Priority: Windows platform (3), then Mac (1)
        for record in name_table.names:
            if record.nameID == 1:  # Family name
                try:
                    return record.toUnicode()
                except UnicodeDecodeError:
                    continue
        
        return "Unknown"
    
    def _get_codepoints(self, font: TTFont) -> set[int]:
        """Extract all Unicode codepoints from font's cmap table."""
        cmap = font.getBestCmap()
        if cmap is None:
            return set()
        return set(cmap.keys())
