# 测试和发布指南 - v2.0.0

## 已修复的启动问题

### 问题 1: PyQt6 属性错误
**错误：** `ApplicationAttribute has no attribute 'AA_EnableHighDpiScaling'`

**原因：** PyQt6 移除了这些属性，默认启用高DPI支持

**修复：** 移除了 `AA_EnableHighDpiScaling` 和 `AA_UseHighDpiPixmaps` 设置

### 问题 2: SettingsManager 参数错误
**错误：** `SettingsManager.__init__() missing 1 required positional argument: 'database'`

**原因：** 忘记传递 database 参数

**修复：** 修改 `main_gui.py`，正确传递 database 参数

## 当前状态

✅ **所有导入测试通过**
✅ **启动错误已修复**
⏳ **等待功能测试**

## 测试步骤

### 1. 启动应用
```bash
cd /Users/Ethan/Desktop/HarrisReader
python3 main_gui.py
```

### 2. 测试基本功能

#### 2.1 数据录入 - API 识别
1. 点击 "数据录入" 标签
2. 选择一张截图文件
3. 点击 "🌐 API 识别" 按钮
4. 检查识别结果是否正确
5. 填写月份和选择设备
6. 保存数据

#### 2.2 数据录入 - 手动输入
1. 点击 "数据录入" 标签
2. 选择一张截图文件
3. 点击 "✍️ 手动录入" 按钮
4. 手动填写数据
5. 保存数据

#### 2.3 全屏数据录入
1. 在数据录入页面点击 "全屏模式" 按钮
2. 测试 API 识别功能
3. 测试手动录入功能
4. 保存数据后返回

#### 2.4 数据管理
1. 点击 "数据管理" 标签
2. 查看已保存的数据
3. 测试编辑功能
4. 测试删除功能
5. 测试导出功能

#### 2.5 趋势分析
1. 点击 "趋势分析" 标签
2. 选择设备和时间范围
3. 查看趋势图表

#### 2.6 对比分析
1. 点击 "对比分析" 标签
2. 选择要对比的月份
3. 查看对比图表

#### 2.7 设置
1. 点击 "设置" 标签
2. 检查 API 配置显示是否正确
3. 测试 API 连接
4. 检查其他设置选项

### 3. 检查控制台输出
- 是否有错误或警告信息
- 日志是否正常记录

### 4. 检查数据库
```bash
# 查看数据库文件
ls -lh data/transmitter_data.db

# 可选：使用 sqlite3 查看数据
sqlite3 data/transmitter_data.db "SELECT * FROM monthly_data LIMIT 5;"
```

## 如果测试通过

### 1. 查看所有更改
```bash
git status
git diff
```

### 2. 添加所有更改
```bash
git add .
```

### 3. 提交更改
```bash
git commit -m "v2.0.0: 重构项目，移除OCR和深度学习，只保留API识别和手动录入

主要变更：
- 移除所有 OCR 和深度学习相关代码
- 删除 PyTorch、Tesseract 等依赖
- 简化为只支持 API 识别和手动录入
- 创建新的 main_gui.py 入口文件
- 更新所有相关文档

修复的问题：
- 修复 PyQt6 高DPI属性错误
- 修复 SettingsManager 参数错误
- 修复类名导入错误

详细内容请查看 REFACTORING_V2.0.0.md"
```

### 4. 创建标签
```bash
git tag -a v2.0.0 -m "Release v2.0.0: 移除OCR，只保留API识别和手动录入"
```

### 5. 推送到远程仓库
```bash
# 推送代码
git push origin main

# 推送标签
git push origin v2.0.0
```

### 6. 创建 GitHub Release

1. 访问 GitHub 仓库页面
2. 点击 "Releases" → "Draft a new release"
3. 选择 tag: `v2.0.0`
4. 填写 Release 标题: `v2.0.0 - 重构版本`
5. 复制以下内容到描述：

```markdown
# v2.0.0 - 重构版本

## 🎉 重大变更

本版本对项目进行了大规模重构，**移除了所有 OCR 和深度学习功能**，简化为只支持 **API 识别** 和 **手动录入** 两种方式。

## ✨ 主要特性

### 保留的功能
- ✅ **API 识别**（阿里云百炼 qwen-vl-plus）
- ✅ **手动录入**（完整的 71 项数据模板）
- ✅ **数据管理**（查看、编辑、删除）
- ✅ **数据分析**（趋势分析、对比分析）
- ✅ **数据可视化**（图表展示）
- ✅ **数据导出**（Excel 格式）

### 移除的功能
- ❌ Tesseract OCR 识别
- ❌ 深度学习模型识别
- ❌ 模型训练工具

## 📦 安装

### 基础依赖
```bash
pip install -r requirements.txt
```

### GUI 依赖
```bash
pip install -r requirements-gui.txt
```

## 🚀 启动

```bash
python3 main_gui.py
```

## ⚙️ 配置

需要配置 `config/api_config.json` 文件：

```json
{
  "provider": "dashscope",
  "api_key": "your-api-key-here",
  "model": "qwen-vl-plus",
  "max_tokens": 8000
}
```

## 📝 依赖变更

### 移除的依赖
- `pytesseract` - Tesseract OCR
- `opencv-python` - OpenCV（OCR 预处理用）
- `torch` 和 `torchvision` - PyTorch（深度学习）

### 保留的依赖
- `Pillow` - 图像处理
- `requests` - API 请求
- `PyQt6` - GUI 框架
- `pandas` - 数据处理
- `matplotlib` 和 `plotly` - 数据可视化

## 🐛 修复的问题

- 修复 PyQt6 高DPI 属性错误
- 修复 SettingsManager 初始化错误
- 修复类名导入错误

## 📚 文档

- [重构说明](REFACTORING_V2.0.0.md) - 详细的重构说明
- [API 参考](API_REFERENCE.md) - API 使用指南
- [故障排除](docs/TROUBLESHOOTING.md) - 常见问题

## ⚠️ 不兼容性说明

- **不向后兼容**：v2.0.0 移除了深度学习功能
- 如果需要深度学习功能，请使用 v1.x 版本
- 数据库格式保持不变，旧版本数据可以无缝迁移

## 🙏 致谢

感谢所有使用和支持本项目的用户！

---

**完整更改日志:** [REFACTORING_V2.0.0.md](REFACTORING_V2.0.0.md)
```

6. 点击 "Publish release"

## 如果测试失败

1. 记录详细的错误信息
2. 截图错误界面
3. 查看日志文件：`logs/` 目录
4. 告诉我具体的错误，我会帮你修复

## 打包（可选）

如果要创建独立可执行文件：

```bash
# 使用 PyInstaller 打包
pyinstaller --name="HarrisReader" \
            --windowed \
            --icon=icon.ico \
            --add-data "config:config" \
            main_gui.py
```

生成的文件在 `dist/HarrisReader/` 目录中。

## 注意事项

1. **API 配置必需**
   - 必须有有效的 `config/api_config.json`
   - API Key 必须有效

2. **数据库自动创建**
   - 首次运行会自动创建数据库
   - 数据库位置：`data/transmitter_data.db`

3. **日志文件**
   - 日志自动记录到 `logs/` 目录
   - 可以用于调试问题

## 回滚（如果需要）

如果 v2.0.0 有问题，可以回滚到上一个版本：

```bash
# 查看所有标签
git tag

# 检出上一个版本
git checkout v1.x.x  # 替换为实际的版本号
```

## 联系支持

如果遇到问题，请：
1. 查看日志文件
2. 查看 [故障排除文档](docs/TROUBLESHOOTING.md)
3. 在 GitHub 上创建 Issue
