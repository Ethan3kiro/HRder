# GitHub Actions 自动打包 Windows EXE 说明

## ✅ 已完成

### 1. 仓库配置
- ✅ 代码已推送到新仓库: `https://github.com/Ethan3kiro/HRder`
- ✅ GitHub Actions 工作流已配置
- ✅ 自动打包配置已就绪

### 2. 工作流文件
**文件位置**: `.github/workflows/build-windows-exe.yml`

**触发条件**:
- 推送到 main 或 master 分支
- 创建 Pull Request
- 手动触发（推荐用于测试）

## 🚀 使用方法

### 方法1: 手动触发（推荐）

1. 访问仓库: https://github.com/Ethan3kiro/HRder
2. 点击顶部 **Actions** 标签
3. 在左侧选择 **Build Windows EXE**
4. 点击右侧 **Run workflow** 按钮
5. 选择分支（通常是 main）
6. 点击绿色 **Run workflow** 按钮
7. 等待构建完成（约10-15分钟）

### 方法2: 自动触发

每次推送代码到 main 分支时，会自动触发构建：

```bash
git add .
git commit -m "your message"
git push origin main
```

## 📦 下载构建结果

### 从 Actions 页面下载

1. 进入 Actions 页面
2. 点击最新的成功构建（绿色✓）
3. 在页面底部找到 **Artifacts** 部分
4. 点击 **HarrisReader-Windows** 下载 ZIP 文件
5. 解压后得到 `HarrisReader.exe`

### 构建产物说明

下载的 ZIP 包含：
```
HarrisReader-Windows/
├── HarrisReader.exe       # 主程序
├── README.md              # 项目说明
└── 使用说明.txt          # Windows 使用说明
```

## 🔧 构建过程

工作流会自动完成以下步骤：

1. **环境准备**
   - 使用 Windows 最新版系统
   - 安装 Python 3.11
   - 安装 Tesseract OCR

2. **依赖安装**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-gui.txt
   pip install pyinstaller
   ```

3. **打包配置**
   - 使用 PyInstaller
   - 打包模式: 单文件 EXE
   - 包含所有必要的库和资源
   - 隐藏控制台窗口

4. **包含的模块**
   - PyQt6 (GUI)
   - OpenCV (图像处理)
   - Tesseract (OCR)
   - Pandas (数据处理)
   - Matplotlib/Plotly (可视化)
   - 所有其他依赖

5. **打包文件和文件夹**
   - config/ (配置文件)
   - models/ (模型文件)
   - docs/ (文档)

## ⚙️ 自定义配置

### 修改打包选项

编辑 `.github/workflows/build-windows-exe.yml` 中的 spec 文件部分：

```python
# 修改应用名称
name='HarrisReader',

# 显示控制台（调试用）
console=True,  # 改为 True

# 添加图标
icon='path/to/icon.ico',

# 添加更多数据文件
datas=[
    ('config', 'config'),
    ('models', 'models'),
    ('your_folder', 'your_folder'),  # 添加这一行
],
```

### 修改 Python 版本

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'  # 改为其他版本，如 '3.10'
```

## 🐛 常见问题

### 1. 构建失败

**检查日志**:
1. 进入失败的构建
2. 展开失败的步骤
3. 查看错误信息

**常见原因**:
- 依赖安装失败 → 检查 requirements.txt
- 模块导入错误 → 添加到 hiddenimports
- 文件缺失 → 检查 datas 配置

### 2. EXE 无法运行

**确认系统要求**:
- Windows 10 或更高版本
- 已安装 Tesseract OCR
- 有网络连接（首次运行可能需要）

**调试方法**:
1. 临时改为 `console=True`
2. 重新构建
3. 查看控制台错误信息

### 3. 缺少 Tesseract

**解决方案**:
```bash
# 使用 Chocolatey 安装
choco install tesseract

# 或下载安装包
# https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Actions 额度不足

**查看额度**:
- Settings → Billing → Actions minutes

**解决方案**:
- 使用手动触发，避免频繁构建
- 只在需要时构建
- 考虑使用自托管 runner

## 📊 构建状态徽章

在 README.md 中添加构建状态：

```markdown
![Build Status](https://github.com/Ethan3kiro/HRder/actions/workflows/build-windows-exe.yml/badge.svg)
```

效果：显示构建是否成功

## 🔐 发布 Release

### 自动创建 Release

打标签推送会自动创建 Release：

```bash
# 创建标签
git tag v1.0.0

# 推送标签
git push origin v1.0.0
```

工作流会自动：
1. 创建 GitHub Release
2. 上传 ZIP 包
3. 用户可以直接下载

### 手动创建 Release

1. 进入仓库 Releases 页面
2. 点击 **Draft a new release**
3. 输入标签（如 v1.0.0）
4. 填写说明
5. 上传从 Actions 下载的 ZIP
6. 点击 **Publish release**

## 📝 完整工作流程

### 开发 → 打包 → 测试

```bash
# 1. 本地开发和测试
python main_gui.py

# 2. 提交代码
git add .
git commit -m "feat: 新功能"
git push origin main

# 3. 等待 Actions 构建完成（自动）
# 或手动触发构建

# 4. 下载 Artifacts

# 5. 在 Windows 上测试 EXE

# 6. 如果测试通过，打标签发布
git tag v1.0.0
git push origin v1.0.0

# 7. 用户从 Releases 下载
```

## 🎯 下一步

### 立即测试

1. ✅ 访问: https://github.com/Ethan3kiro/HRder/actions
2. ✅ 点击 **Run workflow**
3. ✅ 等待构建完成
4. ✅ 下载并测试 EXE

### 优化建议

1. **添加应用图标**
   - 创建 `icon.ico` 文件
   - 在 spec 文件中指定

2. **版本号管理**
   - 在代码中添加 `__version__`
   - 在打包时使用

3. **减小文件大小**
   - 排除不必要的模块
   - 使用 UPX 压缩

4. **自动化测试**
   - 添加单元测试
   - 在打包前运行测试

## 📞 支持

如果遇到问题：
1. 查看 Actions 日志
2. 检查本文档的"常见问题"部分
3. 创建 Issue 报告问题

---

**配置完成时间**: 2026年7月15日  
**仓库地址**: https://github.com/Ethan3kiro/HRder  
**Actions 状态**: ✅ 已配置，可以开始使用
