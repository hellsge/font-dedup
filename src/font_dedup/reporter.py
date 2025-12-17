"""
Reporter 模块用于生成中文报告和错误信息。

本模块提供 Reporter 类，负责：
- 生成分析报告（中文）
- 生成去重结果报告（中文）
- 格式化错误信息（中文）
- 格式化验证结果（中文）
- 保留技术关键词的英文原文（TTF、glyph、cmap、Unicode、code point 等）
"""

from pathlib import Path

from .models import (
    DuplicateReport,
    DeduplicationResult,
    ValidationResult,
    ShapeVariantReport,
    ShapeAwareDeduplicationResult,
)


class Reporter:
    """
    报告生成器，用于生成中文输出报告和错误信息。
    
    所有最终用户可见的报告和错误信息使用中文，
    但技术关键词（TTF、glyph、cmap、Unicode、code point 等）保留英文。
    """
    
    def generate_analysis_report(
        self, 
        duplicate_report: DuplicateReport | ShapeVariantReport
    ) -> str:
        """
        生成分析报告（中文）。
        
        支持基本的重复分析报告和字形变体分析报告。
        
        Args:
            duplicate_report: 重复分析报告数据或字形变体报告数据
            
        Returns:
            格式化的中文分析报告字符串
        """
        # 如果是字形变体报告，使用专门的方法
        if isinstance(duplicate_report, ShapeVariantReport):
            return self.generate_shape_variant_report(duplicate_report)
        
        lines = []
        lines.append("=" * 60)
        lines.append("字体 Glyph 重复分析报告")
        lines.append("=" * 60)
        lines.append("")
        
        # 字体文件列表
        lines.append(f"分析的字体文件数量: {len(duplicate_report.fonts)}")
        lines.append("")
        
        for i, font_meta in enumerate(duplicate_report.fonts, 1):
            lines.append(f"{i}. {font_meta.path.name}")
            lines.append(f"   字体家族: {font_meta.family_name}")
            lines.append(f"   Glyph 总数: {font_meta.glyph_count}")
            lines.append(f"   支持的 Unicode Code Point 数量: {len(font_meta.codepoints)}")
            lines.append("")
        
        # 重复情况统计
        lines.append("-" * 60)
        lines.append("重复情况统计")
        lines.append("-" * 60)
        lines.append(f"发现的重复 Code Point 总数: {duplicate_report.total_duplicate_count}")
        lines.append("")
        
        if duplicate_report.total_duplicate_count > 0:
            # 按重复次数分组统计
            duplication_counts: dict[int, int] = {}
            for fonts_with_cp in duplicate_report.duplicates.values():
                count = len(fonts_with_cp)
                duplication_counts[count] = duplication_counts.get(count, 0) + 1
            
            lines.append("重复分布:")
            for dup_count in sorted(duplication_counts.keys(), reverse=True):
                cp_count = duplication_counts[dup_count]
                lines.append(f"  在 {dup_count} 个字体中重复: {cp_count} 个 code point")
            lines.append("")
            
            # 显示部分重复的 code point 示例
            if duplicate_report.total_duplicate_count <= 20:
                lines.append("重复的 Code Point 列表:")
                for codepoint in sorted(duplicate_report.duplicates.keys()):
                    fonts = duplicate_report.duplicates[codepoint]
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
            else:
                lines.append("重复的 Code Point 示例（前 20 个）:")
                for i, codepoint in enumerate(sorted(duplicate_report.duplicates.keys())[:20]):
                    fonts = duplicate_report.duplicates[codepoint]
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
                lines.append(f"  ... 还有 {duplicate_report.total_duplicate_count - 20} 个")
        else:
            lines.append("未发现重复的 glyph。")
        
        lines.append("")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def generate_deduplication_report(
        self, 
        result: DeduplicationResult | ShapeAwareDeduplicationResult
    ) -> str:
        """
        生成去重结果报告（中文）。
        
        支持基本的去重结果和基于字形分析的去重结果。
        
        Args:
            result: 去重结果数据或字形感知去重结果数据
            
        Returns:
            格式化的中文去重报告字符串
        """
        lines = []
        lines.append("=" * 60)
        
        # 根据结果类型调整标题
        if isinstance(result, ShapeAwareDeduplicationResult):
            lines.append("字体 Glyph 去重结果报告（字形感知模式）")
        else:
            lines.append("字体 Glyph 去重结果报告")
        
        lines.append("=" * 60)
        lines.append("")
        
        total_removed = sum(len(glyphs) for glyphs in result.removed_glyphs.values())
        total_kept = sum(len(glyphs) for glyphs in result.font_glyphs.values())
        
        lines.append(f"处理的字体文件数量: {len(result.font_glyphs)}")
        lines.append(f"保留的 Glyph 总数: {total_kept}")
        lines.append(f"移除的 Glyph 总数: {total_removed}")
        
        # 如果是字形感知模式，显示保护的字形变体信息
        if isinstance(result, ShapeAwareDeduplicationResult):
            lines.append(f"保护的字形变体数量: {len(result.preserved_variants)}")
        
        lines.append("")
        
        # 显示保护的字形变体详情
        if isinstance(result, ShapeAwareDeduplicationResult) and result.preserved_variants:
            lines.append("-" * 60)
            lines.append("保护的字形变体")
            lines.append("-" * 60)
            lines.append("")
            lines.append("以下 Code Point 在不同字体中具有不同字形，已保留所有变体:")
            lines.append("")
            
            if len(result.preserved_variants) <= 20:
                for variant in result.preserved_variants:
                    codepoint = variant.codepoint
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in variant.fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
            else:
                for variant in result.preserved_variants[:20]:
                    codepoint = variant.codepoint
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in variant.fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
                lines.append(f"  ... 还有 {len(result.preserved_variants) - 20} 个")
            
            lines.append("")
        
        # 每个字体的详细信息
        lines.append("-" * 60)
        lines.append("各字体处理详情")
        lines.append("-" * 60)
        lines.append("")
        
        for font_path in result.font_glyphs.keys():
            kept = result.font_glyphs[font_path]
            removed = result.removed_glyphs[font_path]
            
            lines.append(f"字体: {font_path.name}")
            lines.append(f"  保留的 Code Point 数量: {len(kept)}")
            lines.append(f"  移除的 Code Point 数量: {len(removed)}")
            
            if removed:
                if len(removed) <= 10:
                    removed_list = ', '.join(f'U+{cp:04X}' for cp in sorted(removed))
                    lines.append(f"  移除的 Code Point: {removed_list}")
                else:
                    first_ten = ', '.join(f'U+{cp:04X}' for cp in sorted(removed)[:10])
                    lines.append(f"  移除的 Code Point 示例: {first_ten} ... (共 {len(removed)} 个)")
            
            lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def format_error(self, error: Exception) -> str:
        """
        格式化错误信息（中文）。
        
        Args:
            error: 异常对象
            
        Returns:
            格式化的中文错误信息字符串
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # 根据错误类型提供更友好的中文描述
        if isinstance(error, FileNotFoundError):
            return f"错误: 文件未找到 - {error_msg}"
        elif isinstance(error, ValueError):
            return f"错误: 参数值无效 - {error_msg}"
        elif isinstance(error, OSError):
            return f"错误: 文件系统操作失败 - {error_msg}"
        elif isinstance(error, PermissionError):
            return f"错误: 权限不足 - {error_msg}"
        else:
            return f"错误 ({error_type}): {error_msg}"
    
    def format_validation_result(self, result: ValidationResult) -> str:
        """
        格式化验证结果（中文）。
        
        Args:
            result: 验证结果数据
            
        Returns:
            格式化的中文验证结果字符串
        """
        lines = []
        
        if result.is_valid:
            lines.append("✓ 验证通过")
        else:
            lines.append("✗ 验证失败")
        
        if result.errors:
            lines.append("")
            lines.append("错误:")
            for error in result.errors:
                lines.append(f"  - {error}")
        
        if result.warnings:
            lines.append("")
            lines.append("警告:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
        
        return '\n'.join(lines)
    
    def format_file_size_info(self, original_size: int, new_size: int) -> str:
        """
        格式化文件大小信息（中文）。
        
        Args:
            original_size: 原始文件大小（字节）
            new_size: 新文件大小（字节）
            
        Returns:
            格式化的文件大小对比信息
        """
        def format_bytes(size: int) -> str:
            """将字节数格式化为人类可读的格式"""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} TB"
        
        original_str = format_bytes(original_size)
        new_str = format_bytes(new_size)
        
        if new_size < original_size:
            reduction = original_size - new_size
            percentage = (reduction / original_size) * 100
            reduction_str = format_bytes(reduction)
            return f"文件大小: {original_str} → {new_str} (减少 {reduction_str}, {percentage:.1f}%)"
        elif new_size > original_size:
            increase = new_size - original_size
            percentage = (increase / original_size) * 100
            increase_str = format_bytes(increase)
            return f"文件大小: {original_str} → {new_str} (增加 {increase_str}, {percentage:.1f}%)"
        else:
            return f"文件大小: {original_str} (无变化)"
    
    def format_progress(self, current: int, total: int, description: str = "") -> str:
        """
        格式化进度信息（中文）。
        
        Args:
            current: 当前进度
            total: 总数
            description: 进度描述
            
        Returns:
            格式化的进度信息字符串
        """
        percentage = (current / total * 100) if total > 0 else 0
        desc_part = f"{description}: " if description else ""
        return f"{desc_part}[{current}/{total}] {percentage:.1f}%"
    
    def generate_shape_variant_report(self, variant_report: ShapeVariantReport) -> str:
        """
        生成字形变体分析报告（中文）。
        
        区分显示"Unicode 重复"和"字形变体"两种类型。
        
        Args:
            variant_report: 字形变体分析报告数据
            
        Returns:
            格式化的中文字形变体报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("字体 Glyph 字形变体分析报告")
        lines.append("=" * 60)
        lines.append("")
        
        # 字体文件列表
        lines.append(f"分析的字体文件数量: {len(variant_report.fonts)}")
        lines.append("")
        
        for i, font_meta in enumerate(variant_report.fonts, 1):
            lines.append(f"{i}. {font_meta.path.name}")
            lines.append(f"   字体家族: {font_meta.family_name}")
            lines.append(f"   Glyph 总数: {font_meta.glyph_count}")
            lines.append(f"   支持的 Unicode Code Point 数量: {len(font_meta.codepoints)}")
            lines.append("")
        
        # 分类统计
        lines.append("-" * 60)
        lines.append("分类统计")
        lines.append("-" * 60)
        lines.append(f"发现的字形变体总数: {variant_report.total_variant_count}")
        lines.append(f"发现的 Unicode 重复总数: {len(variant_report.unicode_duplicates)}")
        lines.append("")
        
        # Unicode 重复部分
        if variant_report.unicode_duplicates:
            lines.append("-" * 60)
            lines.append("Unicode 重复（相同字形）")
            lines.append("-" * 60)
            lines.append("")
            lines.append("这些 Code Point 在多个字体中具有相同的字形，可以安全去重。")
            lines.append("")
            
            if len(variant_report.unicode_duplicates) <= 20:
                lines.append("Unicode 重复列表:")
                for codepoint in sorted(variant_report.unicode_duplicates.keys()):
                    fonts = variant_report.unicode_duplicates[codepoint]
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
            else:
                lines.append("Unicode 重复示例（前 20 个）:")
                for i, codepoint in enumerate(sorted(variant_report.unicode_duplicates.keys())[:20]):
                    fonts = variant_report.unicode_duplicates[codepoint]
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
                lines.append(f"  ... 还有 {len(variant_report.unicode_duplicates) - 20} 个")
            lines.append("")
        
        # 字形变体部分
        if variant_report.shape_variants:
            lines.append("-" * 60)
            lines.append("字形变体（不同字形）")
            lines.append("-" * 60)
            lines.append("")
            lines.append("这些 Code Point 在不同字体中具有不同的字形表现，")
            lines.append("可能代表不同语言/地区的字形差异，建议保留。")
            lines.append("")
            
            if len(variant_report.shape_variants) <= 20:
                lines.append("字形变体列表:")
                for variant in variant_report.shape_variants:
                    codepoint = variant.codepoint
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in variant.fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
                    
                    # 显示相似度信息
                    if variant.similarity_scores:
                        lines.append("    相似度:")
                        for (font1, font2), score in variant.similarity_scores.items():
                            lines.append(f"      {font1.name} ↔ {font2.name}: {score:.2f}")
            else:
                lines.append("字形变体示例（前 20 个）:")
                for variant in variant_report.shape_variants[:20]:
                    codepoint = variant.codepoint
                    char = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF else '?'
                    font_names = ', '.join(f.name for f in variant.fonts)
                    lines.append(f"  U+{codepoint:04X} ({char}): {font_names}")
                lines.append(f"  ... 还有 {len(variant_report.shape_variants) - 20} 个")
            lines.append("")
        
        if not variant_report.unicode_duplicates and not variant_report.shape_variants:
            lines.append("未发现重复或字形变体。")
            lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
