# Harris 发射机数据分析器

一个用于从发射机监控系统截图中提取、分析和管理数据的桌面应用程序。

## 📥 快速下载

**Windows 用户可以直接下载打包好的 exe 文件，无需安装 Python 环境！**

[![下载最新版本](https://img.shields.io/github/v/release/Ethan915025/HarrisReader?label=下载最新版本&style=for-the-badge)](https://github.com/Ethan915025/HarrisReader/releases/latest)

### 下载步骤
1. 访问 [Releases 页面](https://github.com/Ethan915025/HarrisReader/releases)
2. 下载 `HarrisReader-Windows-vX.X.X.zip`
3. 解压后运行 `HarrisReader.exe`

## ✨ 功能特性

### 数据识别
- **🤖 AI 识别**（推荐）：使用阿里云百炼 API 识别，准确率高
- **⌨️ 手动输入**：完全手动填写数据

### 核心功能
- **📊 数据录入**：从截图中提取数据或手动输入
- **🔧 多设备管理**：支持管理多个发射机设备
- **📈 数据分析**：趋势分析、对比分析、异常检测
- **📉 数据可视化**：图表展示、趋势图、对比图
- **💾 数据导出**：导出为 CSV、Excel 格式

### 支持的数据项
系统支持提取 **71 个数据项**：
- **COMBINER 区域**：7 个温度数据（AZ, BZ, CZ, DZ, AB, CD, ABCD）
- **Z-Plane 区域**：64 个数据（4 个模块 × 8 行 × 2 列）
  - 每个模块包含 Current（电流）和 ISO Temp（温度）数据

## 🚀 快速开始

### 方式一：使用打包版本（推荐）

1. 下载并解压 exe 文件
2. 双击 `HarrisReader.exe` 启动
3. 开始使用

### 方式二：从源码运行

#### 1. 安装依赖

**Windows**:
```cmd
install_simple.bat
```

**macOS/Linux**:
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

#### 2. 启动程序

**Windows**:
```cmd
start_gui.bat
```

**macOS/Linux**:
```bash
python main.py
```

## 📖 使用说明

### 配置 API 识别（可选但推荐）

1. 打开程序，进入"系统设置"
2. 填写阿里云百炼 API 配置：
   - API Key：在阿里云百炼控制台获取
   - API URL：`https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
   - 模型名称：`qwen-vl-plus` 或 `qwen-vl-max`
   - Max Tokens：8000
3. 点击"保存 API 配置"
4. 点击"测试 API 连接"验证配置

**获取 API Key**：
1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 在控制台创建 API Key
4. 确保账户有余额（按使用量计费）

### 基本使用流程

1. **添加设备**
   - 点击"设备管理" → "添加设备"
   - 输入设备名称和描述

2. **录入数据**
   - 点击"数据录入"
   - 选择设备
   - 输入月份（格式：YYYY-MM）
   - 方式1：点击"浏览"选择截图 → 点击"API 识别"
   - 方式2：手动输入所有数据
   - 核对数据后点击"保存到数据库"

3. **查看分析**
   - **趋势分析**：查看数据随时间的变化趋势
   - **对比分析**：对比不同设备/时间的数据
   - **仪表板**：查看关键指标统计

4. **导出数据**
   - 点击"数据管理"
   - 选择要导出的数据
   - 点击"导出" → 选择格式（CSV/Excel）

## 📁 项目结构

```
HarrisReader/
├── main.py                 # 程序入口
├── start_gui.bat          # Windows 启动脚本
├── install_simple.bat     # Windows 安装脚本
├── config/                # 配置文件
│   └── api_config.json    # API 配置
├── src/                   # 源代码
│   ├── gui/              # 图形界面
│   │   ├── main_window.py
│   │   └── widgets/      # UI 组件
│   ├── api_ocr_extractor.py  # API 识别
│   ├── database.py       # 数据库管理
│   ├── device_manager.py # 设备管理
│   └── ...
├── docs/                  # 文档
└── tests/                 # 测试

```

## 🛠️ 系统要求

- **操作系统**：Windows 10+, macOS 10.14+, Linux
- **Python**：3.9 - 3.13（源码运行时需要）
- **内存**：至少 4GB RAM
- **磁盘空间**：至少 200MB

## 📝 依赖说明

### 核心依赖
- **PyQt6**：图形界面
- **pandas**：数据处理
- **matplotlib**：数据可视化
- **requests**：API 调用
- **Pillow**：图像处理

### 可选依赖
- **openpyxl**：Excel 导出（推荐安装）

## 🔧 故障排查

### Windows 用户常见问题

**Q1: 打包版 exe 双击没反应？**
- 右键"以管理员身份运行"
- 检查是否被杀毒软件拦截
- 查看解压目录是否包含所有文件

**Q2: 源码运行时提示找不到模块？**
```cmd
# 重新安装依赖
install_simple.bat
```

**Q3: API 连接失败？**
- 检查网络连接
- 确认 API Key 正确
- 确认账户有余额
- 尝试使用 VPN

### macOS/Linux 用户常见问题

**Q1: 权限错误？**
```bash
# 添加执行权限
chmod +x install_dependencies.sh
chmod +x start_gui.sh
```

**Q2: 依赖安装失败？**
```bash
# 使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### API 识别问题

**Q1: 识别结果不准确？**
- 确保截图清晰
- 尝试使用不同的模型（qwen-vl-max 更准确但更贵）
- 增加 max_tokens 到 10000
- 手动核对并修正数据

**Q2: 识别速度慢？**
- 正常情况下需要 10-30 秒
- 检查网络连接
- 考虑压缩图片大小

**Q3: API 配置保存后不生效？**
- 重启程序
- 或切换到其他页面再返回数据录入页面

## 📚 详细文档

- [API 参考文档](API_REFERENCE.md) - API 配置详细说明
- [Windows 安装指南](WINDOWS_SETUP.md) - Windows 详细安装步骤
- [Windows 故障排查](TROUBLESHOOTING_WINDOWS.md) - Windows 常见问题
- [GitHub 发布指南](GITHUB_RELEASE.md) - 如何发布新版本
- [GitHub 配置指南](GITHUB_SETUP.md) - 如何配置 GitHub 仓库

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [GitHub Issue](https://github.com/Ethan915025/HarrisReader/issues)
- 发送邮件至项目维护者

---

**版本**：1.3.4  
**最后更新**：2026-01-15
