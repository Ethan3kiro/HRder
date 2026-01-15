# 快速开始指南

## 5 分钟快速上手

### 第一步：安装依赖

**Windows 用户**:

双击运行 `install_simple.bat`

**macOS/Linux 用户**:

运行：
```bash
./install_dependencies.sh
```

### 第二步：启动应用

**Windows**:

双击运行 `start_gui.bat`，或运行：
```cmd
py main_gui.py
```

**macOS/Linux**:
```bash
python main_gui.py
```

### 第三步：开始使用

1. **添加设备**
   - 点击左侧菜单"设备管理"
   - 点击"添加设备"
   - 输入设备名称和描述

2. **录入数据**
   - 点击左侧菜单"数据录入"
   - 点击"浏览"选择截图文件
   - 可选：勾选"🤖 使用辅助模型"
   - 点击"OCR 识别"
   - 参考识别结果，手动填写/修正数据
   - 输入月份（格式：YYYY-MM）
   - 点击"保存到数据库"

3. **查看分析**
   - 点击"趋势分析"查看数据趋势
   - 点击"对比分析"对比不同设备/时间的数据

4. **导出数据**
   - 点击"数据管理"
   - 选择要导出的数据
   - 点击"导出"选择格式（CSV/Excel）

## 常见问题

**Q: 安装依赖失败？**
- 检查 Python 版本是否 3.9+
- Windows 用户尝试：`py -m pip install -r requirements.txt -r requirements-gui.txt`
- macOS/Linux 用户尝试：`pip install -r requirements.txt -r requirements-gui.txt`
- 参考 [DEPENDENCIES.md](DEPENDENCIES.md) 详细说明

**Q: 深度学习模型不可用？**
- 确保 `models/digit_ocr_model.pth` 文件存在
- 确保 `models/coordinates.json` 文件存在
- 安装 PyTorch：`pip install torch`

**Q: OCR 识别失败？**
- 确保 Tesseract OCR 已安装
- 尝试使用深度学习模型或手动输入

## 下一步

- 详细使用说明：[README.md](README.md)
- 依赖安装指南：[DEPENDENCIES.md](DEPENDENCIES.md)
- 模型训练指南：[TRAINING.md](TRAINING.md)

---

**提示**: 深度学习模型准确率较低（~12%），建议仅作为参考，务必人工核对所有数据。
