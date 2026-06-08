# 重构说明 - v2.0.0

## 概述

本次重构的目标是简化项目，只保留 **API 识别** 和 **手动输入** 两种数据录入方式，移除所有 OCR 和深度学习相关的代码和依赖。

## 主要变更

### 1. 已删除的文件

#### OCR 相关
- `src/ocr_extractor.py`
- `src/ocr_extractor_v2.py` ~ `src/ocr_extractor_v11.py`
- `src/dl_ocr_extractor.py`

#### 训练相关
- `training/` 目录及所有内容
- `models/` 目录
- `tools/` 目录

#### 文档
- `TRAINING.md`
- `QUICK_START_TRAINING.md`
- `QUICK_START_DL_TRAINING.md`
- `QUICK_START.md`
- `docs/INSTALL.md`
- `docs/USAGE.md`
- `docs/MAIN_ENTRY.md`
- 以及其他旧版本文档

#### 测试文件
- 所有 `tests/test_*.py` 文件（单元测试、集成测试、属性测试）

#### 备份文件
- `src/gui/widgets/data_entry_widget_old.py`

### 2. 已修改的文件

#### `requirements.txt`
**移除的依赖：**
- `pytesseract` - Tesseract OCR 库
- `opencv-python` - OpenCV 图像处理库（OCR 预处理用）

**保留的依赖：**
- `Pillow` - 基础图像处理（API 识别需要）
- `requests` - HTTP 请求（API 识别需要）
- 其他数据处理和可视化库

#### `src/gui/widgets/fullscreen_data_entry.py`
**主要更改：**
- 移除 `OCRWorker` 类，改为 `APIWorker` 类
- 移除 `dl_ocr_extractor` 参数，只保留 `api_ocr_extractor`
- 移除 "辅助录入" 按钮和相关功能
- 移除深度学习模型检查逻辑
- 简化为只支持 "API 识别" 和 "手动录入" 两种模式
- 更新所有相关的注释和提示文本

#### `src/gui/widgets/data_entry_widget.py`
**主要更改：**
- 完全重写，简化为只支持 API 和手动录入
- 移除所有 OCR 和深度学习相关代码
- 保持与原有功能的兼容性

#### `src/gui/main_window.py`
**主要更改：**
- 移除 `ocr_extractor` 和 `dl_ocr_extractor` 参数
- 更新所有子窗口的创建逻辑

#### `src/gui/widgets/settings_widget.py`
**主要更改：**
- 移除深度学习模型设置部分

#### `src/gui/widgets/dashboard_widget.py`
**主要更改：**
- 将 "OCR 自动识别" 改为 "AI API 自动识别"

### 3. 新创建的文件

#### `main_gui.py`
**描述：**
- GUI 应用的新入口文件
- 不依赖任何 OCR 或深度学习库
- 只初始化必要的组件（数据库、设备管理、API 识别等）

**正确的类名：**
- `TransmitterDatabase` (而不是 `Database`)
- `DataAnalyzer` (而不是 `Analyzer`)
- `DataVisualizer` (而不是 `Visualizer`)
- `DataExporter` (而不是 `Exporter`)
- 使用 `get_theme()` 函数 (而不是 `Styles.get_stylesheet()`)

#### `README.md`
**描述：**
- 全新的简化版 README
- 只介绍 API 识别和手动录入两种方式
- 更新了安装说明和使用指南

## 功能保留

### ✅ 保留的功能
1. **API 识别**
   - 阿里云百炼 API (qwen-vl-plus 模型)
   - 可扩展支持其他 API 提供商

2. **手动录入**
   - 完整的 71 个数据项模板
   - 数据验证和格式检查

3. **数据管理**
   - 数据库存储
   - 设备管理
   - 数据导出（Excel）

4. **数据分析**
   - 趋势分析
   - 对比分析
   - 数据可视化

### ❌ 移除的功能
1. **OCR 识别**
   - Tesseract OCR
   - 所有基于 OCR 的识别方法

2. **深度学习模型**
   - 本地训练的数字识别模型
   - 模型训练和坐标提取工具

## 启动方式

### 图形界面
```bash
python3 main_gui.py
```

### 命令行界面（保留原有功能）
```bash
python3 main.py
```

## 依赖安装

### 最小依赖（核心功能）
```bash
pip install -r requirements.txt
```

### GUI 依赖
```bash
pip install -r requirements-gui.txt
```

## 测试状态

- ✅ main_gui.py 导入测试通过
- ✅ 所有必要的类和函数可以正常导入
- ⚠️ 需要用户进行完整的功能测试

## 下一步

1. **用户测试**
   - 启动 GUI：`python3 main_gui.py`
   - 测试 API 识别功能
   - 测试手动录入功能
   - 测试数据管理功能

2. **提交到 Git**
   ```bash
   git add .
   git commit -m "v2.0.0: 重构项目，移除OCR和深度学习，只保留API识别和手动录入"
   git tag v2.0.0
   git push origin main --tags
   ```

3. **打包发布**
   - 使用 PyInstaller 打包 main_gui.py
   - 创建 GitHub Release

## 注意事项

1. **API 配置必需**
   - 必须正确配置 `config/api_config.json`
   - 需要有效的 API Key

2. **不兼容旧版本**
   - v2.0.0 移除了深度学习功能
   - 如果需要深度学习功能，请使用 v1.x 版本

3. **数据库兼容**
   - 数据库格式保持不变
   - 旧版本的数据可以无缝迁移

## 版本信息

- **版本号：** v2.0.0
- **重构日期：** 2026-06-06
- **主要贡献者：** Kiro AI Assistant
- **测试状态：** 待用户测试确认
