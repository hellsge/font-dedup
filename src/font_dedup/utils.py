"""
工具函数模块，用于集成 Reporter 与其他组件。

本模块提供便捷函数，将 Reporter 与 FontAnalyzer、DeduplicationEngine、
FontGenerator 和 Validator 集成使用。
"""

from pathlib import Path
from typing import Optional

from .analyzer import FontAnalyzer
from .engine import DeduplicationEngine
from .generator import FontGenerator
from .validator import Validator
from .reporter import Reporter
from .models import DeduplicationResult


def analyze_and_report(
    font_paths: list[Path],
    shape_analysis_enabled: bool = False,
    similarity_threshold: float = 1.0
) -> str:
    """
    分析字体并生成中文报告。
    
    Args:
        font_paths: 要分析的字体文件路径列表
        shape_analysis_enabled: 是否启用字形检测模式
        similarity_threshold: 字形相似度阈值 (0.0-1.0)
        
    Returns:
        格式化的中文分析报告
        
    Raises:
        ValueError: 如果字体列表为空
        FileNotFoundError: 如果字体文件不存在
    """
    analyzer = FontAnalyzer()
    reporter = Reporter()
    
    try:
        if shape_analysis_enabled:
            # 使用字形检测模式
            from .shape_analyzer import ShapeAnalyzer
            shape_analyzer = ShapeAnalyzer()
            shape_variant_report = shape_analyzer.find_shape_variants(
                fonts=font_paths,
                similarity_threshold=similarity_threshold
            )
            return reporter.generate_shape_variant_report(shape_variant_report)
        else:
            # 使用基本分析模式
            duplicate_report = analyzer.find_duplicates(font_paths)
            return reporter.generate_analysis_report(duplicate_report)
    except Exception as e:
        return reporter.format_error(e)


def deduplicate_and_report(
    font_paths: list[Path],
    priority: Optional[list[Path]] = None,
    unicode_ranges: Optional[list[tuple[int, int]]] = None,
    exclude_ranges: Optional[list[tuple[int, int]]] = None,
    shape_analysis_enabled: bool = False,
    similarity_threshold: float = 1.0
) -> tuple[DeduplicationResult, str]:
    """
    执行去重并生成中文报告。
    
    Args:
        font_paths: 要处理的字体文件路径列表
        priority: 可选的优先级顺序
        unicode_ranges: 可选的 Unicode 范围
        exclude_ranges: 可选的排除范围
        shape_analysis_enabled: 是否启用字形检测模式
        similarity_threshold: 字形相似度阈值 (0.0-1.0)
        
    Returns:
        元组 (去重结果, 中文报告)
        
    Raises:
        ValueError: 如果字体列表为空
        FileNotFoundError: 如果字体文件不存在
    """
    engine = DeduplicationEngine(
        priority=priority,
        shape_analysis_enabled=shape_analysis_enabled,
        similarity_threshold=similarity_threshold
    )
    reporter = Reporter()
    
    try:
        if shape_analysis_enabled:
            # 使用字形检测模式
            result = engine.deduplicate_with_shape_analysis(
                fonts=font_paths,
                unicode_ranges=unicode_ranges,
                exclude_ranges=exclude_ranges
            )
        else:
            # 使用基本去重模式
            result = engine.deduplicate(
                fonts=font_paths,
                unicode_ranges=unicode_ranges,
                exclude_ranges=exclude_ranges
            )
        
        # generate_deduplication_report 可以处理两种类型的结果
        report = reporter.generate_deduplication_report(result)
        return result, report
    except Exception as e:
        error_msg = reporter.format_error(e)
        raise RuntimeError(error_msg) from e


def generate_and_validate(
    dedup_result: DeduplicationResult,
    output_dir: Path,
    suffix: str = "_dedup"
) -> str:
    """
    生成字体文件并验证，返回中文报告。
    
    Args:
        dedup_result: 去重结果
        output_dir: 输出目录
        suffix: 文件名后缀
        
    Returns:
        格式化的中文验证报告
        
    Raises:
        OSError: 如果无法创建输出目录或写入文件
    """
    generator = FontGenerator()
    validator = Validator()
    reporter = Reporter()
    
    try:
        # 生成字体文件
        generated_files = generator.batch_generate(
            dedup_result=dedup_result,
            output_dir=output_dir,
            suffix=suffix
        )
        
        # 验证每个生成的文件
        validation_reports = []
        all_valid = True
        
        for font_path in generated_files:
            # 获取对应的保留 glyph 集合
            original_path = None
            for orig_path in dedup_result.font_glyphs.keys():
                if orig_path.stem in font_path.stem:
                    original_path = orig_path
                    break
            
            if original_path:
                expected_codepoints = dedup_result.font_glyphs[original_path]
                validation_result = validator.validate_glyphs(font_path, expected_codepoints)
            else:
                validation_result = validator.validate_ttf(font_path)
            
            if not validation_result.is_valid:
                all_valid = False
            
            validation_reports.append(
                f"\n文件: {font_path.name}\n" +
                reporter.format_validation_result(validation_result)
            )
        
        # 汇总报告
        summary = "=" * 60 + "\n"
        summary += "字体生成与验证报告\n"
        summary += "=" * 60 + "\n\n"
        summary += f"生成的字体文件数量: {len(generated_files)}\n"
        summary += f"输出目录: {output_dir}\n"
        summary += f"验证状态: {'全部通过' if all_valid else '存在错误'}\n"
        summary += "\n" + "-" * 60 + "\n"
        summary += "详细验证结果:"
        summary += "\n".join(validation_reports)
        summary += "\n" + "=" * 60
        
        return summary
        
    except Exception as e:
        return reporter.format_error(e)


def get_file_size_report(original_path: Path, new_path: Path) -> str:
    """
    获取文件大小对比报告。
    
    Args:
        original_path: 原始文件路径
        new_path: 新文件路径
        
    Returns:
        格式化的文件大小对比信息
    """
    reporter = Reporter()
    
    try:
        original_size = original_path.stat().st_size
        new_size = new_path.stat().st_size
        return reporter.format_file_size_info(original_size, new_size)
    except Exception as e:
        return reporter.format_error(e)
