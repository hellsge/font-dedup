# Font Dedup - TTF 字体 Glyph 去重工具

一个用于分析和优化 TTF 字体文件的命令行工具，通过智能去重减小字体文件总体积。

## 功能特点

- 🔍 **字体分析**: 分析多个字体文件中的 glyph 重复情况
- 🎯 **优先级去重**: 根据用户指定的优先级保留 glyph
- 📊 **Unicode 范围过滤**: 支持指定特定 Unicode 范围进行去重
- 🛡️ **排除范围保护**: 保护特定范围的 glyph 不被去重
- ✅ **自动验证**: 验证生成的字体文件有效性
- 🇨🇳 **中文界面**: 输出报告和错误信息使用中文

## 安装

```bash
pip install -e .
```

开发模式安装（包含测试依赖）：

```bash
pip install -e ".[dev]"
```

## 使用方法

### 分析字体文件

仅分析字体文件中的重复 glyph，不修改任何文件：

```bash
font-dedup analyze font1.ttf font2.ttf font3.ttf
```

### 执行去重

基本去重操作：

```bash
font-dedup deduplicate font1.ttf font2.ttf -o ./output
```

指定字体优先级（font1.ttf 优先级最高）：

```bash
font-dedup deduplicate font1.ttf font2.ttf -o ./output -p font1.ttf
```

仅处理中文字符范围：

```bash
font-dedup deduplicate font1.ttf font2.ttf -o ./output -r 0x4E00-0x9FFF
```

排除 ASCII 字符范围：

```bash
font-dedup deduplicate font1.ttf font2.ttf -o ./output -e 0x0020-0x007F
```

自定义输出文件后缀：

```bash
font-dedup deduplicate font1.ttf font2.ttf -o ./output -s _optimized
```

## 工作原理

1. **解析字体**: 使用 fonttools 解析 TTF 文件，提取 glyph 和 Unicode 映射信息
2. **检测重复**: 分析多个字体间的 code point 重叠情况
3. **优先级去重**: 根据优先级顺序，从低优先级字体中移除重复 glyph
4. **生成字体**: 使用 fonttools subsetting 功能生成优化后的字体文件
5. **验证输出**: 验证生成的字体文件格式正确且所有保留的 glyph 可访问

## 技术栈

- **Python 3.10+**
- **fonttools**: 字体文件解析和处理
- **click**: 命令行接口
- **pytest + hypothesis**: 测试框架

## 开发

### 获取测试字体

测试需要使用 TTF 字体文件。你可以从 [Google Fonts](https://fonts.google.com/) 下载 Noto Sans 系列字体：

- [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP)
- [Noto Sans KR](https://fonts.google.com/noto/specimen/Noto+Sans+KR)
- [Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC)

将下载的 TTF 文件放在项目根目录即可运行测试。

### 运行测试

```bash
pytest
```

运行测试并查看覆盖率：

```bash
pytest --cov=src/font_dedup
```

## 项目结构

```
font-dedup/
├── src/font_dedup/
│   ├── analyzer.py      # 字体分析器
│   ├── engine.py        # 去重引擎
│   ├── generator.py     # 字体生成器
│   ├── validator.py     # 验证器
│   ├── reporter.py      # 报告生成器
│   ├── models.py        # 数据模型
│   ├── cli.py           # 命令行接口
│   └── utils.py         # 工具函数
├── tests/               # 测试文件
├── .kiro/specs/         # 功能规格文档
└── pyproject.toml       # 项目配置
```

## 许可证

MIT License

## 作者

hellsge (hellsge@qq.com)
