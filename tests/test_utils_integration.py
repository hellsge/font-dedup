"""
Integration tests for utils module with Reporter.

Tests the integration of Reporter with other components through
the utility functions.
"""

from pathlib import Path
from src.font_dedup.utils import (
    analyze_and_report,
    deduplicate_and_report,
    get_file_size_report,
)


def test_analyze_and_report_with_real_fonts():
    """Test analyze_and_report with actual font files."""
    # 使用小型字体文件来加快测试速度
    font_paths = [
        Path("fonts/NotoSans-Light.ttf"),
        Path("fonts/NotoSans-Regular.ttf"),
    ]
    
    # Check if fonts exist
    if not all(p.exists() for p in font_paths):
        # Skip if fonts don't exist
        return
    
    report = analyze_and_report(font_paths)
    
    # Verify Chinese output
    assert "字体 Glyph 重复分析报告" in report
    assert "分析的字体文件数量" in report
    
    # Verify technical keywords in English
    assert "Glyph" in report
    assert "Code Point" in report or "code point" in report


def test_deduplicate_and_report_with_real_fonts():
    """Test deduplicate_and_report with actual font files."""
    # 使用小型字体文件来加快测试速度
    font_paths = [
        Path("fonts/NotoSans-Light.ttf"),
        Path("fonts/NotoSans-Regular.ttf"),
    ]
    
    # Check if fonts exist
    if not all(p.exists() for p in font_paths):
        # Skip if fonts don't exist
        return
    
    result, report = deduplicate_and_report(font_paths)
    
    # Verify result structure
    assert len(result.font_glyphs) == 2
    assert len(result.removed_glyphs) == 2
    
    # Verify Chinese output
    assert "字体 Glyph 去重结果报告" in report
    assert "处理的字体文件数量" in report
    
    # Verify technical keywords in English
    assert "Glyph" in report
    assert "Code Point" in report or "code point" in report


def test_get_file_size_report_with_real_files():
    """Test get_file_size_report with actual files."""
    # 使用小型字体文件
    font_path = Path("fonts/NotoSansTaiViet-Regular.ttf")
    
    if not font_path.exists():
        # Skip if font doesn't exist
        return
    
    # Compare with itself for testing
    report = get_file_size_report(font_path, font_path)
    
    # Verify Chinese output
    assert "文件大小" in report
    assert "无变化" in report


def test_analyze_and_report_error_handling():
    """Test error handling in analyze_and_report."""
    # Use non-existent files
    font_paths = [
        Path("nonexistent1.ttf"),
        Path("nonexistent2.ttf"),
    ]
    
    report = analyze_and_report(font_paths)
    
    # Should return error message in Chinese
    assert "错误" in report
    assert "文件未找到" in report or "文件" in report
