# Windows EXE 打包指南

## 方法选择

由于GitHub Actions和AppVeyor额度已用完，需要使用以下替代方案：

### ✅ 方案1：借用Windows电脑打包（推荐）
### ✅ 方案2：使用Windows虚拟机
### ✅ 方案3：使用Wine在Mac上打包（实验性）

---

## 方案1：在Windows电脑上打包

### 步骤1：准备Windows环境

在Windows 10电脑上：

```bash
# 1. 安装Python 3.9-3.11（推荐3.10）
# 从 https://www.python.org/downloads/ 下载安装
# ⚠️ 注意勾选 "Add Python to PATH"

# 2. 验证安装
python --version
pip --version
```

### 步骤2：传输代码

**方式A：使用U盘**
1. 将整个 HarrisReader 文件夹复制到U盘
2. 插入Windows电脑
3. 复制到 `C:\HarrisReader`

**方式B：使用Git**
```bash
cd C:\
git clone https://github.com/Ethan915025/HarrisReader.git
cd HarrisReader
```

### 步骤3：安装依赖

```bash
cd C:\HarrisReader

# 安装依赖
pip install -r requirements.txt

# 安装Tesseract OCR
# 下载: https://github.com/UB-Mannheim/tesseract/wiki
# 安装到默认路径: C:\Program Files\Tesseract-OCR

# 安装PyInstaller
pip install pyinstaller
```

### 步骤4：运行打包脚本

```bash
# 运行现有的打包脚本
python build_spec.py
pyinstaller HarrisReader.spec

# 或使用批处理脚本
build_exe.bat
```

### 步骤5：测试EXE

```bash
cd dist\HarrisReader
HarrisReader.exe
```

### 步骤6：打包发布

```bash
# 压缩dist\HarrisReader文件夹
# 生成 HarrisReader-v2.0.0-Windows.zip
```

---

## 方案2：使用Windows虚拟机

### 在Mac上使用Parallels/VMware/VirtualBox

#### 1. 安装虚拟机软件

**免费选项：**
- VirtualBox: https://www.virtualbox.org/
- UTM: https://mac.getutm.app/ (Apple Silicon专用)

**付费选项：**
- Parallels Desktop (最佳性能)
- VMware Fusion

#### 2. 创建Windows虚拟机

```bash
# 所需资源
- Windows 10/11 ISO
- 硬盘空间: 至少30GB
- 内存: 至少4GB
- CPU核心: 2个
```

#### 3. 在虚拟机中打包

按照"方案1"的步骤在虚拟机中操作。

**文件传输：**
- 使用共享文件夹功能
- 将HarrisReader文件夹放在共享文件夹中

---

## 方案3：使用Wine（实验性，不推荐）

⚠️ 此方法可能不稳定，仅用于测试。

### 安装Wine

```bash
# 使用Homebrew安装
brew install --cask wine-stable

# 或者使用PlayOnMac
brew install --cask playonmac
```

### 使用PyInstaller通过Wine

```bash
# 安装Windows版Python到Wine
wine python-3.10.exe

# 在Wine中安装依赖
wine pip install -r requirements.txt
wine pip install pyinstaller

# 打包
wine pyinstaller HarrisReader.spec
```

⚠️ **警告**：
- Wine打包成功率不高
- 可能缺少Windows系统库
- 不推荐用于生产环境

---

## 快速打包脚本（Windows）

我已经为你准备好了打包脚本。在Windows上运行：

### build_exe_simple.bat

```batch
@echo off
echo ========================================
echo HarrisReader v2.0.0 打包工具
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [1/5] 检查依赖...
pip install -r requirements.txt

echo.
echo [2/5] 安装PyInstaller...
pip install pyinstaller

echo.
echo [3/5] 生成打包配置...
python build_spec.py

echo.
echo [4/5] 开始打包（这可能需要5-10分钟）...
pyinstaller HarrisReader.spec

echo.
echo [5/5] 检查输出...
if exist "dist\HarrisReader\HarrisReader.exe" (
    echo.
    echo ========================================
    echo ✓ 打包成功！
    echo ========================================
    echo.
    echo 输出位置: dist\HarrisReader\
    echo 主程序: HarrisReader.exe
    echo.
    echo 请测试程序是否正常运行：
    echo   cd dist\HarrisReader
    echo   HarrisReader.exe
    echo.
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
    echo.
)

pause
```

---

## 常见问题

### Q1: 缺少 VCRUNTIME140.dll

**解决方案：**
下载并安装 Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Q2: Tesseract OCR找不到

**解决方案：**
确保Tesseract安装在默认路径，或修改代码中的路径：

```python
# src/template_ocr_extractor.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Q3: EXE体积太大（>500MB）

这是正常的，因为包含了：
- Python解释器
- PyQt6库
- OpenCV
- Tesseract数据文件

可以使用UPX压缩：
```bash
pyinstaller --upx-dir=path/to/upx HarrisReader.spec
```

### Q4: 启动太慢

第一次启动会慢一些（解压临时文件），这是正常的。

### Q5: 在其他Windows电脑上无法运行

确保目标电脑已安装：
1. Visual C++ Redistributable
2. Tesseract OCR（或将其打包进EXE）

---

## 推荐工作流程

### 最佳实践：

1. **使用实体Windows电脑或虚拟机打包**
   - 最可靠
   - 可以完整测试
   - 避免跨平台问题

2. **打包后立即测试**
   ```bash
   cd dist\HarrisReader
   HarrisReader.exe
   ```

3. **在目标机器上测试**
   - 复制到HP Z800测试
   - 检查所有功能
   - 验证Tesseract OCR

4. **准备发布包**
   ```
   HarrisReader-v2.0.0-Windows/
   ├── HarrisReader.exe
   ├── config/
   │   ├── template_coordinates.json
   │   └── reference_point.json
   ├── README.txt
   └── INSTALL.txt
   ```

---

## 联系方式

如果遇到打包问题：
- GitHub Issues
- Email: ethanzhang915025@gmail.com

---

**建议**: 如果你有朋友/同事有Windows电脑，让他们帮忙打包是最快的方法！
