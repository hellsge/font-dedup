"""
Tests for CLI module.

This module tests the command-line interface functionality.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from font_dedup.cli import main


def test_cli_help():
    """Test that CLI help message displays correctly"""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'TTF 字体 glyph 去重工具' in result.output


def test_cli_version():
    """Test that CLI version displays correctly"""
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_analyze_help():
    """Test that analyze command help displays correctly"""
    runner = CliRunner()
    result = runner.invoke(main, ['analyze', '--help'])
    assert result.exit_code == 0
    assert '分析字体文件中的重复 glyph' in result.output


def test_deduplicate_help():
    """Test that deduplicate command help displays correctly"""
    runner = CliRunner()
    result = runner.invoke(main, ['deduplicate', '--help'])
    assert result.exit_code == 0
    assert '执行字体 glyph 去重' in result.output


def test_analyze_missing_fonts():
    """Test that analyze command requires font arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ['analyze'])
    assert result.exit_code != 0
    assert 'Missing argument' in result.output


def test_deduplicate_missing_output_dir():
    """Test that deduplicate command requires output directory"""
    runner = CliRunner()
    # Create a temporary font file for testing
    with runner.isolated_filesystem():
        Path('test.ttf').touch()
        result = runner.invoke(main, ['deduplicate', 'test.ttf'])
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'output-dir' in result.output.lower()


def test_analyze_with_real_fonts():
    """Test analyze command with real font files"""
    runner = CliRunner()
    
    # 使用小型字体文件来加快测试速度
    font1 = Path('fonts/NotoSans-Light.ttf')
    font2 = Path('fonts/NotoSans-Regular.ttf')
    
    if font1.exists() and font2.exists():
        result = runner.invoke(main, ['analyze', str(font1), str(font2)])
        assert result.exit_code == 0
        assert '字体 Glyph 重复分析报告' in result.output
        assert '重复情况统计' in result.output


def test_deduplicate_with_real_fonts():
    """Test deduplicate command with real font files"""
    runner = CliRunner()
    
    # 使用最小的字体文件来加快测试速度
    font1 = Path('fonts/NotoSansTaiViet-Regular.ttf')  # 只有 68KB
    font2 = Path('fonts/NotoSans-Regular.ttf')
    
    if font1.exists() and font2.exists():
        # Don't use isolated filesystem since we need access to real fonts
        import tempfile
        import shutil
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'output'
            result = runner.invoke(main, [
                'deduplicate',
                str(font1.absolute()),
                str(font2.absolute()),
                '-o', str(output_dir)
            ])
            assert result.exit_code == 0
            assert '去重完成' in result.output
            assert output_dir.exists()
            assert len(list(output_dir.glob('*.ttf'))) == 2


def test_invalid_unicode_range():
    """Test that invalid Unicode range format is rejected"""
    runner = CliRunner()
    
    font1 = Path('fonts/NotoSansJP-Bold.ttf')
    
    if font1.exists():
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(main, [
                'deduplicate',
                str(font1.absolute()),
                '-o', tmpdir,
                '-r', 'invalid-range'
            ])
            assert result.exit_code != 0
            assert '错误' in result.output or 'Unicode 范围' in result.output
