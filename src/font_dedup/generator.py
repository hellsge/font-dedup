"""
Font Generator module for creating optimized TTF files.

This module provides the FontGenerator class which handles:
- Generating new TTF files with only specified glyphs using fonttools subsetting
- Updating cmap tables to reflect removed glyphs
- Batch processing multiple fonts based on deduplication results
"""

from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

from .models import DeduplicationResult


class FontGenerator:
    """
    Generator for creating optimized TTF font files.
    
    Uses fonttools subsetting functionality to create new font files
    containing only the specified glyphs.
    """
    
    def generate(
        self,
        source_font: Path,
        glyphs_to_keep: set[int],
        output_path: Path
    ) -> Path:
        """
        Generate a new font file containing only the specified glyphs.
        
        Uses fonttools subsetting to create a new TTF file with only
        the glyphs corresponding to the given Unicode code points.
        The cmap table is automatically updated to reflect the subset.
        
        Args:
            source_font: Path to the source TTF font file
            glyphs_to_keep: Set of Unicode code points to retain in the output
            output_path: Path where the output font will be written
            
        Returns:
            Path to the generated font file
            
        Raises:
            FileNotFoundError: If the source font doesn't exist
            ValueError: If the source is not a valid TTF font
            OSError: If the output directory cannot be created or written to
        """
        source_font = Path(source_font)
        output_path = Path(output_path)
        
        if not source_font.exists():
            raise FileNotFoundError(f"Source font not found: {source_font}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            font = TTFont(source_font)
        except Exception as e:
            raise ValueError(f"Invalid TTF font file: {source_font}") from e

        try:
            # Configure subsetter options
            options = Options()
            options.layout_features = ['*']  # Keep all layout features
            options.name_IDs = ['*']  # Keep all name records
            options.name_legacy = True  # Keep legacy name records
            options.name_languages = ['*']  # Keep all language name records
            options.notdef_outline = True  # Keep .notdef glyph outline
            options.recalc_bounds = True  # Recalculate font bounds
            options.recalc_timestamp = False  # Keep original timestamp
            options.drop_tables = []  # Don't drop any tables by default
            
            # Create subsetter and populate with codepoints to keep
            subsetter = Subsetter(options=options)
            
            # Convert codepoints to Unicode strings for subsetter
            # The subsetter expects text characters, not codepoint integers
            text_to_keep = ''.join(chr(cp) for cp in glyphs_to_keep if cp <= 0x10FFFF)
            subsetter.populate(text=text_to_keep)
            
            # Perform subsetting
            subsetter.subset(font)
            
            # Save the subsetted font
            font.save(output_path)
            
            return output_path
        finally:
            font.close()
    
    def batch_generate(
        self,
        dedup_result: DeduplicationResult,
        output_dir: Path,
        suffix: str = "_dedup"
    ) -> list[Path]:
        """
        Batch generate deduplicated font files.
        
        Processes all fonts in the deduplication result and generates
        new font files with only the glyphs marked for retention.
        
        Args:
            dedup_result: Result from DeduplicationEngine.deduplicate()
            output_dir: Directory where output fonts will be written
            suffix: Suffix to append to output filenames (default: "_dedup")
            
        Returns:
            List of paths to generated font files
            
        Raises:
            OSError: If the output directory cannot be created
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files: list[Path] = []
        
        for font_path, glyphs_to_keep in dedup_result.font_glyphs.items():
            font_path = Path(font_path)
            
            # Generate output filename with suffix
            stem = font_path.stem
            extension = font_path.suffix
            output_filename = f"{stem}{suffix}{extension}"
            output_path = output_dir / output_filename
            
            # Generate the font
            result_path = self.generate(font_path, glyphs_to_keep, output_path)
            generated_files.append(result_path)
        
        return generated_files
