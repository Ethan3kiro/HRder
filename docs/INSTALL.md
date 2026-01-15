# 安装指南

本文档提供发射机数据分析器在Mac和Windows系统上的详细安装步骤。

## 目录

- [系统要求](#系统要求)
- [Mac系统安装](#mac系统安装)
- [Windows系统安装](#windows系统安装)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

## 系统要求

### 必需组件

- **Python**: 3.8 或更高版本
- **Tesseract-OCR**: 4.0 或更高版本
- **磁盘空间**: 至少 500MB 可用空间
- **内存**: 建议 2GB 或以上

### Python依赖包

所有Python依赖包都列在 `requirements.txt` 文件中，主要包括：

- pytesseract: OCR文本识别
- Pillow: 图像处理
- pandas: 数据处理
- matplotlib: 静态图表
- plotly: 交互式图表
- openpyxl: Excel文件处理
- hypothesis: 属性测试（开发环境）
- pytest: 单元测试（开发环境）

## Mac系统安装

### 1. 安装Python

Mac系统通常预装Python，但可能版本较旧。建议使用Homebrew安装最新版本：

```bash
# 安装Homebrew（如果尚未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python 3
brew install python3

# 验证Python版本
python3 --version
```

### 2. 安装Tesseract-OCR

使用Homebrew安装Tesseract：

```bash
# 安装Tesseract
brew install tesseract

# 验证安装
tesseract --version
```

Tesseract将被安装到 `/opt/homebrew/bin/tesseract` (Apple Silicon) 或 `/usr/local/bin/tesseract` (Intel)。

### 3. 下载项目代码

```bash
# 克隆或下载项目到本地
cd ~/Documents
git clone <repository-url> transmitter-data-analyzer
cd transmitter-data-analyzer
```

### 4. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 5. 安装Python依赖

```bash
# 安装生产依赖
pip install -r requirements.txt

# 如果需要开发和测试（可选）
pip install -r requirements-dev.txt
```

### 6. 验证安装

```bash
# 检查所有依赖
python3 main.py --check-deps

# 运行测试（可选）
pytest
```

## Windows系统安装

### 1. 安装Python

1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载Python 3.8或更高版本的Windows安装程序
3. 运行安装程序，**务必勾选 "Add Python to PATH"**
4. 选择 "Install Now" 完成安装

验证安装：

```cmd
# 打开命令提示符（cmd）或PowerShell
python --version
```

### 2. 安装Tesseract-OCR

#### 方法一：使用安装程序（推荐）

1. 访问 [Tesseract Windows版本](https://github.com/UB-Mannheim/tesseract/wiki)
2. 下载最新的安装程序（例如：`tesseract-ocr-w64-setup-5.3.0.exe`）
3. 运行安装程序
4. 记住安装路径（默认：`C:\Program Files\Tesseract-OCR`）
5. 将Tesseract添加到系统PATH：
   - 右键"此电脑" → "属性" → "高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 点击"新建"，添加：`C:\Program Files\Tesseract-OCR`
   - 点击"确定"保存

#### 方法二：使用Chocolatey

如果您已安装Chocolatey包管理器：

```powershell
# 以管理员身份运行PowerShell
choco install tesseract
```

验证安装：

```cmd
tesseract --version
```

### 3. 下载项目代码

```cmd
# 在命令提示符中
cd C:\Users\YourUsername\Documents
git clone <repository-url> transmitter-data-analyzer
cd transmitter-data-analyzer
```

或者直接下载ZIP文件并解压。

### 4. 创建虚拟环境（推荐）

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

### 5. 安装Python依赖

```cmd
# 安装生产依赖
pip install -r requirements.txt

# 如果需要开发和测试（可选）
pip install -r requirements-dev.txt
```

### 6. 验证安装

```cmd
# 检查所有依赖
python main.py --check-deps

# 运行测试（可选）
pytest
```

## 验证安装

### 运行依赖检查

```bash
python3 main.py --check-deps
```

成功的输出应该类似：

```
正在检查系统依赖...

✓ Python 3.10.0 已安装
✓ Tesseract-OCR 5.3.0 已安装
✓ 所有Python包已安装

所有依赖检查通过！系统已准备就绪。
```

### 运行示例测试

```bash
# 生成示例数据
python3 scripts/generate_sample_data.py

# 使用示例数据库启动系统
python3 main.py --db-path examples/sample_transmitter_data.db
```

### 运行测试套件

```bash
# 运行所有测试
pytest

# 运行快速测试（跳过慢速测试）
pytest -m "not slow"
```

## 常见问题

### Q1: Python命令不可用

**问题**: 运行 `python` 或 `python3` 时提示命令未找到。

**解决方案**:
- **Mac**: 确保已安装Python 3，使用 `python3` 而不是 `python`
- **Windows**: 重新安装Python，确保勾选 "Add Python to PATH"
- 重启终端或命令提示符

### Q2: Tesseract未找到

**问题**: 系统提示找不到Tesseract或pytesseract错误。

**解决方案**:

**Mac**:
```bash
# 检查Tesseract是否安装
which tesseract

# 如果未安装
brew install tesseract
```

**Windows**:
1. 确认Tesseract已安装到 `C:\Program Files\Tesseract-OCR`
2. 检查PATH环境变量是否包含Tesseract路径
3. 重启命令提示符

### Q3: pip安装依赖失败

**问题**: 运行 `pip install -r requirements.txt` 时出错。

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像（如果网络慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 逐个安装依赖以定位问题
pip install pytesseract
pip install Pillow
pip install pandas
# ... 等等
```

### Q4: 权限错误

**问题**: Mac/Linux上提示权限不足。

**解决方案**:
```bash
# 不要使用sudo安装到系统Python
# 使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Q5: 虚拟环境激活失败

**问题**: Windows PowerShell提示无法运行脚本。

**解决方案**:
```powershell
# 以管理员身份运行PowerShell
Set-ExecutionPolicy RemoteSigned

# 然后激活虚拟环境
venv\Scripts\activate
```

### Q6: 数据库路径问题

**问题**: 找不到默认数据库路径。

**解决方案**:
- 系统会自动在 `~/Documents` (Mac) 或 `C:\Users\用户名\Documents` (Windows) 创建数据库
- 可以使用 `--db-path` 参数指定自定义路径
- 确保目标目录有写入权限

### Q7: 图像处理错误

**问题**: OCR提取时出现图像格式错误。

**解决方案**:
```bash
# 确保Pillow正确安装
pip install --upgrade Pillow

# 支持的图像格式：PNG, JPG, JPEG, BMP, TIFF
# 如果图像格式不支持，使用图像编辑器转换为PNG
```

## 升级和更新

### 更新Python依赖

```bash
# 激活虚拟环境
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 更新所有依赖
pip install --upgrade -r requirements.txt
```

### 更新Tesseract

**Mac**:
```bash
brew upgrade tesseract
```

**Windows**:
下载并安装最新版本的安装程序。

## 卸载

### 卸载Python依赖

```bash
# 如果使用虚拟环境，直接删除虚拟环境目录
rm -rf venv  # Mac/Linux
rmdir /s venv  # Windows
```

### 卸载Tesseract

**Mac**:
```bash
brew uninstall tesseract
```

**Windows**:
通过"控制面板" → "程序和功能"卸载Tesseract-OCR。

## 获取帮助

如果遇到本文档未涵盖的问题：

1. 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 获取更多故障排查信息
2. 查看项目的Issue列表
3. 提交新的Issue并附上详细的错误信息

## 下一步

安装完成后，请参考：
- [USAGE.md](USAGE.md) - 详细使用说明
- [examples/README.md](../examples/README.md) - 示例数据说明
