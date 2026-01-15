# 依赖安装说明

本文档详细说明如何在不同操作系统上安装项目依赖。

## 目录

- [Python 环境](#python-环境)
- [Python 依赖包](#python-依赖包)
- [Tesseract OCR](#tesseract-ocr)
- [深度学习依赖（可选）](#深度学习依赖可选)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

## Python 环境

### 要求
- Python 3.9 - 3.13
- pip (Python 包管理器)

### 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

### 安装 Python

#### Windows
1. 访问 [python.org](https://www.python.org/downloads/)
2. 下载 Python 3.11 或 3.12 安装程序
3. 运行安装程序，**勾选 "Add Python to PATH"**
4. 完成安装

#### macOS
```bash
# 使用 Homebrew
brew install python@3.11
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3-pip
```

## Python 依赖包

### 1. 核心依赖（必需）

```bash
pip install -r requirements.txt
```

**requirements.txt** 包含:
- pandas >= 2.0.0
- numpy >= 1.24.0
- Pillow >= 10.0.0
- pytesseract >= 0.3.10
- opencv-python >= 4.8.0

### 2. GUI 依赖（图形界面必需）

```bash
pip install -r requirements-gui.txt
```

**requirements-gui.txt** 包含:
- PyQt6 >= 6.5.0
- matplotlib >= 3.7.0

### 3. 训练依赖（仅模型训练需要）

```bash
pip install -r requirements-training.txt
```

**requirements-training.txt** 包含:
- torch >= 2.0.0
- torchvision >= 0.15.0
- tqdm >= 4.65.0

### 一次性安装所有依赖

```bash
# Windows
pip install -r requirements.txt -r requirements-gui.txt -r requirements-training.txt

# macOS/Linux
pip3 install -r requirements.txt -r requirements-gui.txt -r requirements-training.txt
```

## Tesseract OCR

Tesseract OCR 用于传统 OCR 识别。如果只使用深度学习模型或手动输入，可以跳过此步骤。

### Windows

1. **下载安装程序**:
   - 访问: https://github.com/UB-Mannheim/tesseract/wiki
   - 下载最新版本（推荐 5.x）

2. **安装**:
   - 运行安装程序
   - 记住安装路径（默认: `C:\Program Files\Tesseract-OCR`）
   - 安装时选择 "English" 语言包

3. **配置环境变量**（可选）:
   - 右键"此电脑" → "属性" → "高级系统设置"
   - "环境变量" → "系统变量" → "Path"
   - 添加: `C:\Program Files\Tesseract-OCR`

4. **验证安装**:
   ```cmd
   tesseract --version
   ```

### macOS

```bash
# 使用 Homebrew
brew install tesseract

# 验证安装
tesseract --version
```

### Linux (Ubuntu/Debian)

```bash
# 安装 Tesseract
sudo apt update
sudo apt install tesseract-ocr

# 安装英文语言包
sudo apt install tesseract-ocr-eng

# 验证安装
tesseract --version
```

### Linux (CentOS/RHEL)

```bash
# 安装 Tesseract
sudo yum install tesseract

# 验证安装
tesseract --version
```

## 深度学习依赖（可选）

如果需要使用深度学习模型辅助识别或训练新模型，需要安装 PyTorch。

### 自动安装

```bash
pip install -r requirements-training.txt
```

### 手动安装

访问 [PyTorch 官网](https://pytorch.org/get-started/locally/) 选择适合你系统的安装命令。

#### Windows (CPU 版本)
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### Windows (GPU 版本 - CUDA 11.8)
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### macOS (支持 Apple Silicon MPS)
```bash
pip install torch torchvision
```

#### Linux (CPU 版本)
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### Linux (GPU 版本 - CUDA 11.8)
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 验证 PyTorch 安装

```python
python -c "import torch; print(f'PyTorch {torch.__version__} installed')"
```

## 验证安装

运行以下脚本验证所有依赖是否正确安装：

```bash
python verify_dependencies.py
```

或手动检查：

```python
# 检查核心依赖
python -c "import pandas, numpy, PIL, cv2; print('✓ 核心依赖已安装')"

# 检查 GUI 依赖
python -c "from PyQt6.QtWidgets import QApplication; print('✓ GUI 依赖已安装')"

# 检查 Tesseract
python -c "import pytesseract; pytesseract.get_tesseract_version(); print('✓ Tesseract 已安装')"

# 检查 PyTorch（可选）
python -c "import torch; print(f'✓ PyTorch {torch.__version__} 已安装')"
```

## 常见问题

### Q: pip 安装失败，提示权限错误

**Windows**:
```bash
# 以管理员身份运行命令提示符
pip install -r requirements.txt
```

**macOS/Linux**:
```bash
# 使用 --user 标志
pip install --user -r requirements.txt

# 或使用 sudo（不推荐）
sudo pip install -r requirements.txt
```

### Q: pytesseract 找不到 Tesseract

**Windows**:
在代码中指定 Tesseract 路径：
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

或设置环境变量 `TESSDATA_PREFIX`。

**macOS/Linux**:
```bash
# 检查 Tesseract 路径
which tesseract

# 如果找不到，重新安装
brew reinstall tesseract  # macOS
sudo apt reinstall tesseract-ocr  # Linux
```

### Q: PyQt6 安装失败

尝试安装特定版本：
```bash
pip install PyQt6==6.5.0
```

或使用 conda：
```bash
conda install -c conda-forge pyqt
```

### Q: PyTorch 安装太慢

使用国内镜像源：
```bash
pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: OpenCV 导入错误

```bash
# 卸载所有 OpenCV 包
pip uninstall opencv-python opencv-python-headless opencv-contrib-python

# 重新安装
pip install opencv-python
```

### Q: 在 Python 3.14+ 上安装失败

某些包可能不支持最新的 Python 版本。建议使用 Python 3.11 或 3.12：

```bash
# 使用 pyenv 安装特定版本
pyenv install 3.11.7
pyenv local 3.11.7
```

## 虚拟环境（推荐）

使用虚拟环境可以避免依赖冲突：

### 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 在虚拟环境中安装依赖

```bash
pip install -r requirements.txt -r requirements-gui.txt
```

### 退出虚拟环境

```bash
deactivate
```

## 更新依赖

```bash
# 更新所有包到最新版本
pip install --upgrade -r requirements.txt -r requirements-gui.txt

# 更新单个包
pip install --upgrade pandas
```

## 依赖版本锁定

如果需要确保所有人使用相同版本的依赖：

```bash
# 生成精确版本列表
pip freeze > requirements-lock.txt

# 从锁定文件安装
pip install -r requirements-lock.txt
```

---

**提示**: 如果遇到其他问题，请查看项目的 GitHub Issues 或联系开发团队。
