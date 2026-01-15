# 主入口文件文档

## 概述

`main.py` 是发射机数据分析器的主入口文件，负责程序的启动、初始化和顶层异常处理。

## 功能特性

### 1. 命令行参数解析

使用 `argparse` 模块提供丰富的命令行参数支持：

```bash
# 显示版本信息
python3 main.py --version

# 显示帮助信息
python3 main.py --help

# 指定数据库路径
python3 main.py --db-path /path/to/database.db

# 设置日志级别
python3 main.py --log-level DEBUG

# 指定日志目录
python3 main.py --log-dir /path/to/logs

# 检查系统依赖
python3 main.py --check-deps

# 不记录日志到文件
python3 main.py --no-log-file
```

### 2. 日志系统初始化

- 自动配置文件日志和控制台日志
- 支持自定义日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 支持自定义日志目录
- 可选择仅输出到控制台

### 3. 依赖检测

- 启动时自动检测系统依赖
- 检测 Tesseract-OCR 安装状态
- 检测 Python 包依赖
- 提供详细的安装指引
- 支持独立的依赖检测模式（--check-deps）

### 4. CLI 启动

- 初始化所有必需模块
- 启动交互式命令行界面
- 处理用户中断（Ctrl+C）

### 5. 异常处理

- 捕获并记录所有顶层异常
- 提供友好的错误消息
- 确保程序优雅退出
- 记录详细的错误日志

## 执行流程

```
1. 解析命令行参数
   ↓
2. 处理特殊参数（--version, --check-deps）
   ↓
3. 初始化日志系统
   ↓
4. 检测系统依赖
   ↓
5. 询问用户是否继续（如果有缺失依赖）
   ↓
6. 启动 CLI 界面
   ↓
7. 处理异常和清理
   ↓
8. 程序退出
```

## 使用示例

### 基本使用

```bash
# 使用默认配置启动
python3 main.py
```

### 自定义配置

```bash
# 使用自定义数据库和日志级别
python3 main.py --db-path ~/my_data.db --log-level DEBUG
```

### 依赖检查

```bash
# 仅检查依赖，不启动程序
python3 main.py --check-deps
```

### 开发调试

```bash
# 启用 DEBUG 日志，不记录到文件
python3 main.py --log-level DEBUG --no-log-file
```

## 退出代码

- `0`: 正常退出
- `1`: 发生错误或依赖不满足

## 环境变量

程序通过命令行参数传递配置，不依赖环境变量。所有配置都可以通过命令行参数指定。

## 依赖要求

### 必需依赖

- Python 3.8+
- pytesseract
- Pillow (PIL)
- pandas
- numpy
- matplotlib
- plotly
- openpyxl
- xlsxwriter

### 可选依赖

- Tesseract-OCR（用于 OCR 功能）

## 故障排除

### 问题：Tesseract-OCR 未找到

**解决方案：**
```bash
# Mac
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
```

### 问题：Python 包缺失

**解决方案：**
```bash
pip install -r requirements.txt
```

### 问题：权限错误

**解决方案：**
```bash
# 确保有写入权限
chmod +x main.py

# 或使用 python3 显式运行
python3 main.py
```

## 开发说明

### 添加新的命令行参数

在 `parse_arguments()` 函数中添加：

```python
parser.add_argument(
    '--my-option',
    type=str,
    help='我的选项说明'
)
```

### 修改启动流程

在 `main()` 函数中修改相应的逻辑。

### 添加新的异常处理

在 `main()` 函数的 try-except 块中添加新的异常类型。

## 相关文件

- `src/cli.py`: CLI 界面实现
- `src/logging_config.py`: 日志配置
- `src/dependency_checker.py`: 依赖检测
- `src/config.py`: 配置管理
- `src/exceptions.py`: 异常定义

## 版本历史

- v0.1.0: 初始版本
  - 实现基本的命令行参数解析
  - 实现日志系统初始化
  - 实现依赖检测
  - 实现 CLI 启动
  - 实现顶层异常处理
