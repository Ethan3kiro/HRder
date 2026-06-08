# Windows EXE 打包检查清单

## 📋 打包前准备

### 1. 环境要求
- [ ] Windows 10/11 电脑（物理机或虚拟机）
- [ ] Python 3.9-3.11 已安装
- [ ] pip 已安装并更新到最新版本
- [ ] 至少 5GB 可用硬盘空间

### 2. 必需软件
- [ ] Tesseract OCR - https://github.com/UB-Mannheim/tesseract/wiki
  - 安装路径: `C:\Program Files\Tesseract-OCR`
  - 确保安装中文和英文语言包
- [ ] Visual C++ Redistributable - https://aka.ms/vs/17/release/vc_redist.x64.exe

### 3. 代码准备
- [ ] 所有代码已推送到GitHub
- [ ] 本地代码是最新的v2.0.0
- [ ] 已测试主要功能正常运行

## 🔧 打包步骤

### 步骤1：获取代码（Windows上）

```bash
# 方式A：Git克隆
cd C:\
git clone https://github.com/Ethan915025/HarrisReader.git
cd HarrisReader

# 方式B：从Mac复制
# 使用U盘或网络共享复制整个文件夹
```

- [ ] 代码已在Windows上准备好

### 步骤2：安装Python依赖

```bash
cd C:\HarrisReader
pip install -r requirements.txt
pip install pyinstaller
```

- [ ] 所有依赖安装成功
- [ ] PyInstaller安装成功

### 步骤3：运行打包脚本

```bash
# 使用简化脚本
build_exe_simple.bat

# 或手动执行
python build_spec.py
pyinstaller HarrisReader.spec
```

- [ ] 打包过程无错误
- [ ] 生成了 `dist\HarrisReader\HarrisReader.exe`

### 步骤4：测试EXE

```bash
cd dist\HarrisReader
HarrisReader.exe
```

测试项目：
- [ ] 程序正常启动
- [ ] GUI界面显示正常
- [ ] 可以添加设备
- [ ] 可以选择图片文件
- [ ] 模板识别功能正常
- [ ] 数据可以保存到数据库
- [ ] 数据可以导出Excel

### 步骤5：准备发布包

创建文件夹结构：
```
HarrisReader-v2.0.0-Windows/
├── HarrisReader.exe
├── README.txt (→ WINDOWS_INSTALLATION_GUIDE.txt)
├── config/
│   ├── template_coordinates.json
│   ├── reference_point.json
│   └── api_config.json.example
├── tools/  (可选，用于坐标标定)
│   ├── coordinate_calibrator.py
│   ├── coordinate_adjuster.py
│   ├── mark_reference_point.py
│   └── image_aligner.py
├── docs/
│   ├── TEMPLATE_OCR_QUICKSTART.md
│   └── 工具使用快速参考.md
└── 依赖软件/
    ├── vcredist_x64.exe
    └── tesseract-ocr-setup.exe
```

- [ ] 文件夹结构已创建
- [ ] 所有文件已复制

### 步骤6：创建安装包

```bash
# 压缩为ZIP
# 右键 → 发送到 → 压缩(zipped)文件夹
# 重命名为: HarrisReader-v2.0.0-Windows.zip
```

- [ ] ZIP文件已创建
- [ ] 文件大小约 300-500MB

### 步骤7：测试安装包

在干净的Windows系统上：
- [ ] 解压ZIP文件
- [ ] 安装依赖软件
- [ ] 运行HarrisReader.exe
- [ ] 所有功能正常

## 📦 打包输出检查

### 必需文件检查

dist/HarrisReader/ 目录应包含：
- [ ] HarrisReader.exe (主程序)
- [ ] *.dll 文件（各种依赖库）
- [ ] PyQt6/ (Qt库)
- [ ] cv2/ (OpenCV库)
- [ ] config/ (配置文件夹)
- [ ] _internal/ (Python运行时)

### 大小检查
- [ ] EXE文件: ~10-20MB
- [ ] 整个dist文件夹: 300-500MB
- [ ] ZIP压缩后: 200-350MB

## 🎯 发布清单

### GitHub Release

- [ ] 推送代码到GitHub
- [ ] 创建标签 v2.0.0
- [ ] 上传 HarrisReader-v2.0.0-Windows.zip
- [ ] 编写Release说明
- [ ] 发布Release

### Release附件

- [ ] HarrisReader-v2.0.0-Windows.zip (主程序)
- [ ] SHA256SUMS.txt (校验文件)
- [ ] CHANGELOG.md (更新日志)

## ⚠️ 常见问题处理

### 打包失败

**问题：找不到模块**
```bash
# 解决：重新安装依赖
pip install --force-reinstall -r requirements.txt
```

**问题：Tesseract路径错误**
```python
# 修改 src/template_ocr_extractor.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**问题：EXE太大**
```bash
# 可以使用UPX压缩（可选）
# 下载UPX: https://upx.github.io/
pyinstaller --upx-dir=path/to/upx HarrisReader.spec
```

### 运行问题

**问题：VCRUNTIME140.dll缺失**
- 安装 Visual C++ Redistributable

**问题：程序启动慢**
- 这是正常的，首次启动需要10-15秒

**问题：模板识别不工作**
- 确保Tesseract已正确安装
- 检查坐标文件是否存在

## 📞 技术支持

如遇问题：
1. 查看 BUILD_EXE_WINDOWS.md 详细指南
2. 检查 build 和 dist 文件夹的错误日志
3. 联系：ethanzhang915025@gmail.com

## ✅ 最终检查

打包完成后：
- [ ] 在HP Z800上测试运行
- [ ] 识别准确率 >90%
- [ ] 性能满足要求（3-5秒/71项）
- [ ] 所有功能正常
- [ ] 用户手册已提供
- [ ] 发布到GitHub

---

**打包日期**: _______________  
**打包人员**: _______________  
**测试状态**: _______________  
**发布状态**: _______________
