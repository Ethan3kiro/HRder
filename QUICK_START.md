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

**Q: 安装失败？**  
→ 查看 [WINDOWS_SETUP.md](WINDOWS_SETUP.md) 或 [TROUBLESHOOTING_WINDOWS.md](TROUBLESHOOTING_WINDOWS.md)

**Q: 辅助录入按钮无法点击？**  
→ 需要安装 PyTorch 和训练模型，详见 [WINDOWS_SETUP.md](WINDOWS_SETUP.md#安装深度学习支持)

**Q: OCR 识别失败？**  
→ 使用深度学习模型或手动输入

## 下一步

- 详细功能说明：[README.md](README.md)
- Windows 安装：[WINDOWS_SETUP.md](WINDOWS_SETUP.md)
- 模型训练：[QUICK_START_DL_TRAINING.md](QUICK_START_DL_TRAINING.md)
- 故障排除：[TROUBLESHOOTING_WINDOWS.md](TROUBLESHOOTING_WINDOWS.md)

---

**提示**: 深度学习模型准确率较低（~12%），建议仅作为参考，务必人工核对所有数据。
