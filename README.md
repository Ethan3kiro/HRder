# 发射机数据分析器

一个用于从发射机监控系统截图中提取、分析和管理数据的桌面应用程序。

## 📥 快速下载

**Windows 用户可以直接下载打包好的 exe 文件，无需安装 Python 环境！**

[![下载最新版本](https://img.shields.io/github/v/release/Ethan915025/HarrisReader?label=下载最新版本&style=for-the-badge)](https://github.com/Ethan915025/HarrisReader/releases/latest)

### 下载步骤
1. 点击上方按钮或访问 [Releases 页面](https://github.com/Ethan915025/HarrisReader/releases)
2. 下载 `HarrisReader-Windows-vX.X.X.zip`
3. 解压后运行 `HarrisReader.exe`

> 💡 **提示**: 首次运行可能需要几秒钟启动，请耐心等待

## 功能特性

### 核心功能
- **数据录入**: 从截图中提取数据（支持 OCR 和深度学习模型辅助）
- **多设备管理**: 支持管理多个发射机设备的数据
- **数据分析**: 趋势分析、对比分析、异常检测
- **数据可视化**: 图表展示、趋势图、对比图
- **数据导出**: 导出为 CSV、Excel 等格式

### 数据提取方式
1. **API 识别** ⭐ 推荐：使用云端 AI 模型识别（准确率最高，无需训练）
2. **深度学习模型**: 使用训练好的 CNN 模型辅助识别（需要训练）
3. **传统 OCR**: 使用 Tesseract OCR 引擎识别数字（准确率低，不建议）
4. **手动输入**: 完全手动填写数据

### 数据项
系统支持提取 71 个数据项：
- **COMBINER 区域**: 7 个温度数据（AZ, BZ, CZ, DZ, AB, CD, ABCD）
- **Z-Plane 区域**: 64 个数据（4 个模块 × 8 行 × 2 列）
  - 每个模块包含 Current（电流）和 ISO Temp（温度）两列数据

## 快速开始

> 💡 **新手？** 查看 [快速开始指南](QUICK_START.md) 5分钟上手  
> 🪟 **Windows用户？** 查看 [Windows安装指南](WINDOWS_SETUP.md)  
> 🌐 **想用 API 识别？** 查看 [API配置说明](API配置说明.md)

### 安装

```bash
# Windows
install_simple.bat

# macOS/Linux
./install_dependencies.sh
```

### 配置 API 识别（可选，推荐）

如果您想使用云端 AI 进行图像识别：

1. 打开 `config/api_config.json`
2. 填入您的 API 密钥
3. 重启程序

**详细说明**: [API配置说明.md](API配置说明.md)

### 启动

```bash
# Windows
start_gui.bat

# macOS/Linux
python main_gui.py
```

### 使用

1. 添加设备
2. 录入数据（支持OCR/深度学习/手动）
3. 查看分析和趋势
4. 导出数据

详细说明请查看 [快速开始指南](QUICK_START.md)

## 项目结构

```
HarrisReader/
│
├── 📱 启动脚本
│   ├── main_gui.py                 # GUI 主程序入口
│   ├── main.py                     # CLI 主程序入口
│   ├── start_gui.bat               # Windows 启动脚本
│   ├── start_gui.sh                # macOS/Linux 启动脚本
│   └── verify_dependencies.py      # 依赖验证脚本
│
├── 📚 文档
│   ├── README.md                   # 项目概述和快速开始
│   ├── DEPENDENCIES.md             # 依赖安装详细说明
│   └── TRAINING.md                 # 模型训练完整指南
│
├── ⚙️ 配置文件
│   ├── requirements.txt            # 核心依赖
│   ├── requirements-gui.txt        # GUI 依赖
│   ├── requirements-training.txt   # 训练依赖
│   └── setup.py                    # 安装配置
│
├── 💻 系统核心代码 (src/)
│   ├── 🎨 图形界面 (gui/)
│   │   ├── main_window.py          # 主窗口
│   │   ├── styles.py               # 样式定义
│   │   └── widgets/                # UI 组件
│   │       ├── dashboard_widget.py         # 仪表板
│   │       ├── device_widget.py            # 设备管理
│   │       ├── data_entry_widget.py        # 数据录入
│   │       ├── comparison_widget.py        # 对比分析
│   │       ├── trend_widget.py             # 趋势分析
│   │       ├── data_management_widget.py   # 数据管理
│   │       ├── settings_widget.py          # 设置
│   │       └── fullscreen_data_entry.py    # 全屏录入
│   │
│   └── 🔧 核心模块
│       ├── database.py             # 数据库管理
│       ├── device_manager.py       # 设备管理器
│       ├── settings_manager.py     # 设置管理器
│       ├── ocr_extractor.py        # 传统 OCR 提取器
│       ├── dl_ocr_extractor.py     # 深度学习 OCR 提取器
│       ├── analyzer.py             # 数据分析器
│       ├── visualizer.py           # 数据可视化器
│       ├── exporter.py             # 数据导出器
│       └── ...                     # 其他核心模块
│
├── 🤖 模型文件 (models/)
│   ├── digit_ocr_model.pth         # 训练好的深度学习模型
│   ├── coordinates.json            # 坐标定义（71 个数据项）
│   └── ...                         # 训练历史和测试结果
│
├── 🎓 训练相关 (training/)
│   ├── 🛠️ 训练工具 (tools/)
│   │   ├── train_dl_model.py           # 训练深度学习模型
│   │   ├── test_dl_model.py            # 测试模型
│   │   ├── prepare_dl_data.py          # 准备训练数据
│   │   ├── data_labeling_tool.py       # 数据标注工具
│   │   ├── visualize_coordinates.py    # 坐标可视化
│   │   └── ...                         # 其他训练工具
│   │
│   └── 📁 训练数据 (training_data/)
│       ├── *_labels.json           # 标注文件
│       └── dl_dataset/             # 准备好的训练数据集
│
├── 🧪 测试 (tests/)
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   └── ...
│
├── 📖 文档 (docs/)
│   ├── ARCHITECTURE.md             # 架构说明
│   ├── USAGE.md                    # 使用说明
│   └── ...
│
└── 📝 示例和脚本
    ├── examples/                   # 示例代码
    └── scripts/                    # 实用脚本
```

### 关键文件说明

**启动应用**:
- Windows: `start_gui.bat`
- macOS/Linux: `start_gui.sh`

**核心功能**:
- 数据录入: `src/gui/widgets/data_entry_widget.py`
- 深度学习模型: `src/dl_ocr_extractor.py`
- 模型训练: `training/tools/train_dl_model.py`

**文档**:
- 快速开始: `README.md` (本文件)
- 依赖安装: `DEPENDENCIES.md`
- 模型训练: `TRAINING.md`

## 深度学习模型

系统包含一个可选的深度学习模型用于辅助数字识别。

### 模型信息
- **架构**: CNN (3 层卷积 + 3 层全连接)
- **输入**: 28x28 灰度图像
- **输出**: 单个数值（回归任务）
- **当前准确率**: ~12% (仅供参考，建议人工核对)

### 使用建议
由于模型准确率较低，建议：
1. 仅作为参考，不要完全依赖
2. 使用时务必人工核对所有数据
3. 或者关闭"使用辅助模型"开关，使用传统 OCR 或手动输入

### 改进模型
如需改进模型，参见 [TRAINING.md](TRAINING.md) 了解如何：
- 标注更多训练数据
- 调整坐标定义
- 重新训练模型

## 系统要求

- **操作系统**: Windows 10+, macOS 10.14+, Linux
- **Python**: 3.9 - 3.13
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 500MB

## 常见问题

### 安装问题
- **依赖安装失败**: 查看 [WINDOWS_SETUP.md](WINDOWS_SETUP.md) 或 [DEPENDENCIES.md](DEPENDENCIES.md)
- **Tesseract OCR 未找到**: 安装 Tesseract 或使用手动录入

### 功能问题
- **辅助录入按钮无法点击**: 需要安装 PyTorch 和训练模型，详见 [WINDOWS_SETUP.md](WINDOWS_SETUP.md#安装深度学习支持)
- **OCR 识别失败**: 使用深度学习模型或手动录入
- **数据保存失败**: 检查月份格式（YYYY-MM）和设备选择

更多问题请查看 [故障排除文档](TROUBLESHOOTING_WINDOWS.md)

## 技术栈

- **GUI**: PyQt6
- **OCR**: Tesseract OCR, pytesseract
- **深度学习**: PyTorch
- **数据处理**: pandas, numpy
- **图像处理**: OpenCV, Pillow
- **数据库**: SQLite
- **可视化**: matplotlib




---

**版本**: 0.1.0  
**最后更新**: 2026-01-15
