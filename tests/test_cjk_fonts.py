"""
CJK font tests - marked as slow tests.

These tests use large CJK font files and are important for validating
shape analysis with real-world CJK fonts, but are slower to run.

Run these tests with: pytest -m cjk
Skip these tests with: pytest -m "not cjk"
"""

from pathlib import Path
import pytest
from src.font_dedup.engine import DeduplicationEngine
from src.font_dedup.models import ShapeAwareDeduplicationResult


# Fixtures to cache font paths
@pytest.fixture(scope="module")
def cjk_jp_kr_fonts():
    """Provide JP and KR font paths."""
    fonts = [
        Path("fonts/NotoSansJP-Bold.ttf"),
        Path("fonts/NotoSansKR-Bold.ttf"),
    ]
    if not all(p.exists() for p in fonts):
        pytest.skip("CJK font files not found")
    return fonts


@pytest.fixture(scope="module")
def cjk_three_fonts():
    """Provide JP, KR, and SC font paths."""
    fonts = [
        Path("fonts/NotoSansJP-Bold.ttf"),
        Path("fonts/NotoSansKR-Bold.ttf"),
        Path("fonts/NotoSansSC-Bold.ttf"),
    ]
    if not all(p.exists() for p in fonts):
        pytest.skip("CJK font files not found")
    return fonts


@pytest.mark.cjk
@pytest.mark.slow
def test_cjk_shape_analysis_jp_kr(cjk_jp_kr_fonts):
    """Test shape analysis with Japanese and Korean CJK fonts."""
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 减少到 8 个字符，足以验证功能
    result = engine.deduplicate_with_shape_analysis(
        cjk_jp_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E07)]  # 8 个 CJK 字符
    )
    
    assert isinstance(result, ShapeAwareDeduplicationResult)
    assert len(result.font_glyphs) == 2
    assert len(result.removed_glyphs) == 2
    
    # 验证字形变体被正确识别
    # JP 和 KR 字体在很多 CJK 字符上有不同的字形
    if result.preserved_variants:
        for variant in result.preserved_variants:
            # 变体应该在两个字体中都被保留
            for font_path in variant.fonts:
                assert variant.codepoint in result.font_glyphs[font_path]


@pytest.mark.cjk
@pytest.mark.slow
def test_cjk_shape_analysis_three_fonts(cjk_three_fonts):
    """Test shape analysis with three CJK fonts (JP, KR, SC)."""
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 减少到 5 个字符，三个字体的组合已经足够复杂
    result = engine.deduplicate_with_shape_analysis(
        cjk_three_fonts,
        unicode_ranges=[(0x4E00, 0x4E04)]  # 5 个 CJK 字符
    )
    
    assert isinstance(result, ShapeAwareDeduplicationResult)
    assert len(result.font_glyphs) == 3
    assert len(result.removed_glyphs) == 3
    
    # 验证相似度数据被正确收集
    assert isinstance(result.similarity_data, dict)


@pytest.mark.cjk
@pytest.mark.slow
def test_cjk_deduplicate_with_priority(cjk_jp_kr_fonts):
    """Test CJK font deduplication with priority order."""
    # JP 优先级更高
    engine = DeduplicationEngine(
        priority=[cjk_jp_kr_fonts[0]],  # JP 优先
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 减少到 4 个字符
    result = engine.deduplicate_with_shape_analysis(
        cjk_jp_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E03)]  # 4 个字符
    )
    
    # JP 字体应该保留所有字符（高优先级）
    jp_removed = result.removed_glyphs[cjk_jp_kr_fonts[0]]
    kr_removed = result.removed_glyphs[cjk_jp_kr_fonts[1]]
    
    # JP 移除的字符应该少于或等于 KR
    assert len(jp_removed) <= len(kr_removed)


@pytest.mark.cjk
@pytest.mark.slow
def test_cjk_exclude_ranges(cjk_jp_kr_fonts):
    """Test that CJK exclude ranges work correctly."""
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 排除前 2 个字符
    exclude_range = [(0x4E00, 0x4E01)]
    
    # 减少到 6 个字符
    result = engine.deduplicate_with_shape_analysis(
        cjk_jp_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E05)],  # 6 个字符
        exclude_ranges=exclude_range
    )
    
    # 验证排除范围内的字符在所有字体中都被保留
    for codepoint in range(0x4E00, 0x4E02):
        for font_path in cjk_jp_kr_fonts:
            if codepoint in result.font_glyphs[font_path] or codepoint in result.removed_glyphs[font_path]:
                assert codepoint in result.font_glyphs[font_path]
                assert codepoint not in result.removed_glyphs[font_path]


@pytest.mark.cjk
@pytest.mark.slow
def test_cjk_larger_range_analysis(cjk_jp_kr_fonts):
    """Test CJK font analysis with a larger range (slower test)."""
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 减少到 32 个字符，仍然足以验证大范围处理
    # 从 256 个减少到 32 个，性能提升约 8 倍
    result = engine.deduplicate_with_shape_analysis(
        cjk_jp_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E1F)]  # 32 个字符
    )
    
    assert isinstance(result, ShapeAwareDeduplicationResult)
    
    # 验证结果结构
    assert len(result.font_glyphs) == 2
    assert len(result.removed_glyphs) == 2
    
    # 如果发现字形变体，验证它们被正确处理
    # 注意：不强制要求找到变体，因为这取决于具体的字体和字符范围
    if result.preserved_variants:
        for variant in result.preserved_variants:
            # 变体应该在所有相关字体中都被保留
            for font_path in variant.fonts:
                assert variant.codepoint in result.font_glyphs[font_path]
                assert variant.codepoint not in result.removed_glyphs[font_path]
    
    # 验证统计信息
    total_preserved = sum(len(glyphs) for glyphs in result.font_glyphs.values())
    total_removed = sum(len(glyphs) for glyphs in result.removed_glyphs.values())
    
    assert total_preserved > 0
    assert total_removed >= 0  # 可能有些字符被去重
