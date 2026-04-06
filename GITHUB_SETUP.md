# GitHub 仓库设置指南

## 🚀 快速开始

### 1. 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - Repository name: `HarrisReader`
   - Description: `发射机数据智能分析系统`
   - 选择 Public 或 Private
   - 不要勾选 "Initialize this repository with a README"
3. 点击 "Create repository"

### 2. 添加 GitHub 远程仓库

```bash
# 方式 A：如果还没有 remote
git remote add github https://github.com/你的用户名/HarrisReader.git

# 方式 B：如果已经有 origin（Gitee）
git remote rename origin gitee
git remote add github https://github.com/你的用户名/HarrisReader.git

# 查看远程仓库
git remote -v
```

### 3. 推送代码到 GitHub

```bash
# 推送主分支
git push github main

# 如果提示需要设置上游分支
git push -u github main
```

## 🎯 首次发布

### 创建第一个 Release

```bash
# 1. 确保所有更改已提交
git status

# 2. 创建版本标签
git tag -a v1.0.0 -m "首个正式版本

主要功能：
- 数据录入（手动/API/深度学习）
- 多设备管理
- 数据分析和可视化
- 数据导出

系统要求：
- Windows 10/11 64位
- 4GB+ 内存
"

# 3. 推送标签到 GitHub（触发自动打包）
git push github v1.0.0

# 4. 等待 5-10 分钟，GitHub Actions 会自动：
#    - 打包成 Windows exe
#    - 创建 Release
#    - 上传文件
```

### 查看打包进度

1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 查看 "Build Windows Executable" workflow
4. 等待完成（绿色✓）

### 下载打包文件

1. 进入 "Releases" 页面
2. 找到 v1.0.0
3. 下载 `HarrisReader-Windows-v1.0.0.zip`

## 📝 后续更新

### 发布新版本

```bash
# 1. 开发新功能
git add .
git commit -m "feat: 添加新功能"

# 2. 推送到 GitHub
git push github main

# 3. 创建新版本标签
git tag -a v1.1.0 -m "版本 1.1.0

新增功能：
- 功能 A
- 功能 B

Bug 修复：
- 修复问题 X
"

# 4. 推送标签（触发自动打包）
git push github v1.1.0
```

### 同时更新 Gitee

```bash
# 推送代码
git push gitee main
git push github main

# 推送标签
git push gitee v1.1.0
git push github v1.1.0
```

## 🔧 配置说明

### GitHub Actions 配置

文件位置：`.github/workflows/build-windows.yml`

**触发条件**：
- 推送 `v*` 标签（如 v1.0.0）
- 手动触发

**打包内容**：
- HarrisReader.exe（主程序）
- README.md
- API 配置文件
- 示例文件

### 本地测试打包

在推送到 GitHub 之前，建议先本地测试：

```bash
# Windows
build_exe.bat

# Linux/macOS
./build_exe.sh
```

## 🎨 自定义

### 修改 README 中的下载链接

编辑 `README.md`，将 `你的用户名` 替换为实际的 GitHub 用户名：

```markdown
[![下载最新版本](https://img.shields.io/github/v/release/你的用户名/HarrisReader?label=下载最新版本&style=for-the-badge)](https://github.com/你的用户名/HarrisReader/releases/latest)
```

### 添加项目图标

1. 准备 256x256 的 .ico 文件
2. 放在 `assets/icon.ico`
3. 修改 `.github/workflows/build-windows.yml` 中的 `--icon` 参数

### 修改打包选项

编辑 `.github/workflows/build-windows.yml`：

```yaml
# 单文件模式（当前）
--onefile

# 改为文件夹模式（体积更小）
--onedir
```

## 📊 版本号规范

使用语义化版本号：`vMAJOR.MINOR.PATCH`

- **MAJOR**（主版本号）：不兼容的 API 修改
- **MINOR**（次版本号）：向下兼容的功能性新增
- **PATCH**（修订号）：向下兼容的问题修正

示例：
- `v1.0.0` - 首个正式版本
- `v1.1.0` - 添加 API 识别功能
- `v1.1.1` - 修复 bug
- `v2.0.0` - 重大更新

## ⚠️ 注意事项

### 1. 不要推送敏感信息

确保 `.gitignore` 包含：
```
config/api_config.json
*.db
*.log
__pycache__/
```

### 2. 标签不可修改

一旦推送标签，不要修改或删除。如果需要修改：

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push github :refs/tags/v1.0.0

# 重新创建
git tag -a v1.0.0 -m "新的说明"
git push github v1.0.0
```

### 3. Actions 配额

GitHub Actions 免费配额：
- Public 仓库：无限制
- Private 仓库：2000 分钟/月

每次打包约需 5-10 分钟。

## 🐛 常见问题

### Q1: Actions 失败怎么办？

1. 查看 Actions 日志
2. 检查依赖是否正确
3. 确保 `main_gui.py` 存在
4. 检查 PyInstaller 参数

### Q2: exe 文件太大？

- 当前约 100-200MB（包含所有依赖）
- 可以使用 `--onedir` 模式
- 可以排除不需要的模块

### Q3: exe 运行报错？

- 检查是否缺少数据文件
- 确保 `--add-data` 路径正确
- 查看是否有隐藏导入未包含

### Q4: 如何手动触发打包？

1. 进入 GitHub 仓库
2. 点击 "Actions"
3. 选择 "Build Windows Executable"
4. 点击 "Run workflow"
5. 选择分支，点击 "Run workflow"

## 📚 相关文档

- [GitHub Actions 文档](https://docs.github.com/actions)
- [PyInstaller 文档](https://pyinstaller.org/)
- [语义化版本](https://semver.org/lang/zh-CN/)
- [GITHUB_RELEASE.md](GITHUB_RELEASE.md) - 详细发布指南

## 💡 最佳实践

1. **开发分支**：在 `dev` 分支开发，测试通过后合并到 `main`
2. **版本标签**：只在 `main` 分支打标签
3. **Release 说明**：详细列出变更内容
4. **测试打包**：推送前先本地测试
5. **保持同步**：定期同步 Gitee 和 GitHub

---

**准备好了吗？开始你的第一次发布吧！** 🎉

```bash
git tag -a v1.0.0 -m "首个正式版本"
git push github v1.0.0
```
