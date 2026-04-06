# GitHub 发布指南

本文档说明如何使用 GitHub Actions 自动打包和发布 Windows 可执行文件。

## 📋 前置准备

### 1. 创建 GitHub 仓库

```bash
# 如果还没有 GitHub 仓库，先创建一个
# 在 GitHub 网站上创建新仓库，然后：

# 添加 GitHub 远程仓库
git remote add github https://github.com/你的用户名/HarrisReader.git

# 或者如果已经有 origin，可以重命名
git remote rename origin gitee
git remote add github https://github.com/你的用户名/HarrisReader.git
```

### 2. 推送代码到 GitHub

```bash
# 推送所有分支和标签
git push github main
git push github --tags
```

## 🚀 自动打包发布

### 方式 1：通过 Git 标签触发（推荐）

每次创建新版本时，打一个标签即可自动触发打包：

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到 GitHub
git push github v1.0.0

# 或推送所有标签
git push github --tags
```

**自动流程**：
1. GitHub Actions 检测到新标签
2. 自动在 Windows 环境中打包
3. 生成 .exe 文件
4. 创建 GitHub Release
5. 上传打包文件到 Release

### 方式 2：手动触发

在 GitHub 网站上手动触发：

1. 进入仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build Windows Executable"
4. 点击 "Run workflow"
5. 选择分支，点击 "Run workflow"

## 📦 下载打包文件

### 从 Release 下载（推荐）

1. 进入仓库的 "Releases" 页面
2. 找到对应版本
3. 下载 `HarrisReader-Windows-vX.X.X.zip`

### 从 Actions 下载

1. 进入 "Actions" 标签
2. 选择对应的 workflow 运行
3. 在 "Artifacts" 部分下载

## 🔧 本地打包测试

在推送到 GitHub 之前，可以先在本地测试打包：

### Windows

```bash
# 运行打包脚本
build_exe.bat

# 测试生成的 exe
dist\HarrisReader.exe
```

### Linux/macOS

```bash
# 运行打包脚本
./build_exe.sh

# 测试生成的可执行文件
./dist/HarrisReader
```

## 📝 版本号规范

建议使用语义化版本号（Semantic Versioning）：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

示例：
- `v1.0.0` - 首个正式版本
- `v1.1.0` - 添加新功能（如 API 识别）
- `v1.1.1` - 修复 bug
- `v2.0.0` - 重大更新

## 🎯 发布流程示例

### 完整发布流程

```bash
# 1. 确保所有更改已提交
git status
git add .
git commit -m "feat: 添加新功能"

# 2. 推送到 GitHub
git push github main

# 3. 创建版本标签
git tag -a v1.1.0 -m "Release v1.1.0

新增功能：
- 云端 API 识别
- 数据同步优化
- 全屏模式改进

Bug 修复：
- 修复 Windows 全屏模式崩溃
- 修复数据同步问题
"

# 4. 推送标签（触发自动打包）
git push github v1.1.0

# 5. 等待 GitHub Actions 完成（约 5-10 分钟）
# 6. 在 GitHub Releases 页面查看发布
```

## 🔍 检查打包状态

### 查看 Actions 日志

1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择最新的 workflow 运行
4. 查看详细日志

### 常见问题

**问题 1：打包失败**
- 检查 requirements.txt 是否正确
- 查看 Actions 日志中的错误信息
- 确保所有依赖都兼容 Windows

**问题 2：exe 文件太大**
- 考虑使用 `--onedir` 而不是 `--onefile`
- 排除不必要的模块
- 使用 UPX 压缩

**问题 3：exe 运行报错**
- 检查是否缺少数据文件
- 确保 `--add-data` 路径正确
- 查看是否有隐藏导入未包含

## 📊 打包文件说明

打包后的 ZIP 文件包含：

```
HarrisReader-Windows-vX.X.X.zip
├── HarrisReader.exe          # 主程序
├── README.md                  # 使用说明
├── 如何使用API识别.md         # API 识别指南
├── API密钥配置快速参考.txt    # 快速参考
├── config/                    # 配置文件夹
│   ├── api_config.json       # API 配置（带占位符）
│   └── api_config.json.example
├── examples/                  # 示例文件
└── VERSION.txt               # 版本信息
```

## 🎨 自定义打包

### 修改图标

1. 准备 `.ico` 文件（推荐 256x256）
2. 放在 `assets/icon.ico`
3. 修改 `.github/workflows/build-windows.yml` 中的 `--icon` 参数

### 添加更多文件

在 workflow 文件的 "Create release package" 步骤中添加：

```yaml
- name: Create release package
  run: |
    mkdir release
    copy dist\HarrisReader.exe release\
    copy 你的文件.txt release\  # 添加这行
```

### 修改打包选项

编辑 `.github/workflows/build-windows.yml` 中的 PyInstaller 参数：

- `--onefile` → `--onedir`：打包成文件夹（体积更小）
- 添加 `--upx-dir=path`：使用 UPX 压缩
- 添加 `--debug`：生成调试信息

## 🌐 同时发布到 Gitee

如果想同时发布到 Gitee 和 GitHub：

```bash
# 推送到两个远程仓库
git push gitee main
git push github main

# 推送标签
git push gitee v1.0.0
git push github v1.0.0
```

## 📚 相关文档

- [PyInstaller 文档](https://pyinstaller.org/)
- [GitHub Actions 文档](https://docs.github.com/actions)
- [语义化版本](https://semver.org/lang/zh-CN/)

## 💡 提示

1. **首次发布前**，建议先手动触发测试一次
2. **大版本更新**时，建议在 Release 说明中详细列出变更
3. **保持标签和代码同步**，避免标签指向错误的提交
4. **定期清理旧的 Artifacts**，节省存储空间

---

**祝发布顺利！** 🎉
