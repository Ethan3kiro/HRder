# Windows 安装指南

本文档提供 Windows 平台的详细安装步骤。

## 目录
- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [详细步骤](#详细步骤)
- [安装深度学习支持](#安装深度学习支持)
- [常见问题](#常见问题)

---

## 系统要求

- Windows 10 或更高版本
- Python 3.8 或更高版本
- 至少 2GB 可用磁盘空间
- 推荐 4GB 以上内存

---

## 快速安装

### 方法 1：使用安装脚本（推荐）

1. 下载项目到本地
2. 双击运行 `install_simple.bat`
3. 等待安装完成

### 方法 2：手动安装

```bash
# 1. 克隆仓库
git clone https://gitee.com/ethanzhang915025/harris-reader.git
cd harris-reader

# 2. 安装基础依赖
pip install -r requirements.txt

# 3. 安装 Tesseract OCR（见下文）
```

---

## 详细步骤

### 1. 安装 Python

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.8 或更高版本
3. 安装时勾选 "Add Python to PATH"
4. 验证安装：
   ```bash
   python --version
   ```

### 2. 安装 Tesseract OCR

1. 下载 Tesseract OCR for Windows：
   - 访问：https://github.com/UB-Mannheim/tesseract/wiki
   - 下载最新的 `.exe` 安装程序

2. 运行安装程序：
   - 推荐安装到默认路径：`C:\Program Files\Tesseract-OCR`
   - 确保勾选 "Add to PATH" 选项

3. 验证安装：
   ```bash
   tesseract --version
   ```

### 3. 安装项目依赖

```bash
# 进入项目目录
cd harris-reader

# 安装基础依赖
pip install -r requirements.txt

# 如果安装速度慢，可以使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 验证安装

```bash
# 运行依赖检查
python verify_dependencies.py

# 启动 GUI
python main_gui.py
```

---

## 安装深度学习支持

如果需要使用**辅助录入**功能（深度学习模型），需要额外安装 PyTorch。

### 自动安装（推荐）

双击运行 `install_pytorch_windows.bat`

### 手动安装

#### 方法 1：使用官方源（推荐）

```bash
# CPU 版本（适合大多数用户）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### 方法 2：使用国内镜像

```bash
# 清华镜像
pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 方法 3：访问官网获取命令

1. 访问 [PyTorch 官网](https://pytorch.org/get-started/locally/)
2. 选择配置：
   - PyTorch Build: **Stable**
   - Your OS: **Windows**
   - Package: **Pip**
   - Language: **Python**
   - Compute Platform: **CPU** (如果有NVIDIA显卡可选择CUDA版本)
3. 复制生成的安装命令并执行

### 验证 PyTorch 安装

```bash
python -c "import torch; print('PyTorch 版本:', torch.__version__)"
```

### 训练模型

安装 PyTorch 后，需要训练模型才能使用辅助录入功能：

```bash
# 查看训练指南
type QUICK_START_DL_TRAINING.md

# 或直接开始训练
python training/tools/train_dl_model.py
```

---

## 常见问题

### 1. pip 安装失败

**问题：** pip 安装依赖时出错

**解决方案：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. PyTorch 安装失败

**问题：** 提示 "No matching distribution found for torchvision"

**解决方案：**
```bash
# 使用官方 CPU 版本源
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 或访问官网获取最新安装命令
# https://pytorch.org/get-started/locally/
```

### 3. Tesseract OCR 未找到

**问题：** 运行时提示找不到 Tesseract

**解决方案：**
1. 确认已安装 Tesseract OCR
2. 添加到系统 PATH：
   - 右键"此电脑" → "属性" → "高级系统设置"
   - "环境变量" → 编辑 "Path"
   - 添加：`C:\Program Files\Tesseract-OCR`
3. 重启命令提示符

### 4. 辅助录入按钮无法点击

**原因：** 深度学习模型不可用

**解决方案：**
1. 将鼠标悬停在按钮上查看具体原因
2. 根据提示安装 PyTorch 或训练模型
3. 参考 `QUICK_START_DL_TRAINING.md` 文档

### 5. 中文显示乱码

**解决方案：**
```bash
# 设置环境变量
set PYTHONIOENCODING=utf-8

# 然后运行程序
python main_gui.py
```

---

## 下一步

安装完成后，请参考：
- [快速开始](QUICK_START.md) - 基本使用教程
- [深度学习训练](QUICK_START_DL_TRAINING.md) - 训练辅助录入模型
- [故障排除](TROUBLESHOOTING_WINDOWS.md) - 更多问题解决方案

---

## 获取帮助

如果遇到问题：
1. 查看 [故障排除文档](TROUBLESHOOTING_WINDOWS.md)
2. 查看项目 Issues
3. 联系开发者
