# 需求文档

## 简介

本功能旨在开发一个 TTF 字体裁剪工具，通过分析多个字体文件中的 glyph（字形）重复情况，删除重复的 glyph 以减小字体文件的总体积。该工具适用于需要加载多个字体但希望优化资源大小的场景，如 Web 应用、游戏或嵌入式系统。

## 术语表

- **TTF (TrueType Font)**: 一种常见的字体文件格式，包含 glyph 轮廓数据和字体元信息
- **Glyph（字形）**: 字体中单个字符的视觉表示，包含轮廓路径数据
- **Unicode Code Point**: 字符的唯一标识符，用于映射 glyph
- **cmap Table**: 字体中的字符映射表，定义 Unicode 到 glyph index 的映射
- **Subsetting（子集化）**: 从字体中提取特定字符集的过程
- **Primary Font（主字体）**: 保留完整 glyph 的基准字体
- **Secondary Font（次要字体）**: 需要删除与主字体重复 glyph 的字体
- **Glyph Shape（字形形状）**: glyph 的实际视觉轮廓，不同于 Unicode 映射
- **Glyph Variant（字形变体）**: 相同 Unicode 码点在不同语言/地区的不同字形表现
- **Shape Similarity（字形相似度）**: 两个字形在视觉上的相似程度，用数值表示

## 需求列表

### 需求 1

**用户故事:** 作为开发者，我希望分析多个 TTF 字体文件以识别重复的 glyph，以便在优化前了解字体之间的重叠情况。

#### 验收标准

1. WHEN 用户提供多个 TTF 文件路径 THEN Font_Analyzer SHALL 解析每个字体并提取 glyph 信息（包括 Unicode 映射）
2. WHEN 分析字体时 THEN Font_Analyzer SHALL 生成报告，显示哪些 glyph 在多个字体间共享
3. WHEN 发现重复 glyph THEN Font_Analyzer SHALL 显示重叠的 Unicode code point 数量和列表

### 需求 2

**用户故事:** 作为开发者，我希望指定字体的优先级顺序，以便在发现重复时控制哪个字体保留原始 glyph。

#### 验收标准

1. WHEN 用户指定字体优先级顺序 THEN Deduplication_Engine SHALL 在高优先级字体中保留 glyph
2. WHEN 未指定优先级 THEN Deduplication_Engine SHALL 使用输入文件的顺序作为默认优先级
3. WHEN 处理字体时 THEN Deduplication_Engine SHALL 仅从低优先级字体中移除重复 glyph

### 需求 3

**用户故事:** 作为开发者，我希望生成移除重复 glyph 后的优化字体文件，以便减小字体资源的总大小。

#### 验收标准

1. WHEN 去重完成 THEN Font_Generator SHALL 输出移除重复 glyph 的新 TTF 文件
2. WHEN 生成输出文件 THEN Font_Generator SHALL 保留所有非重复 glyph 和字体 metadata
3. WHEN 移除某个 glyph THEN Font_Generator SHALL 更新 cmap table 以反映该移除
4. WHEN 创建输出文件 THEN Font_Generator SHALL 使用可配置的命名规则（如 `_dedup` 后缀）

### 需求 4

**用户故事:** 作为开发者，我希望指定要考虑去重的字符范围，以便针对特定 script 或字符集进行处理。

#### 验收标准

1. WHEN 用户指定 Unicode 范围 THEN Deduplication_Engine SHALL 仅考虑这些范围内的 glyph 进行去重
2. WHEN 未指定范围 THEN Deduplication_Engine SHALL 考虑所有 glyph 进行去重
3. WHERE 用户指定排除范围 THEN Deduplication_Engine SHALL 保留这些 glyph，无论是否重复

### 需求 5

**用户故事:** 作为开发者，我希望有一个 CLI 来运行去重流程，以便将其集成到构建 pipeline 中。

#### 验收标准

1. WHEN 用户使用字体文件参数运行 CLI THEN CLI SHALL 处理指定的字体
2. WHEN 用户提供 `--analyze` flag THEN CLI SHALL 输出分析结果而不修改文件
3. WHEN 用户提供 `--output-dir` option THEN CLI SHALL 将输出文件写入指定目录
4. WHEN 提供无效参数 THEN CLI SHALL 显示有用的错误信息和使用说明

### 需求 6

**用户故事:** 作为开发者，我希望验证优化后的字体仍能正确渲染，以确保去重后的质量。

#### 验收标准

1. WHEN 生成输出字体 THEN Validator SHALL 验证字体文件是有效的 TTF 格式
2. WHEN 执行验证 THEN Validator SHALL 检查所有保留的 glyph 可通过其 Unicode 映射访问
3. IF 验证失败 THEN Validator SHALL 报告具体错误和受影响的 glyph

### 需求 7

**用户故事:** 作为中文用户，我希望工具的最终输出报告和错误信息使用中文，以便更容易理解和使用。

#### 验收标准

1. WHEN 工具输出最终报告或错误信息 THEN Output_System SHALL 使用中文显示内容
2. WHEN 编写代码注释 THEN Output_System SHALL 使用中文编写注释
3. WHEN 测试代码运行时 THEN Test_System SHALL 使用英文进行测试流程和断言
4. WHEN 输出包含技术关键词、常用名词或 CLI 命令 THEN Output_System SHALL 保留英文原文

### 需求 8

**用户故事:** 作为开发者，我希望检测相同 Unicode 码点在不同字体中的字形差异，以便避免错误地删除具有不同视觉表现的字符。

#### 验收标准

1. WHEN 分析字体时 THEN Shape_Analyzer SHALL 提取每个 glyph 的轮廓数据用于形状比较
2. WHEN 发现相同 Unicode 码点 THEN Shape_Analyzer SHALL 计算不同字体间该字符的字形相似度
3. WHEN 字形相似度低于阈值 THEN Deduplication_Engine SHALL 将其标记为字形变体而非重复
4. WHERE 用户启用字形检测模式 THEN Deduplication_Engine SHALL 基于字形相似度而非仅 Unicode 码点进行去重决策
5. WHEN 检测到字形变体 THEN Reporter SHALL 在报告中区分显示"Unicode 重复"和"字形变体"

