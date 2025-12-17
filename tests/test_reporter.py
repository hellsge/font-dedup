"""
Tests for the Reporter module.

This module tests the Chinese output formatting functionality
of the Reporter class.
"""

from pathlib import Path
from src.font_dedup.reporter import Reporter
from src.font_dedup.models import (
    DuplicateReport,
    DeduplicationResult,
    ValidationResult,
    FontMetadata,
)


def test_generate_analysis_report_basic():
    """Test basic analysis report generation with Chinese output."""
    reporter = Reporter()
    
    # Create sample data
    font1 = FontMetadata(
        path=Path("font1.ttf"),
        family_name="Test Font 1",
        glyph_count=100,
        codepoints={0x41, 0x42, 0x43}  # A, B, C
    )
    
    font2 = FontMetadata(
        path=Path("font2.ttf"),
        family_name="Test Font 2",
        glyph_count=150,
        codepoints={0x42, 0x43, 0x44}  # B, C, D
    )
    
    duplicate_report = DuplicateReport(
        fonts=[font1, font2],
        duplicates={
            0x42: [Path("font1.ttf"), Path("font2.ttf")],
            0x43: [Path("font1.ttf"), Path("font2.ttf")],
        },
        total_duplicate_count=2
    )
    
    report = reporter.generate_analysis_report(duplicate_report)
    
    # Verify Chinese text is present
    assert "字体 Glyph 重复分析报告" in report
    assert "分析的字体文件数量" in report
    assert "发现的重复 Code Point 总数" in report
    
    # Verify technical keywords are in English
    assert "Glyph" in report
    assert "Code Point" in report or "code point" in report
    assert "Unicode" in report
    
    # Verify data is correct
    assert "2" in report  # 2 fonts
    assert "Test Font 1" in report
    assert "Test Font 2" in report


def test_generate_deduplication_report():
    """Test deduplication report generation with Chinese output."""
    reporter = Reporter()
    
    result = DeduplicationResult(
        font_glyphs={
            Path("font1.ttf"): {0x41, 0x42, 0x43},
            Path("font2.ttf"): {0x44, 0x45},
        },
        removed_glyphs={
            Path("font1.ttf"): set(),
            Path("font2.ttf"): {0x42, 0x43},
        }
    )
    
    report = reporter.generate_deduplication_report(result)
    
    # Verify Chinese text
    assert "字体 Glyph 去重结果报告" in report
    assert "处理的字体文件数量" in report
    assert "保留的 Glyph 总数" in report
    assert "移除的 Glyph 总数" in report
    
    # Verify technical keywords in English
    assert "Glyph" in report
    assert "Code Point" in report or "code point" in report
    
    # Verify counts
    assert "5" in report  # 5 kept total
    assert "2" in report  # 2 removed total


def test_format_error_file_not_found():
    """Test error formatting for FileNotFoundError."""
    reporter = Reporter()
    
    error = FileNotFoundError("test.ttf")
    formatted = reporter.format_error(error)
    
    # Should contain Chinese error description
    assert "错误" in formatted
    assert "文件未找到" in formatted
    assert "test.ttf" in formatted


def test_format_error_value_error():
    """Test error formatting for ValueError."""
    reporter = Reporter()
    
    error = ValueError("Invalid parameter")
    formatted = reporter.format_error(error)
    
    # Should contain Chinese error description
    assert "错误" in formatted
    assert "参数值无效" in formatted
    assert "Invalid parameter" in formatted


def test_format_validation_result_valid():
    """Test validation result formatting for valid result."""
    reporter = Reporter()
    
    result = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=[]
    )
    
    formatted = reporter.format_validation_result(result)
    
    # Should show success in Chinese
    assert "验证通过" in formatted


def test_format_validation_result_with_errors():
    """Test validation result formatting with errors."""
    reporter = Reporter()
    
    result = ValidationResult(
        is_valid=False,
        errors=["缺少必需的 TTF table: cmap"],
        warnings=["cmap table 为空"]
    )
    
    formatted = reporter.format_validation_result(result)
    
    # Should show failure and errors in Chinese
    assert "验证失败" in formatted
    assert "错误" in formatted
    assert "警告" in formatted
    assert "TTF" in formatted  # Technical keyword preserved
    assert "cmap" in formatted  # Technical keyword preserved


def test_format_file_size_info_reduction():
    """Test file size formatting with size reduction."""
    reporter = Reporter()
    
    formatted = reporter.format_file_size_info(1024 * 1024, 512 * 1024)
    
    # Should show Chinese text
    assert "文件大小" in formatted
    assert "减少" in formatted
    assert "MB" in formatted or "KB" in formatted


def test_format_file_size_info_no_change():
    """Test file size formatting with no change."""
    reporter = Reporter()
    
    formatted = reporter.format_file_size_info(1024, 1024)
    
    # Should show Chinese text
    assert "文件大小" in formatted
    assert "无变化" in formatted


def test_format_progress():
    """Test progress formatting."""
    reporter = Reporter()
    
    formatted = reporter.format_progress(5, 10, "处理字体")
    
    # Should show Chinese description and progress
    assert "处理字体" in formatted
    assert "[5/10]" in formatted
    assert "50" in formatted  # 50%


def test_analysis_report_with_many_duplicates():
    """Test analysis report with many duplicates shows truncation."""
    reporter = Reporter()
    
    # Create many duplicate codepoints
    duplicates = {
        i: [Path("font1.ttf"), Path("font2.ttf")]
        for i in range(0x41, 0x41 + 30)  # 30 duplicates
    }
    
    font1 = FontMetadata(
        path=Path("font1.ttf"),
        family_name="Font 1",
        glyph_count=100,
        codepoints=set(range(0x41, 0x41 + 30))
    )
    
    duplicate_report = DuplicateReport(
        fonts=[font1],
        duplicates=duplicates,
        total_duplicate_count=30
    )
    
    report = reporter.generate_analysis_report(duplicate_report)
    
    # Should show truncation message in Chinese
    assert "还有" in report or "示例" in report
    assert "30" in report


def test_deduplication_report_with_many_removed():
    """Test deduplication report with many removed glyphs shows truncation."""
    reporter = Reporter()
    
    # Create many removed glyphs
    removed = set(range(0x41, 0x41 + 20))  # 20 removed
    
    result = DeduplicationResult(
        font_glyphs={Path("font1.ttf"): {0x30}},
        removed_glyphs={Path("font1.ttf"): removed}
    )
    
    report = reporter.generate_deduplication_report(result)
    
    # Should show truncation
    assert "示例" in report or "共" in report
    assert "20" in report
