# 模板OCR快速开始指南

## 🎯 一分钟快速上手

本地模板OCR识别，专为老旧硬件优化，完全离线运行。

### 第一步：安装Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Windows:**
1. 下载：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装到：`C:\Program Files\Tesseract-OCR`
3. 添加到系统PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

验证安装：
```bash
tesseract --version
```

### 第二步：标定坐标（仅需一次）

```bash
cd /Users/Ethan/Desktop/HarrisReader
python3 tools/coordinate_calibrator.py 911-20251016.jpg
```

#### 标定步骤

1. **框选区域**
   - 鼠标左键点击两次：框选要识别的数字
   - 按 `空格键` 确认并输入名称

2. **命名规则**
   ```
   COMBINER 区域（7个）:
   COMBINER.AZ
   COMBINER.BZ
   COMBINER.CZ
   COMBINER.DZ
   COMBINER.AB
   COMBINER.CD
   COMBINER.ABCD
   
   Z-Plane A 区域（16个 = 8行×2列）:
   ZPLANE_A[0].Current
   ZPLANE_A[0].ISO_Temp
   ZPLANE_A[1].Current
   ZPLANE_A[1].ISO_Temp
   ...
   ZPLANE_A[7].Current
   ZPLANE_A[7].ISO_Temp
   
   同样标定 ZPLANE_B, ZPLANE_C, ZPLANE_D
   ```

3. **快捷键**
   - `空格` - 确认
   - `Z` - 撤销
   - `S` - 保存
   - `Q` - 退出

4. **保存**
   - 按 `S` 保存到 `config/template_coordinates.json`

### 第三步：使用GUI识别

```bash
python3 main_gui.py
```

1. 进入"数据录入"页面
2. 选择截图文件
3. 点击 **🖼️ 模板识别** 按钮
4. 等待识别完成（1-2秒）
5. 核对数据，保存

## 📊 三种识别方式对比

| 方式 | 网络 | 速度 | 硬件要求 | 准确率 | 适用场景 |
|------|------|------|----------|--------|----------|
| 🖼️ 模板识别 | ❌ 离线 | 快(1-2s) | 低 | 90%+ | **推荐** 老旧硬件、断网环境 |
| 🌐 API识别 | ✅ 需要 | 中(2-5s) | 极低 | 95%+ | 有网络、高准确率需求 |
| ✍️ 手动录入 | ❌ 离线 | 慢 | 无 | 100% | 备用方案 |

## 🔧 调试技巧

### 测试单个区域

```python
from pathlib import Path
from src.template_ocr_extractor import TemplateOCRExtractor

extractor = TemplateOCRExtractor()

# 测试特定坐标
result = extractor.test_single_region(
    image_path=Path('911-20251016.jpg'),
    coords=(100, 200, 150, 220),  # 实际坐标
    save_roi=True  # 保存ROI图像检查
)

print(f"识别结果: {result}")
```

### 查看识别详情

启用DEBUG日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 常见问题

**Q: 识别结果为空**
- 检查坐标是否准确
- 查看保存的ROI图像
- 尝试不同的预处理模式

**Q: 识别错误率高**
- 重新精确标定坐标
- 调整预处理参数
- 检查图像质量

**Q: 速度太慢**
- 使用 `simple` 预处理模式
- 关闭形态学处理
- 确保Tesseract正确安装

## 📁 文件结构

```
HarrisReader/
├── tools/
│   └── coordinate_calibrator.py    # 坐标标定工具 ⭐
├── src/
│   └── template_ocr_extractor.py   # 模板OCR提取器 ⭐
├── config/
│   └── template_coordinates.json   # 坐标模板（标定后生成）⭐
└── docs/
    └── TEMPLATE_OCR_GUIDE.md       # 详细文档
```

## 🚀 性能基准

**HP Z800 (Intel Xeon E5620, 8GB RAM):**
- 加载模板: <100ms
- 图像预处理: ~300ms
- OCR识别(71项): ~800ms
- **总计: ~1-2秒**

**现代电脑 (4核+):**
- **总计: <0.5秒**

## 📖 完整文档

详细说明请查看：`docs/TEMPLATE_OCR_GUIDE.md`

包含：
- 详细安装步骤
- 完整API参考
- 故障排除指南
- 性能优化建议
- 批量处理示例

## 💡 提示

1. **坐标标定是关键**
   - 紧贴数字边缘
   - 避免包含过多背景
   - 每个数字独立标定

2. **首次标定耗时较长**
   - 需要标定71个区域
   - 约需15-30分钟
   - 但只需标定一次

3. **布局变化需要重新标定**
   - 不同设备可能需要不同模板
   - 建议为每种布局创建模板

---

**版本：** v2.1.0  
**更新：** 2026-06-06
