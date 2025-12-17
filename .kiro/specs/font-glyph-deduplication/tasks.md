# 实现计划

- [x] 1. 项目初始化与基础结构
  - [x] 1.1 创建项目目录结构和配置文件
    - 创建 `src/font_dedup/` 目录结构
    - 创建 `pyproject.toml` 配置 Python 项目
    - 配置 fonttools、click、pytest、hypothesis 依赖
    - _Requirements: 5.1_
  - [x] 1.2 创建数据模型定义
    - 实现 `GlyphInfo`、`FontMetadata`、`DuplicateReport`、`DeduplicationResult`、`ValidationResult` dataclass
    - _Requirements: 1.1, 3.2_

- [x] 2. FontAnalyzer 字体分析器实现
  - [x] 2.1 实现字体解析功能
    - 使用 fonttools 解析 TTF 文件
    - 提取 cmap table 获取 Unicode 映射
    - 返回 FontMetadata 和 GlyphInfo 列表
    - _Requirements: 1.1_
  - [ ]* 2.2 编写 Property Test: 解析完整性
    - **Property 1: 解析完整性**
    - **Validates: Requirements 1.1**
  - [x] 2.3 实现重复检测功能
    - 分析多个字体的 code point 交集
    - 生成 DuplicateReport
    - _Requirements: 1.2, 1.3_
  - [ ]* 2.4 编写 Property Test: 重复检测准确性
    - **Property 2: 重复检测准确性**
    - **Validates: Requirements 1.2, 1.3**

- [x] 3. DeduplicationEngine 去重引擎实现
  - [x] 3.1 实现优先级去重逻辑
    - 根据优先级顺序决定 glyph 保留策略
    - 高优先级字体保留所有 glyph
    - 低优先级字体移除重复 glyph
    - _Requirements: 2.1, 2.2, 2.3_
  - [ ]* 3.2 编写 Property Test: 优先级保留不变量
    - **Property 3: 优先级保留不变量**
    - **Validates: Requirements 2.1, 2.3**
  - [ ]* 3.3 编写 Property Test: 默认优先级一致性
    - **Property 4: 默认优先级一致性**
    - **Validates: Requirements 2.2**
  - [x] 3.4 实现 Unicode 范围过滤功能
    - 支持指定去重范围
    - 支持排除范围保护
    - _Requirements: 4.1, 4.2, 4.3_
  - [ ]* 3.5 编写 Property Test: Unicode 范围过滤
    - **Property 7: Unicode 范围过滤**
    - **Validates: Requirements 4.1, 4.2**
  - [ ]* 3.6 编写 Property Test: 排除范围保护
    - **Property 8: 排除范围保护**
    - **Validates: Requirements 4.3**

- [x] 4. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [x] 5. FontGenerator 字体生成器实现
  - [x] 5.1 实现单字体生成功能
    - 使用 fonttools 的 subsetting 功能
    - 根据保留的 code point 集合生成新字体
    - 更新 cmap table
    - _Requirements: 3.1, 3.3_
  - [ ]* 5.2 编写 Property Test: Glyph 保留完整性
    - **Property 5: Glyph 保留完整性**
    - **Validates: Requirements 3.1, 3.2**
  - [ ]* 5.3 编写 Property Test: cmap 一致性
    - **Property 6: cmap 一致性**
    - **Validates: Requirements 3.3**
  - [x] 5.4 实现批量生成功能
    - 支持批量处理多个字体
    - 支持可配置的命名规则
    - _Requirements: 3.4_

- [x] 6. Validator 验证器实现
  - [x] 6.1 实现 TTF 格式验证
    - 验证输出文件是有效的 TTF 格式
    - 返回 ValidationResult
    - _Requirements: 6.1_
  - [ ]* 6.2 编写 Property Test: 输出字体有效性
    - **Property 9: 输出字体有效性**
    - **Validates: Requirements 6.1**
  - [x] 6.3 实现 Glyph 可访问性验证
    - 验证所有保留的 code point 可正确映射
    - _Requirements: 6.2_
  - [ ]* 6.4 编写 Property Test: Glyph 可访问性
    - **Property 10: Glyph 可访问性**
    - **Validates: Requirements 6.2**

- [x] 7. Reporter 报告系统实现
  - [x] 7.1 实现中文报告生成器
    - 创建 Reporter 类
    - 最终报告和错误信息使用中文
    - 技术关键词（TTF、glyph、cmap、Unicode、code point）保留英文
    - CLI 命令和参数保留英文
    - 代码注释使用中文
    - _Requirements: 7.1, 7.2, 7.4_
  - [ ]* 7.2 编写 Property Test: 输出报告语言规范
    - **Property 11: 输出报告语言规范**
    - **Validates: Requirements 7.1, 7.4**
    - 测试代码使用英文
  - [x] 7.3 集成报告生成到各组件
    - 在 FontAnalyzer、DeduplicationEngine、FontGenerator、Validator 中使用 Reporter
    - _Requirements: 7.1_

- [x] 8. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [x] 9. CLI 命令行接口实现
  - [x] 9.1 实现主命令入口
    - 使用 click 创建 CLI 框架
    - 支持字体文件参数输入
    - CLI 帮助信息使用中文，命令和参数保留英文
    - 代码注释使用中文
    - _Requirements: 5.1, 7.2, 7.4_
  - [x] 9.2 实现 analyze 子命令
    - 支持 `--analyze` flag 仅输出分析结果
    - 不修改任何文件
    - 最终输出报告使用中文
    - _Requirements: 5.2, 7.1_
  - [x] 9.3 实现 deduplicate 子命令
    - 支持 `--output-dir` 指定输出目录
    - 支持 `--priority` 指定优先级
    - 支持 `--range` 和 `--exclude` 指定范围
    - _Requirements: 5.3_
  - [x] 9.4 实现错误处理和帮助信息
    - 无效参数时显示中文错误信息
    - 提供完整的中文使用说明
    - _Requirements: 5.4, 6.3, 7.1_

- [x] 10. 单元测试实现
  - [x] 10.1 编写 CLI 单元测试
    - 测试命令行接口的基本功能
    - 测试参数验证和错误处理
    - 使用实际字体文件测试完整流程
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 10.2 编写 Reporter 单元测试
    - 测试中文报告生成
    - 测试技术关键词英文保留
    - 测试错误信息格式化
    - 测试验证结果格式化
    - _Requirements: 7.1, 7.2, 7.4_
  - [x] 10.3 编写 Utils 集成测试
    - 测试 analyze_and_report 功能
    - 测试 deduplicate_and_report 功能
    - 测试文件大小报告功能
    - 测试错误处理
    - _Requirements: 1.1, 2.1, 3.1, 7.1_

- [x] 11. ShapeAnalyzer 字形分析器实现
  - [x] 11.1 实现字形轮廓提取功能
    - 使用 fonttools 提取 glyph 轮廓数据
    - 计算字形边界框
    - 返回 GlyphOutline 对象
    - _Requirements: 8.1_
  - [ ]* 11.2 编写 Property Test: 字形轮廓提取完整性
    - **Property 12: 字形轮廓提取完整性**
    - **Validates: Requirements 8.1**
  - [x] 11.3 实现字形相似度计算功能
    - 基于轮廓数据计算两个字形的相似度
    - 返回 0.0-1.0 范围的相似度值
    - 处理边界情况（空轮廓、相同轮廓等）
    - _Requirements: 8.2_
  - [ ]* 11.4 编写 Property Test: 字形相似度计算有效性
    - **Property 13: 字形相似度计算有效性**
    - **Validates: Requirements 8.2**
  - [x] 11.5 实现字形变体检测功能
    - 分析多个字体中相同码点的字形差异
    - 根据相似度阈值识别字形变体
    - 生成 ShapeVariantReport
    - _Requirements: 8.3_
  - [ ]* 11.6 编写 Property Test: 字形变体识别准确性
    - **Property 14: 字形变体识别准确性**
    - **Validates: Requirements 8.3**

- [x] 12. 更新数据模型
  - [x] 12.1 添加字形检测相关数据模型
    - 实现 GlyphOutline、ShapeVariant、ShapeVariantReport、ShapeAwareDeduplicationResult dataclass
    - 更新现有模型以支持字形数据
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 13. 扩展 DeduplicationEngine 支持字形检测




  - [x] 13.1 添加字形检测模式参数


    - 扩展构造函数支持 shape_analysis_enabled 和 similarity_threshold 参数
    - 集成 ShapeAnalyzer 组件
    - _Requirements: 8.4_
  - [x] 13.2 实现基于字形分析的去重逻辑


    - 实现 deduplicate_with_shape_analysis 方法
    - 基于字形相似度而非仅 Unicode 码点进行去重决策
    - 返回 ShapeAwareDeduplicationResult
    - _Requirements: 8.4_
  - [ ]* 13.3 编写 Property Test: 字形检测模式一致性
    - **Property 15: 字形检测模式一致性**
    - **Validates: Requirements 8.4**

- [x] 14. 扩展 Reporter 支持字形变体报告




  - [x] 14.1 实现字形变体报告生成


    - 添加 generate_shape_variant_report 方法
    - 区分显示"Unicode 重复"和"字形变体"
    - 使用中文输出，技术关键词保留英文
    - _Requirements: 8.5, 7.1, 7.4_
  - [ ]* 14.2 编写 Property Test: 报告分类显示准确性
    - **Property 16: 报告分类显示准确性**
    - **Validates: Requirements 8.5**
  - [x] 14.3 更新现有报告方法


    - 在分析报告中包含字形变体信息
    - 在去重报告中显示保护的字形变体
    - _Requirements: 8.5_


- [x] 15. 扩展 CLI 支持字形检测选项



  - [x] 15.1 添加字形检测相关命令行参数


    - 添加 `--shape-analysis` flag 启用字形检测
    - 添加 `--similarity-threshold` 参数设置相似度阈值
    - 更新帮助信息（中文）
    - _Requirements: 8.4, 7.2_
  - [x] 15.2 集成字形检测到 analyze 和 deduplicate 命令


    - 在 analyze 命令中支持字形变体分析
    - 在 deduplicate 命令中支持基于字形的去重
    - _Requirements: 8.4, 8.5_


- [x] 16. Checkpoint - 确保字形检测功能测试通过




  - 确保所有字形检测相关测试通过，如有问题请询问用户。

- [x] 17. 集成测试和文档更新







  - [x] 17.1 编写字形检测集成测试



    - 使用实际字体文件测试字形检测功能
    - 测试 SC/KR 字形差异识别
    - 测试完整的字形检测去重流程
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [x] 17.2 更新 README 文档


    - 添加字形检测功能说明
    - 添加使用示例
    - 更新技术栈说明
    - _Requirements: 8.4, 8.5_


- [x] 18. Final Checkpoint - 确保所有测试通过




  - 确保所有测试通过，如有问题请询问用户。

