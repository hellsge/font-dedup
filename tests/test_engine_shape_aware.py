"""
Tests for shape-aware deduplication in DeduplicationEngine.

Tests the new shape analysis functionality added to the engine.
"""

from pathlib import Path
import pytest
from src.font_dedup.engine import DeduplicationEngine
from src.font_dedup.models import ShapeAwareDeduplicationResult


def test_engine_initialization_with_shape_analysis():
    """Test that engine can be initialized with shape analysis enabled."""
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    assert engine._shape_analysis_enabled is True
    assert engine._similarity_threshold == 1.0
    assert engine._shape_analyzer is not None


def test_engine_initialization_without_shape_analysis():
    """Test that engine initializes without shape analyzer when disabled."""
    engine = DeduplicationEngine(
        shape_analysis_enabled=False
    )
    
    assert engine._shape_analysis_enabled is False
    assert engine._shape_analyzer is None


def test_deduplicate_with_shape_analysis_requires_enabled():
    """Test that deduplicate_with_shape_analysis raises error when not enabled."""
    engine = DeduplicationEngine(shape_analysis_enabled=False)
    
    font_paths = [
        Path("fonts/NotoSansJP-Bold.ttf"),
        Path("fonts/NotoSansKR-Bold.ttf"),
    ]
    
    with pytest.raises(ValueError, match="Shape analysis is not enabled"):
        engine.deduplicate_with_shape_analysis(font_paths)


def test_deduplicate_with_shape_analysis_empty_fonts():
    """Test that deduplicate_with_shape_analysis raises error with empty fonts list."""
    engine = DeduplicationEngine(shape_analysis_enabled=True)
    
    with pytest.raises(ValueError, match="At least one font file is required"):
        engine.deduplicate_with_shape_analysis([])


def test_deduplicate_with_shape_analysis_with_real_fonts():
    """Test shape-aware deduplication with actual font files."""
    # 使用小型字体文件来加快测试速度
    font_paths = [
        Path("fonts/NotoSans-Light.ttf"),
        Path("fonts/NotoSans-Regular.ttf"),
    ]
    
    # Check if fonts exist
    if not all(p.exists() for p in font_paths):
        pytest.skip("Font files not found")
    
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0  # 使用默认阈值 1.0，性能更好
    )
    
    # 使用 ASCII 范围，这些小型字体都包含这些字符
    result = engine.deduplicate_with_shape_analysis(
        font_paths,
        unicode_ranges=[(0x0041, 0x005A)]  # A-Z，26 个字符
    )
    
    # Verify result type
    assert isinstance(result, ShapeAwareDeduplicationResult)
    
    # Verify result structure
    assert len(result.font_glyphs) == 2  # 2 fonts
    assert len(result.removed_glyphs) == 2  # 2 fonts
    assert isinstance(result.preserved_variants, list)
    assert isinstance(result.similarity_data, dict)
    
    # Verify all fonts are in the result
    for font_path in font_paths:
        assert font_path in result.font_glyphs
        assert font_path in result.removed_glyphs


def test_deduplicate_with_shape_analysis_preserves_variants():
    """Test that shape variants are preserved in shape-aware deduplication."""
    # 使用小型字体文件来加快测试速度
    font_paths = [
        Path("fonts/NotoSans-Light.ttf"),
        Path("fonts/NotoSans-Regular.ttf"),
    ]
    
    # Check if fonts exist
    if not all(p.exists() for p in font_paths):
        pytest.skip("Font files not found")
    
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0  # 使用默认阈值 1.0，性能更好
    )
    
    # 测试小写字母，Light 和 Regular 可能有细微差异
    result = engine.deduplicate_with_shape_analysis(
        font_paths,
        unicode_ranges=[(0x0061, 0x007A)]  # a-z，26 个字符
    )
    
    # If there are preserved variants, verify they're in the result
    if result.preserved_variants:
        for variant in result.preserved_variants:
            # Each variant should have the codepoint preserved in all fonts
            for font_path in variant.fonts:
                assert variant.codepoint in result.font_glyphs[font_path]
                assert variant.codepoint not in result.removed_glyphs[font_path]


def test_deduplicate_with_shape_analysis_respects_exclude_ranges():
    """Test that exclude ranges are respected in shape-aware deduplication."""
    # 使用小型字体文件来加快测试速度
    font_paths = [
        Path("fonts/NotoSans-Light.ttf"),
        Path("fonts/NotoSans-Regular.ttf"),
    ]
    
    # Check if fonts exist
    if not all(p.exists() for p in font_paths):
        pytest.skip("Font files not found")
    
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0  # 使用默认阈值 1.0，性能更好
    )
    
    # 排除前 5 个大写字母
    exclude_range = [(0x0041, 0x0045)]  # A-E
    
    result = engine.deduplicate_with_shape_analysis(
        font_paths,
        unicode_ranges=[(0x0041, 0x004A)],  # A-J，10 个字符
        exclude_ranges=exclude_range
    )
    
    # Verify that codepoints in exclude range are preserved in all fonts
    for codepoint in range(0x0041, 0x0046):
        for font_path in font_paths:
            # If the font has this codepoint, it should be preserved
            if codepoint in result.font_glyphs[font_path] or codepoint in result.removed_glyphs[font_path]:
                assert codepoint in result.font_glyphs[font_path]
                assert codepoint not in result.removed_glyphs[font_path]
