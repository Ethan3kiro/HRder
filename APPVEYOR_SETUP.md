# AppVeyor 自动打包设置指南

## 📋 前置准备

AppVeyor 为开源项目提供免费的 Windows CI/CD 服务，非常适合打包 Windows 应用程序。

## 🚀 设置步骤

### 1. 注册 AppVeyor 账号

1. 访问 https://www.appveyor.com/
2. 点击 "Sign up for free"
3. 选择 "GitHub" 登录（使用你的 GitHub 账号）
4. 授权 AppVeyor 访问你的 GitHub 仓库

### 2. 添加项目

1. 登录 AppVeyor 后，点击 "New Project"
2. 在项目列表中找到 `HarrisReader`
3. 点击 "Add" 添加项目

### 3. 配置 GitHub Token（用于发布 Release）

#### 3.1 创建 GitHub Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 填写信息：
   - Note: `AppVeyor HarrisReader`
   - Expiration: 选择一个期限（建议 90 days 或 No expiration）
   - 勾选权限：
     - ✅ `repo` (完整仓库访问权限)
4. 点击 "Generate token"
5. **复制生成的 token**（只显示一次！）

#### 3.2 在 AppVeyor 中加密 Token

1. 访问 https://ci.appveyor.com/tools/encrypt
2. 粘贴你的 GitHub Token
3. 点击 "Encrypt"
4. 复制加密后的字符串

#### 3.3 更新 appveyor.yml

编辑 `appveyor.yml`，将 `YOUR_GITHUB_TOKEN_HERE` 替换为加密后的字符串：

```yaml
deploy:
  provider: GitHub
  auth_token:
    secure: 你的加密token  # 替换这里
  artifact: HarrisReader-Windows
  draft: false
  prerelease: false
  on:
    APPVEYOR_REPO_TAG: true
```

### 4. 推送配置文件

```bash
git add appveyor.yml
git commit -m "ci: add AppVeyor configuration for Windows builds"
git push github main
git push origin main
```

### 5. 触发构建

创建并推送一个新标签：

```bash
# 创建标签
git tag -a v1.2.1 -m "测试 AppVeyor 打包"

# 推送标签
git push github v1.2.1
git push origin v1.2.1
```

### 6. 查看构建进度

1. 访问 https://ci.appveyor.com/project/你的用户名/harrisreader
2. 查看构建日志
3. 等待构建完成（约 10-15 分钟）

### 7. 下载打包文件

构建完成后：

1. 在 AppVeyor 项目页面，点击最新的构建
2. 在 "Artifacts" 标签下载 ZIP 文件
3. 或者访问 GitHub Releases 页面下载

## 📊 AppVeyor vs GitHub Actions

| 特性 | AppVeyor | GitHub Actions |
|------|----------|----------------|
| 免费额度 | 开源项目无限制 | 2000 分钟/月（私有仓库） |
| Windows 支持 | ✅ 原生支持 | ✅ 支持 |
| 构建速度 | 中等 | 快 |
| 配置复杂度 | 简单 | 中等 |
| 社区支持 | 好 | 很好 |

## 🔧 常见问题

### Q1: 构建失败怎么办？

A: 查看 AppVeyor 构建日志，常见问题：
- 依赖安装失败：检查 requirements.txt
- PyInstaller 打包失败：检查隐藏导入
- 文件路径错误：确保使用 Windows 路径分隔符

### Q2: 如何手动触发构建？

A: 在 AppVeyor 项目页面，点击 "New build" 按钮。

### Q3: 构建时间太长怎么办？

A: AppVeyor 免费版构建时间限制为 60 分钟，通常足够。如果超时：
- 减少不必要的依赖
- 使用缓存加速构建

### Q4: 如何查看构建日志？

A: 在 AppVeyor 项目页面，点击构建记录，查看详细日志。

### Q5: 可以同时使用 GitHub Actions 和 AppVeyor 吗？

A: 可以！两者可以共存。建议：
- GitHub Actions：用于代码检查、测试
- AppVeyor：用于 Windows 打包

## 📝 配置文件说明

### appveyor.yml 关键配置

```yaml
# 只在打标签时构建
skip_non_tags: true

# Python 版本
environment:
  matrix:
    - PYTHON: "C:\\Python311"

# 构建产物
artifacts:
  - path: HarrisReader-Windows-*.zip
    name: HarrisReader-Windows

# 部署到 GitHub Releases
deploy:
  provider: GitHub
  auth_token:
    secure: 加密的token
  on:
    APPVEYOR_REPO_TAG: true
```

## 🎯 最佳实践

1. **使用标签触发构建**：避免每次提交都构建
2. **加密敏感信息**：使用 AppVeyor 加密工具
3. **缓存依赖**：加速构建（可选）
4. **测试本地打包**：推送前先本地测试
5. **监控构建状态**：及时发现问题

## 🔗 相关链接

- AppVeyor 官网：https://www.appveyor.com/
- AppVeyor 文档：https://www.appveyor.com/docs/
- 加密工具：https://ci.appveyor.com/tools/encrypt
- GitHub Token 设置：https://github.com/settings/tokens

## 📞 技术支持

如有问题，请在 GitHub Issues 中反馈：
https://github.com/Ethan915025/HarrisReader/issues

---

**祝构建顺利！** 🎉
