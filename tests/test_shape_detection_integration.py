"""
Shape detection integration tests.

These tests validate the complete shape detection workflow including:
- Shape analysis with real font files
- SC/KR glyph shape difference detection
- Complete shape-aware deduplication flow
- Integration between ShapeAnalyzer, DeduplicationEngine, and Reporter

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from pathlib import Path
import pytest
from src.font_dedup.shape_analyzer import ShapeAnalyzer
from src.font_dedup.engine import DeduplicationEngine
from src.font_dedup.reporter import Reporter
from src.font_dedup.models import ShapeAwareDeduplicationResult


@pytest.fixture
def shape_analyzer():
    """Provide a ShapeAnalyzer instance."""
    return ShapeAnalyzer()


@pytest.fixture
def sc_kr_fonts():
    """Provide SC and KR font paths for shape variant testing."""
    fonts = [
        Path("fonts/NotoSansSC-Bold.ttf"),
        Path("fonts/NotoSansKR-Bold.ttf"),
    ]
    if not all(p.exists() for p in fonts):
        pytest.skip("SC/KR font files not found")
    return fonts


@pytest.fixture
def jp_kr_fonts():
    """Provide JP and KR font paths."""
    fonts = [
        Path("fonts/NotoSansJP-Bold.ttf"),
        Path("fonts/NotoSansKR-Bold.ttf"),
    ]
    if not all(p.exists() for p in fonts):
        pytest.skip("JP/KR font files not found")
    return fonts


def test_shape_analyzer_extract_outline(shape_analyzer, sc_kr_fonts):
    """
    Test shape analyzer can extract glyph outlines from real fonts.
    Validates: Requirements 8.1
    """
    # 测试提取一个常见的 CJK 字符
    codepoint = 0x4E00  # "一"
    
    outline = shape_analyzer.extract_glyph_outline(sc_kr_fonts[0], codepoint)
    
    assert outline is not None
    assert outline.codepoint == codepoint
    assert outline.font_path == sc_kr_fonts[0]
    assert outline.outline_data is not None
    assert len(outline.bounding_box) == 4


def test_shape_similarity_calculation(shape_analyzer, sc_kr_fonts):
    """
    Test shape similarity calculation between two glyphs.
    Validates: Requirements 8.2
    """
    codepoint = 0x4E00  # "一"
    
    outline1 = shape_analyzer.extract_glyph_outline(sc_kr_fonts[0], codepoint)
    outline2 = shape_analyzer.extract_glyph_outline(sc_kr_fonts[1], codepoint)
    
    similarity = shape_analyzer.calculate_similarity(outline1, outline2)
    
    # 相似度应该在 0.0 到 1.0 之间
    assert 0.0 <= similarity <= 1.0
    
    # 相同字形的相似度应该是 1.0
    same_similarity = shape_analyzer.calculate_similarity(outline1, outline1)
    assert same_similarity == 1.0


def test_sc_kr_shape_variant_detection(shape_analyzer, sc_kr_fonts):
    """
    Test detection of shape variants between SC and KR fonts.
    SC (Simplified Chinese) and KR (Korean) fonts often have different
    glyph shapes for the same Unicode codepoint due to regional variations.
    Validates: Requirements 8.3
    """
    # 使用一小部分 CJK 字符进行测试
    variant_report = shape_analyzer.find_shape_variants(
        sc_kr_fonts,
        similarity_threshold=1.0,
        codepoint_limit=10  # 限制分析数量以加快测试
    )
    
    assert variant_report is not None
    assert len(variant_report.fonts) == 2
    
    # SC 和 KR 字体应该有一些字形变体
    # 因为它们对相同的汉字有不同的设计
    total_variants = len(variant_report.shape_variants)
    total_duplicates = len(variant_report.unicode_duplicates)
    
    # 至少应该有一些分析结果
    assert total_variants + total_duplicates > 0


def test_shape_aware_deduplication_workflow(sc_kr_fonts):
    """
    Test complete shape-aware deduplication workflow.
    This validates the integration between ShapeAnalyzer and DeduplicationEngine.
    Validates: Requirements 8.4
    """
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 执行基于字形分析的去重
    result = engine.deduplicate_with_shape_analysis(
        sc_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E09)]  # 测试 10 个字符
    )
    
    # 验证返回正确的结果类型
    assert isinstance(result, ShapeAwareDeduplicationResult)
    
    # 验证结果包含所有必要的数据
    assert len(result.font_glyphs) == 2
    assert len(result.removed_glyphs) == 2
    assert isinstance(result.preserved_variants, list)
    assert isinstance(result.similarity_data, dict)
    
    # 验证字形变体被正确保护
    for variant in result.preserved_variants:
        # 变体应该在所有相关字体中都被保留
        for font_path in variant.fonts:
            assert variant.codepoint in result.font_glyphs[font_path]
            assert variant.codepoint not in result.removed_glyphs[font_path]


def test_shape_aware_deduplication_with_priority(jp_kr_fonts):
    """
    Test shape-aware deduplication respects font priority.
    Validates: Requirements 8.4
    """
    # JP 字体优先级更高
    engine = DeduplicationEngine(
        priority=[jp_kr_fonts[0]],
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    result = engine.deduplicate_with_shape_analysis(
        jp_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E04)]  # 5 个字符
    )
    
    # 高优先级字体应该保留更多字符
    jp_kept = len(result.font_glyphs[jp_kr_fonts[0]])
    kr_kept = len(result.font_glyphs[jp_kr_fonts[1]])
    
    jp_removed = len(result.removed_glyphs[jp_kr_fonts[0]])
    kr_removed = len(result.removed_glyphs[jp_kr_fonts[1]])
    
    # JP 移除的应该少于或等于 KR
    assert jp_removed <= kr_removed


def test_reporter_shape_variant_display(sc_kr_fonts):
    """
    Test that Reporter correctly distinguishes between Unicode duplicates
    and shape variants in the output.
    Validates: Requirements 8.5
    """
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    result = engine.deduplicate_with_shape_analysis(
        sc_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E09)]  # 10 个字符
    )
    
    reporter = Reporter()
    report = reporter.generate_deduplication_report(result)
    
    # 报告应该包含中文文本
    assert "字形变体" in report or "Unicode 重复" in report or "去重" in report
    
    # 报告应该包含技术关键词（英文）
    assert "glyph" in report.lower() or "unicode" in report.lower()
    
    # 如果有字形变体，报告应该明确区分显示
    if result.preserved_variants:
        assert "字形变体" in report
        # 验证变体信息被正确显示
        for variant in result.preserved_variants[:3]:  # 检查前几个
            # 码点应该以某种形式出现在报告中
            codepoint_str = f"U+{variant.codepoint:04X}"
            assert codepoint_str in report or hex(variant.codepoint) in report


def test_complete_shape_detection_pipeline(sc_kr_fonts):
    """
    Test the complete shape detection pipeline from analysis to reporting.
    This is an end-to-end integration test.
    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
    """
    # 步骤 1: 创建分析器和引擎
    shape_analyzer = ShapeAnalyzer()
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    reporter = Reporter()
    
    # 步骤 2: 分析字形变体
    variant_report = shape_analyzer.find_shape_variants(
        sc_kr_fonts,
        similarity_threshold=1.0,
        codepoint_limit=8  # 小范围测试
    )
    
    assert variant_report is not None
    
    # 步骤 3: 执行去重
    dedup_result = engine.deduplicate_with_shape_analysis(
        sc_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E07)]  # 8 个字符
    )
    
    assert isinstance(dedup_result, ShapeAwareDeduplicationResult)
    
    # 步骤 4: 生成报告
    analysis_report = reporter.generate_shape_variant_report(variant_report)
    dedup_report = reporter.generate_deduplication_report(dedup_result)
    
    # 验证报告内容
    assert len(analysis_report) > 0
    assert len(dedup_report) > 0
    
    # 报告应该使用中文
    assert any(char >= '\u4e00' and char <= '\u9fff' for char in analysis_report)
    assert any(char >= '\u4e00' and char <= '\u9fff' for char in dedup_report)


def test_shape_detection_with_unicode_ranges(jp_kr_fonts):
    """
    Test shape detection works correctly with Unicode range filtering.
    Validates: Requirements 8.4
    """
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 指定一个小范围
    unicode_range = [(0x4E00, 0x4E05)]  # 6 个字符
    
    result = engine.deduplicate_with_shape_analysis(
        jp_kr_fonts,
        unicode_ranges=unicode_range
    )
    
    # 验证范围外的字符被保留（不受去重影响）
    # 范围内的字符可能被去重
    for font_path in jp_kr_fonts:
        kept_codepoints = result.font_glyphs[font_path]
        removed_codepoints = result.removed_glyphs[font_path]
        
        # 范围外的字符应该都被保留
        for cp in kept_codepoints:
            if cp < 0x4E00 or cp > 0x4E05:
                # 范围外的字符不应该被移除
                assert cp not in removed_codepoints
        
        # 被移除的字符应该都在范围内
        for cp in removed_codepoints:
            assert 0x4E00 <= cp <= 0x4E05


def test_shape_detection_with_exclude_ranges(jp_kr_fonts):
    """
    Test that exclude ranges protect shape variants from deduplication.
    Validates: Requirements 8.4
    """
    engine = DeduplicationEngine(
        shape_analysis_enabled=True,
        similarity_threshold=1.0
    )
    
    # 排除前 3 个字符
    exclude_range = [(0x4E00, 0x4E02)]
    
    result = engine.deduplicate_with_shape_analysis(
        jp_kr_fonts,
        unicode_ranges=[(0x4E00, 0x4E05)],  # 6 个字符
        exclude_ranges=exclude_range
    )
    
    # 验证排除范围内的字符在所有字体中都被保留
    for codepoint in range(0x4E00, 0x4E03):
        for font_path in jp_kr_fonts:
            # 如果这个字符在字体中存在，它应该被保留
            if codepoint in result.font_glyphs[font_path] or codepoint in result.removed_glyphs[font_path]:
                assert codepoint in result.font_glyphs[font_path]
                assert codepoint not in result.removed_glyphs[font_path]
