# 贡献指南

感谢您对发射机数据分析器项目的关注！本文档将指导您如何为项目做出贡献。

## 目录

- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试要求](#测试要求)
- [提交流程](#提交流程)
- [文档贡献](#文档贡献)
- [报告问题](#报告问题)

## 开发环境设置

### 1. Fork和克隆项目

```bash
# Fork项目到您的GitHub账号
# 然后克隆到本地
git clone https://github.com/your-username/transmitter-data-analyzer.git
cd transmitter-data-analyzer
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3. 安装开发依赖

```bash
# 安装所有依赖（包括开发工具）
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

开发依赖包括：
- **pytest**: 测试框架
- **pytest-cov**: 代码覆盖率
- **hypothesis**: 基于属性的测试
- **black**: 代码格式化
- **pylint**: 代码检查
- **mypy**: 类型检查

### 4. 安装Tesseract-OCR

参考 [INSTALL.md](INSTALL.md) 安装Tesseract-OCR。

### 5. 验证环境

```bash
# 运行所有测试
pytest

# 检查代码风格
black --check src/ tests/
pylint src/

# 类型检查
mypy src/
```

## 代码规范

### Python代码风格

项目遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码规范。

#### 使用Black格式化代码

```bash
# 格式化所有代码
black src/ tests/

# 检查格式（不修改）
black --check src/ tests/
```

#### 命名规范

- **模块名**: 小写字母，下划线分隔（如 `ocr_extractor.py`）
- **类名**: 驼峰命名（如 `OCRExtractor`）
- **函数名**: 小写字母，下划线分隔（如 `extract_from_image`）
- **常量**: 大写字母，下划线分隔（如 `DEFAULT_DB_PATH`）
- **私有方法**: 前缀单下划线（如 `_preprocess_image`）

#### 文档字符串

所有公共函数和类都必须有文档字符串：

```python
def extract_from_image(self, image_path: Path) -> pd.DataFrame:
    """
    从图像中提取表格数据
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        包含item_name、value、unit三列的DataFrame
        
    Raises:
        FileNotFoundError: 图像文件不存在
        OCRError: OCR识别失败
        
    Examples:
        >>> extractor = OCRExtractor()
        >>> df = extractor.extract_from_image(Path("screenshot.png"))
        >>> print(df.columns)
        Index(['item_name', 'value', 'unit'], dtype='object')
    """
    pass
```

#### 类型注解

使用类型注解提高代码可读性：

```python
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd

def query_by_month(self, month: str) -> pd.DataFrame:
    """查询指定月份的数据"""
    pass

def get_available_months(self) -> List[str]:
    """获取所有可用月份"""
    pass

def _parse_value_unit(self, text: str) -> Tuple[float, str]:
    """解析数值和单位"""
    pass
```

### 代码组织

#### 模块结构

```python
"""
模块文档字符串
简要描述模块功能
"""

# 标准库导入
import sys
from pathlib import Path
from typing import List, Optional

# 第三方库导入
import pandas as pd
import numpy as np

# 本地导入
from src.exceptions import DatabaseError
from src.config import get_default_db_path

# 常量定义
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 类和函数定义
class MyClass:
    """类文档字符串"""
    pass

def my_function():
    """函数文档字符串"""
    pass
```

#### 错误处理

使用自定义异常类：

```python
from src.exceptions import OCRError, DatabaseError

def extract_data(image_path: Path) -> pd.DataFrame:
    """提取数据"""
    try:
        # 处理逻辑
        pass
    except FileNotFoundError as e:
        raise OCRError(f"图像文件不存在: {image_path}") from e
    except Exception as e:
        logger.exception("提取数据时发生错误")
        raise OCRError(f"提取失败: {str(e)}") from e
```

#### 日志记录

使用标准logging模块：

```python
import logging

logger = logging.getLogger(__name__)

def process_data():
    """处理数据"""
    logger.info("开始处理数据")
    try:
        # 处理逻辑
        logger.debug("处理步骤1完成")
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
    logger.info("数据处理完成")
```

## 测试要求

### 测试类型

项目使用三种测试类型：

1. **单元测试**: 测试单个函数或方法
2. **基于属性的测试**: 使用Hypothesis测试通用属性
3. **集成测试**: 测试模块间的交互

### 编写单元测试

```python
# tests/unit/test_analyzer.py
import pytest
from src.analyzer import DataAnalyzer

def test_calculate_absolute_change():
    """测试绝对变化量计算"""
    analyzer = DataAnalyzer(database=None)
    result = analyzer._calculate_absolute_change(10.0, 15.0)
    assert result == 5.0

def test_calculate_relative_change():
    """测试相对变化率计算"""
    analyzer = DataAnalyzer(database=None)
    result = analyzer._calculate_relative_change(10.0, 15.0)
    assert abs(result - 50.0) < 0.01
```

### 编写属性测试

```python
# tests/property/test_properties_analyzer.py
from hypothesis import given, strategies as st
from src.analyzer import DataAnalyzer

@given(
    value1=st.floats(min_value=0.01, max_value=1000),
    value2=st.floats(min_value=0.01, max_value=1000)
)
def test_property_change_calculation(value1, value2):
    """
    Feature: transmitter-data-analyzer, Property 11: 变化量计算正确性
    
    对于任何数值对，变化量计算应该正确
    """
    analyzer = DataAnalyzer(database=None)
    
    absolute_change = analyzer._calculate_absolute_change(value1, value2)
    relative_change = analyzer._calculate_relative_change(value1, value2)
    
    # 验证绝对变化量
    assert abs(absolute_change - (value2 - value1)) < 1e-6
    
    # 验证相对变化率
    expected_relative = ((value2 - value1) / value1) * 100
    assert abs(relative_change - expected_relative) < 1e-6
```

### 测试覆盖率

- 目标代码覆盖率: ≥ 80%
- 核心模块覆盖率: ≥ 90%

```bash
# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html --cov-report=term

# 查看HTML报告
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
```

### 测试命名规范

- 单元测试: `test_<function_name>_<scenario>`
- 属性测试: `test_property_<property_name>`
- 集成测试: `test_<workflow_name>`

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_analyzer.py

# 运行特定测试函数
pytest tests/unit/test_analyzer.py::test_calculate_absolute_change

# 运行单元测试
pytest tests/unit/

# 运行属性测试
pytest tests/property/

# 运行集成测试
pytest tests/integration/

# 跳过慢速测试
pytest -m "not slow"

# 详细输出
pytest -v

# 显示print输出
pytest -s
```

## 提交流程

### 1. 创建功能分支

```bash
# 从main分支创建新分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

分支命名规范：
- 新功能: `feature/feature-name`
- Bug修复: `fix/bug-description`
- 文档: `docs/doc-description`
- 重构: `refactor/refactor-description`

### 2. 开发和测试

```bash
# 进行代码修改
# ...

# 运行测试
pytest

# 检查代码风格
black src/ tests/
pylint src/

# 类型检查
mypy src/
```

### 3. 提交代码

```bash
# 添加修改的文件
git add .

# 提交（使用有意义的提交信息）
git commit -m "feat: 添加新功能描述"
```

提交信息规范：
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构
- `style:` 代码格式调整
- `chore:` 构建或辅助工具变动

### 4. 推送到远程

```bash
git push origin feature/your-feature-name
```

### 5. 创建Pull Request

1. 访问GitHub项目页面
2. 点击 "New Pull Request"
3. 选择您的分支
4. 填写PR描述：
   - 简要说明修改内容
   - 关联相关Issue（如果有）
   - 列出测试情况
   - 附上截图（如果适用）

### 6. 代码审查

- 等待维护者审查
- 根据反馈进行修改
- 保持PR更新

### 7. 合并

- PR通过审查后将被合并
- 删除功能分支

## 文档贡献

### 文档类型

- **用户文档**: 面向最终用户
  - README.md
  - INSTALL.md
  - USAGE.md
  - TROUBLESHOOTING.md

- **开发者文档**: 面向开发者
  - CONTRIBUTING.md（本文档）
  - ARCHITECTURE.md
  - 代码注释和文档字符串

- **规范文档**: 项目规范
  - .kiro/specs/transmitter-data-analyzer/requirements.md
  - .kiro/specs/transmitter-data-analyzer/design.md
  - .kiro/specs/transmitter-data-analyzer/tasks.md

### 文档编写规范

- 使用Markdown格式
- 提供清晰的标题层次
- 包含代码示例
- 使用截图说明（如果适用）
- 保持简洁明了

### 更新文档

```bash
# 创建文档分支
git checkout -b docs/update-usage-guide

# 修改文档
# ...

# 提交
git commit -m "docs: 更新使用指南"

# 推送并创建PR
git push origin docs/update-usage-guide
```

## 报告问题

### 报告Bug

创建Issue时请包含：

1. **问题描述**: 清晰描述问题
2. **重现步骤**: 详细的操作步骤
3. **预期行为**: 应该发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**:
   - 操作系统和版本
   - Python版本
   - Tesseract版本
   - 相关依赖版本
6. **错误信息**: 完整的错误堆栈
7. **日志**: 相关的日志片段
8. **截图**: 如果适用

### 功能请求

创建Issue时请包含：

1. **功能描述**: 清晰描述期望的功能
2. **使用场景**: 为什么需要这个功能
3. **建议实现**: 如果有想法，描述可能的实现方式
4. **替代方案**: 是否有其他解决方案

## 开发工作流

### 典型开发流程

```bash
# 1. 更新main分支
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/new-feature

# 3. 开发
# 编写代码
# 编写测试
# 更新文档

# 4. 运行测试
pytest
black src/ tests/
pylint src/

# 5. 提交
git add .
git commit -m "feat: 添加新功能"

# 6. 推送
git push origin feature/new-feature

# 7. 创建PR
# 在GitHub上创建Pull Request

# 8. 代码审查和修改
# 根据反馈进行修改

# 9. 合并
# PR被合并后，删除本地分支
git checkout main
git pull origin main
git branch -d feature/new-feature
```

### 持续集成

项目使用GitHub Actions进行持续集成：

- 自动运行测试
- 检查代码覆盖率
- 验证代码风格
- 跨平台测试（Mac、Windows、Linux）

## 代码审查清单

提交PR前请检查：

- [ ] 代码遵循PEP 8规范
- [ ] 所有函数都有文档字符串
- [ ] 添加了适当的类型注解
- [ ] 编写了单元测试
- [ ] 编写了属性测试（如果适用）
- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有遗留的调试代码
- [ ] 没有硬编码的路径或配置

## 获取帮助

如果您在贡献过程中遇到问题：

1. 查看现有文档
2. 搜索已有的Issue
3. 在Issue中提问
4. 联系项目维护者

## 行为准则

- 尊重所有贡献者
- 保持友好和专业
- 接受建设性批评
- 关注项目目标
- 帮助新贡献者

## 许可证

通过贡献代码，您同意您的贡献将在项目的MIT许可证下发布。

## 致谢

感谢所有为项目做出贡献的开发者！

---

再次感谢您的贡献！如有任何问题，请随时提出。
