"""
CLI 命令行接口模块。

提供 font-dedup 命令行工具，支持字体分析和去重操作。
"""

import sys
from pathlib import Path
import click

from .utils import analyze_and_report, deduplicate_and_report, generate_and_validate


# 自定义错误处理
class FontDedupError(click.ClickException):
    """自定义异常类，用于显示中文错误信息"""
    
    def __init__(self, message):
        super().__init__(message)
    
    def show(self, file=None):
        """显示错误信息"""
        if file is None:
            file = click.get_text_stream('stderr')
        click.secho(f'错误: {self.format_message()}', fg='red', file=file)


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="font-dedup")
def main(ctx):
    """
    TTF 字体 glyph 去重工具
    
    分析多个字体文件中的重复 glyph，并根据优先级生成优化后的字体文件。
    
    使用示例:
    
      # 分析字体文件
      font-dedup analyze font1.ttf font2.ttf
    
      # 执行去重
      font-dedup deduplicate font1.ttf font2.ttf --output-dir ./output
    """
    # 如果没有提供子命令，显示帮助信息
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument('fonts', nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    '--shape-analysis',
    is_flag=True,
    help='启用字形检测模式，分析相同 Unicode 码点的字形差异'
)
@click.option(
    '--similarity-threshold',
    type=float,
    default=1.0,
    help='字形相似度阈值 (0.0-1.0)，低于此值视为字形变体（默认: 1.0）'
)
def analyze(fonts, shape_analysis, similarity_threshold):
    """
    分析字体文件中的重复 glyph
    
    仅输出分析结果，不修改任何文件。
    
    FONTS: 要分析的字体文件路径（可指定多个）
    
    使用示例:
    
      # 基本分析
      font-dedup analyze font1.ttf font2.ttf font3.ttf
      
      # 启用字形检测
      font-dedup analyze font1.ttf font2.ttf --shape-analysis
      
      # 自定义相似度阈值
      font-dedup analyze font1.ttf font2.ttf --shape-analysis --similarity-threshold 0.9
    """
    # 验证至少提供了一个字体文件
    if not fonts:
        raise FontDedupError("请至少提供一个字体文件")
    
    # 验证所有文件都是 TTF 格式
    for font in fonts:
        font_path = Path(font)
        if font_path.suffix.lower() not in ['.ttf', '.otf']:
            raise FontDedupError(f"不支持的字体格式: {font_path.name}，仅支持 TTF 和 OTF 格式")
    
    # 验证相似度阈值
    if shape_analysis and not (0.0 <= similarity_threshold <= 1.0):
        raise FontDedupError(f"相似度阈值必须在 0.0 到 1.0 之间，当前值: {similarity_threshold}")
    
    try:
        # 转换为 Path 对象列表
        font_paths = [Path(f) for f in fonts]
        
        # 执行分析并生成报告
        report = analyze_and_report(
            font_paths,
            shape_analysis_enabled=shape_analysis,
            similarity_threshold=similarity_threshold
        )
        
        # 输出报告
        click.echo(report)
        
    except FileNotFoundError as e:
        raise FontDedupError(f"文件不存在: {str(e)}")
    except ValueError as e:
        raise FontDedupError(f"参数错误: {str(e)}")
    except Exception as e:
        raise FontDedupError(f"分析失败: {str(e)}")


@main.command()
@click.argument('fonts', nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    required=True,
    help='输出目录路径'
)
@click.option(
    '--priority', '-p',
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help='字体优先级顺序（可多次指定，先指定的优先级更高）'
)
@click.option(
    '--range', '-r',
    'unicode_ranges',
    multiple=True,
    help='Unicode 范围，格式: START-END (十六进制)，例如: 0x4E00-0x9FFF'
)
@click.option(
    '--exclude', '-e',
    'exclude_ranges',
    multiple=True,
    help='排除范围，格式: START-END (十六进制)，例如: 0x0020-0x007F'
)
@click.option(
    '--suffix', '-s',
    default='_dedup',
    help='输出文件名后缀（默认: _dedup）'
)
@click.option(
    '--shape-analysis',
    is_flag=True,
    help='启用字形检测模式，保护相同 Unicode 码点的不同字形'
)
@click.option(
    '--similarity-threshold',
    type=float,
    default=1.0,
    help='字形相似度阈值 (0.0-1.0)，低于此值视为字形变体（默认: 1.0）'
)
def deduplicate(fonts, output_dir, priority, unicode_ranges, exclude_ranges, suffix, shape_analysis, similarity_threshold):
    """
    执行字体 glyph 去重
    
    根据优先级顺序，从低优先级字体中移除重复的 glyph，生成优化后的字体文件。
    
    FONTS: 要处理的字体文件路径（可指定多个）
    
    使用示例:
    
      # 基本去重
      font-dedup deduplicate font1.ttf font2.ttf -o ./output
    
      # 指定优先级
      font-dedup deduplicate font1.ttf font2.ttf -o ./output -p font1.ttf
    
      # 指定 Unicode 范围（仅处理中文）
      font-dedup deduplicate font1.ttf font2.ttf -o ./output -r 0x4E00-0x9FFF
    
      # 排除 ASCII 范围
      font-dedup deduplicate font1.ttf font2.ttf -o ./output -e 0x0020-0x007F
      
      # 启用字形检测（保护字形变体）
      font-dedup deduplicate font1.ttf font2.ttf -o ./output --shape-analysis
      
      # 自定义相似度阈值
      font-dedup deduplicate font1.ttf font2.ttf -o ./output --shape-analysis --similarity-threshold 0.9
    """
    # 验证至少提供了一个字体文件
    if not fonts:
        raise FontDedupError("请至少提供一个字体文件")
    
    # 验证所有文件都是 TTF 格式
    for font in fonts:
        font_path = Path(font)
        if font_path.suffix.lower() not in ['.ttf', '.otf']:
            raise FontDedupError(f"不支持的字体格式: {font_path.name}，仅支持 TTF 和 OTF 格式")
    
    # 转换为 Path 对象列表
    font_paths = [Path(f) for f in fonts]
    
    # 处理优先级参数
    priority_list = None
    if priority:
        priority_list = [Path(p) for p in priority]
        # 验证优先级列表中的字体是否在输入列表中
        for p in priority_list:
            if p not in font_paths:
                raise FontDedupError(f"优先级中指定的字体 {p} 不在输入字体列表中")
    
    # 解析 Unicode 范围
    parsed_unicode_ranges = None
    if unicode_ranges:
        parsed_unicode_ranges = []
        for range_str in unicode_ranges:
            try:
                if '-' not in range_str:
                    raise ValueError("缺少分隔符 '-'")
                start_str, end_str = range_str.split('-', 1)
                start = int(start_str, 16) if start_str.startswith('0x') else int(start_str)
                end = int(end_str, 16) if end_str.startswith('0x') else int(end_str)
                if start > end:
                    raise FontDedupError(f"Unicode 范围无效 {range_str}，起始值大于结束值")
                if start < 0 or end > 0x10FFFF:
                    raise FontDedupError(f"Unicode 范围无效 {range_str}，值必须在 0x0 到 0x10FFFF 之间")
                parsed_unicode_ranges.append((start, end))
            except ValueError as e:
                raise FontDedupError(f"Unicode 范围格式无效 {range_str}，应为 START-END 格式（例如: 0x4E00-0x9FFF）")
    
    # 解析排除范围
    parsed_exclude_ranges = None
    if exclude_ranges:
        parsed_exclude_ranges = []
        for range_str in exclude_ranges:
            try:
                if '-' not in range_str:
                    raise ValueError("缺少分隔符 '-'")
                start_str, end_str = range_str.split('-', 1)
                start = int(start_str, 16) if start_str.startswith('0x') else int(start_str)
                end = int(end_str, 16) if end_str.startswith('0x') else int(end_str)
                if start > end:
                    raise FontDedupError(f"排除范围无效 {range_str}，起始值大于结束值")
                if start < 0 or end > 0x10FFFF:
                    raise FontDedupError(f"排除范围无效 {range_str}，值必须在 0x0 到 0x10FFFF 之间")
                parsed_exclude_ranges.append((start, end))
            except ValueError as e:
                raise FontDedupError(f"排除范围格式无效 {range_str}，应为 START-END 格式（例如: 0x0020-0x007F）")
    
    # 验证相似度阈值
    if shape_analysis and not (0.0 <= similarity_threshold <= 1.0):
        raise FontDedupError(f"相似度阈值必须在 0.0 到 1.0 之间，当前值: {similarity_threshold}")
    
    # 验证输出目录
    output_dir = Path(output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        raise FontDedupError(f"输出路径已存在且不是目录: {output_dir}")
    
    try:
        # 执行去重
        click.echo("正在执行去重分析...")
        dedup_result, dedup_report = deduplicate_and_report(
            font_paths=font_paths,
            priority=priority_list,
            unicode_ranges=parsed_unicode_ranges,
            exclude_ranges=parsed_exclude_ranges,
            shape_analysis_enabled=shape_analysis,
            similarity_threshold=similarity_threshold
        )
        
        # 输出去重报告
        click.echo(dedup_report)
        click.echo()
        
        # 生成字体文件
        click.echo("正在生成优化后的字体文件...")
        validation_report = generate_and_validate(
            dedup_result=dedup_result,
            output_dir=output_dir,
            suffix=suffix
        )
        
        # 输出验证报告
        click.echo(validation_report)
        
        click.secho(f"\n✓ 去重完成！输出文件已保存到: {output_dir}", fg='green')
        
    except FileNotFoundError as e:
        raise FontDedupError(f"文件不存在: {str(e)}")
    except ValueError as e:
        raise FontDedupError(f"参数错误: {str(e)}")
    except OSError as e:
        raise FontDedupError(f"文件系统错误: {str(e)}")
    except Exception as e:
        raise FontDedupError(f"去重失败: {str(e)}")


if __name__ == "__main__":
    main()
