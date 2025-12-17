# 测试指南

## 快速开始

```bash
# 日常开发 - 快速测试（~17秒）
pytest

# 完整测试 - 包括 CJK 测试（~3分钟）
pytest -m ""

# 只运行 CJK 测试
pytest -m cjk
```

## 测试策略

本项目采用分层测试策略，平衡测试覆盖率和执行速度：

### 🚀 快速测试（默认）
- **执行时间**: ~17秒
- **字体文件**: 小型字体（615KB）
  - `NotoSans-Light.ttf`
  - `NotoSans-Regular.ttf`
- **测试范围**: ASCII 字符、基本功能
- **使用场景**: 
  - 日常开发
  - 代码提交前检查
  - CI/CD 流水线
  - TDD 开发

### 🐢 CJK 测试（按需运行）
- **执行时间**: ~2-3分钟
- **字体文件**: 大型 CJK 字体（5-10MB）
  - `NotoSansSC-Bold.ttf`
  - `NotoSansKR-Bold.ttf`
  - `NotoSansJP-Bold.ttf`
- **测试范围**: CJK 字符、字形变体检测
- **使用场景**:
  - 发布前验证
  - 字形分析功能修改后
  - 深度集成测试
  - 性能基准测试

## 测试命令

### 基本命令

```bash
# 运行所有快速测试（推荐）
pytest

# 显示详细输出
pytest -v

# 显示测试耗时
pytest --durations=10

# 运行特定文件
pytest tests/test_cli.py
```

### 标记过滤

```bash
# 排除慢速测试
pytest -m "not slow"

# 排除 CJK 测试
pytest -m "not cjk"

# 只运行 CJK 测试
pytest -m cjk

# 只运行慢速测试
pytest -m slow

# 运行所有测试（包括慢速）
pytest -m ""
```

### 覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=src/font_dedup --cov-report=html

# 查看覆盖率
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## 测试文件结构

```
tests/
├── README.md                      # 测试说明
├── test_cli.py                    # CLI 测试（快速）
├── test_engine_shape_aware.py     # 字形分析引擎测试（快速）
├── test_reporter.py               # 报告生成器测试（快速）
├── test_utils_integration.py      # 工具函数测试（快速）
└── test_cjk_fonts.py             # CJK 字体测试（慢速）
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run fast tests
        run: pytest -m "not slow" -v

  full-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'release' || contains(github.event.head_commit.message, '[full-test]')
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run all tests
        run: pytest -v
```

## 性能基准

| 测试套件 | 测试数量 | 执行时间 | 字体大小 |
|---------|---------|---------|---------|
| 快速测试 | 37 | ~17秒 | 68-614KB |
| CJK 测试 | 5 | ~160秒 | 5-10MB |
| 全部测试 | 42 | ~180秒 | - |

## 最佳实践

### 开发工作流

1. **编写代码** → 运行快速测试 `pytest`
2. **提交前** → 运行快速测试 `pytest -v`
3. **发布前** → 运行完整测试 `pytest -m ""`
4. **修改字形分析** → 运行 CJK 测试 `pytest -m cjk`

### 添加新测试

- **快速测试**: 使用小型字体，添加到现有测试文件
- **CJK 测试**: 使用 `@pytest.mark.cjk` 和 `@pytest.mark.slow` 标记，添加到 `test_cjk_fonts.py`

```python
@pytest.mark.cjk
@pytest.mark.slow
def test_my_cjk_feature():
    """Test description."""
    # 使用 CJK 字体测试
    pass
```

## 故障排查

### 测试失败

```bash
# 显示详细错误信息
pytest -vv

# 在第一个失败时停止
pytest -x

# 显示本地变量
pytest -l

# 进入调试器
pytest --pdb
```

### 性能问题

```bash
# 查看最慢的 10 个测试
pytest --durations=10

# 只运行快速测试
pytest -m "not slow"

# 并行运行（需要 pytest-xdist）
pytest -n auto
```

## 相关文档

- [tests/README.md](tests/README.md) - 详细测试说明
- [pyproject.toml](pyproject.toml) - pytest 配置
- [README.md](README.md) - 项目主文档
