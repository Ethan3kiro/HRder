# 🚀 深度学习 OCR 快速开始

## ⚡ 3 步开始训练

### 步骤 1: 调整坐标 ⚠️ 重要！

编辑 `tools/prepare_dl_data.py`，找到 `get_cell_coordinates()` 方法，调整坐标：

```python
# COMBINER 区域
combiner_base_y = 150  # ← 根据实际图像调整
combiner_x = 100       # ← 根据实际图像调整
combiner_spacing = 40  # ← 根据实际图像调整

# Z-Plane 区域
zplane_base_x = 400    # ← 根据实际图像调整
zplane_base_y = 150    # ← 根据实际图像调整
cell_width = 60        # ← 根据实际图像调整
cell_height = 25       # ← 根据实际图像调整
```

### 步骤 2: 运行训练

```bash
./train_dl_ocr.sh
```

### 步骤 3: 查看结果

```bash
# 查看训练曲线
open models/training_history.png

# 查看测试结果
cat models/test_results.json
```

## 📊 预期结果

- **训练时间**: 10-20 分钟（MPS 加速）
- **目标准确率**: > 85%
- **生成文件**: 
  - `models/digit_ocr_model.pth` - 训练好的模型
  - `models/training_history.png` - 训练曲线
  - `models/test_results.json` - 测试报告

## ✅ 成功标准

如果测试结果显示：
- ✅ 准确率 > 90% → 可以直接使用
- ⚠️ 准确率 80-90% → 可能需要更多数据
- ❌ 准确率 < 80% → 需要调整坐标或增加数据

## 🔧 如果失败

### 数据准备失败
→ 调整 `get_cell_coordinates()` 中的坐标

### 准确率太低
→ 标注更多图像（建议 15-20 张）

### 训练太慢
→ 确认 MPS 已启用: `python3 -c "import torch; print(torch.backends.mps.is_available())"`

## 📚 详细文档

查看 `DL_TRAINING_COMPLETE.md` 了解完整说明。
