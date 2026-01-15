# 模型训练说明

本文档说明如何训练和改进深度学习 OCR 模型。

## 目录

- [概述](#概述)
- [训练流程](#训练流程)
- [数据标注](#数据标注)
- [坐标定位](#坐标定位)
- [模型训练](#模型训练)
- [模型测试](#模型测试)
- [模型集成](#模型集成)
- [常见问题](#常见问题)

## 概述

### 当前模型状态
- **准确率**: ~12% (非常低，仅供参考)
- **训练数据**: 11 张图像（781 个样本）
- **模型架构**: CNN (3 层卷积 + 3 层全连接)

### 改进建议
1. **增加训练数据**: 目标 50-100 张图像
2. **验证坐标定义**: 确保坐标准确覆盖数字
3. **调整模型架构**: 根据需要优化网络结构

## 训练流程

完整的训练流程包括以下步骤：

```
1. 收集图像
   ↓
2. 标注数据
   ↓
3. 验证/调整坐标
   ↓
4. 准备训练数据
   ↓
5. 训练模型
   ↓
6. 测试模型
   ↓
7. 集成到系统
```

## 数据标注

### 方法 1: AI 辅助标注（推荐）

使用 AI 助手快速标注数据：

1. **准备图像**:
   - 将截图放在项目根目录
   - 支持格式: JPG, PNG, BMP

2. **上传图像给 AI**:
   - 在聊天中上传图像
   - 告诉 AI: "请识别这张图像中的所有 71 个数字"

3. **保存标注**:
   ```bash
   # AI 会生成标注文件
   # 保存到 training/training_data/<filename>_labels.json
   ```

4. **验证标注**:
   - 打开生成的 JSON 文件
   - 检查数值是否正确
   - 确保格式正确（COMBINER: 整数，Current: 一位小数，Temp: 整数）

### 方法 2: 手动标注工具

使用内置的标注工具：

```bash
python training/tools/data_labeling_tool.py
```

**使用步骤**:
1. 加载图像
2. 点击每个数据项位置
3. 输入对应的数值
4. 保存标注文件

### 标注文件格式

```json
{
  "image_path": "/path/to/image.jpg",
  "labels": {
    "AZ": 42,
    "BZ": 50,
    "CZ": 51,
    "DZ": 56,
    "AB": 30,
    "CD": 40,
    "ABCD": 29,
    "Z-Plane A-Current-1": 7.2,
    "Z-Plane A-ISO Temp-1": 48,
    ...
  },
  "total_cells": 71,
  "labeled_cells": 71,
  "created_by": "AI Assistant",
  "created_at": "2026-01-15T19:47:08.350891",
  "coordinates": { ... }
}
```

## 坐标定位

坐标定义决定了从图像的哪个位置提取数字。准确的坐标是模型训练成功的关键。

### 当前坐标文件

坐标定义在 `models/coordinates.json`：

```json
{
  "AZ": [215, 224, 34, 23],  // [x, y, width, height]
  "BZ": [263, 224, 34, 23],
  ...
}
```

### 可视化坐标

查看坐标是否准确：

```bash
python training/tools/visualize_coordinates.py <image_path>
```

这会生成一张图像，显示所有坐标框的位置。

### 调整坐标

如果坐标不准确，使用交互式工具调整：

```bash
python training/tools/interactive_coordinate_adjuster.py
```

**使用方法**:
1. 加载图像
2. 选择要调整的数据项
3. 使用键盘调整坐标:
   - 方向键: 移动位置
   - Shift + 方向键: 调整大小
   - S: 保存
   - Q: 退出

### 批量调整坐标

如果需要调整特定区域的所有坐标：

```bash
python training/tools/individual_coordinate_adjuster.py
```

## 模型训练

### 1. 准备训练数据

```bash
python training/tools/prepare_dl_data.py
```

这会：
- 从标注文件中提取数字图像
- 应用数据增强（旋转、缩放、噪声等）
- 分割为训练集和验证集
- 保存到 `training/training_data/dl_dataset/`

### 2. 训练模型

```bash
python training/tools/train_dl_model.py
```

**训练参数**（在脚本中修改）:
- `num_epochs`: 训练轮次（默认 50）
- `batch_size`: 批次大小（默认 32）
- `learning_rate`: 学习率（默认 0.001）

**训练过程**:
- 显示训练进度条
- 自动保存最佳模型
- 生成训练曲线图
- 支持早停（验证损失不再下降时停止）

**输出文件**:
- `models/digit_ocr_model.pth`: 训练好的模型
- `models/training_history.png`: 训练曲线
- `models/training_history.json`: 训练历史数据

### 3. 监控训练

训练过程中会显示：
```
Epoch 1/50
  训练损失: 125.34, MAE: 8.45
  验证损失: 98.76, MAE: 7.23
  ✓ 保存最佳模型 (验证损失: 98.76)

Epoch 2/50
  训练损失: 87.65, MAE: 6.12
  验证损失: 76.54, MAE: 5.89
  ✓ 保存最佳模型 (验证损失: 76.54)
...
```

## 模型测试

### 1. 测试模型性能

```bash
python training/tools/test_dl_model.py
```

**输出**:
```
============================================================
测试结果
============================================================

总预测数: 781
正确预测: 93 (误差 < 2.0)
准确率: 11.9%

平均绝对误差 (MAE): 12.05
中位数误差 (P50): 4.36
90% 误差 (P90): 7.03
95% 误差 (P95): 7.03

============================================================
```

### 2. 详细测试报告

```bash
python training/tools/detailed_test_report.py
```

这会生成按单元格分类的详细报告，显示每个数据项的准确率。

### 3. 可视化提取结果

```bash
python training/tools/visualize_extracted_digits.py
```

这会生成图像，显示模型实际看到的内容，帮助诊断问题。

## 模型集成

训练好的模型会自动保存到 `models/` 目录。系统启动时会自动加载。

### 验证集成

1. 启动应用:
   ```bash
   python main_gui.py
   ```

2. 在数据录入页面:
   - 勾选"🤖 使用辅助模型"
   - 选择图像
   - 点击"OCR 识别"

3. 检查识别结果是否合理

## 训练技巧

### 提高准确率

1. **增加训练数据**:
   - 目标: 50-100 张图像
   - 确保数据多样性（不同日期、不同数值范围）

2. **验证坐标**:
   - 使用可视化工具检查坐标
   - 确保坐标框准确覆盖数字
   - 避免包含过多背景

3. **调整数据增强**:
   - 在 `prepare_dl_data.py` 中调整增强参数
   - 减少可能引入噪声的增强

4. **调整模型架构**:
   - 在 `train_dl_model.py` 中修改 `DigitCNN` 类
   - 尝试增加/减少层数
   - 调整神经元数量

5. **调整训练参数**:
   - 学习率: 太大可能不收敛，太小训练太慢
   - 批次大小: 根据内存调整
   - 训练轮次: 观察训练曲线，避免过拟合

### 诊断问题

**准确率很低（< 20%）**:
- 检查坐标是否准确
- 检查标注数据是否正确
- 可视化提取的数字图像

**训练损失不下降**:
- 降低学习率
- 检查数据是否正确加载
- 尝试更简单的模型架构

**验证损失上升（过拟合）**:
- 增加训练数据
- 减少数据增强
- 增加 Dropout
- 使用早停

**COMBINER 区域准确率为 0**:
- 重点检查 COMBINER 区域的坐标
- 可能坐标偏移或大小不对
- 使用交互式工具调整

## 文件结构

```
training/
├── tools/                          # 训练工具
│   ├── train_dl_model.py          # 训练脚本
│   ├── test_dl_model.py           # 测试脚本
│   ├── prepare_dl_data.py         # 数据准备
│   ├── data_labeling_tool.py      # 标注工具
│   ├── visualize_coordinates.py   # 坐标可视化
│   ├── visualize_extracted_digits.py  # 提取结果可视化
│   ├── interactive_coordinate_adjuster.py  # 交互式坐标调整
│   ├── individual_coordinate_adjuster.py   # 个别坐标调整
│   ├── detailed_test_report.py    # 详细测试报告
│   ├── fix_label_image_paths.py   # 修复标注文件路径
│   └── add_coordinates_to_labels.py  # 添加坐标到标注
│
└── training_data/                  # 训练数据
    ├── *_labels.json              # 标注文件
    └── dl_dataset/                # 准备好的训练数据
        ├── train/                 # 训练集
        └── val/                   # 验证集
```

## 常见问题

### Q: 训练需要多长时间？

取决于：
- 数据量: 11 张图像约 5-10 分钟
- 硬件: GPU 比 CPU 快 10-100 倍
- 训练轮次: 50 轮约 5-10 分钟（GPU）

### Q: 需要 GPU 吗？

不是必需的，但强烈推荐：
- CPU: 可以训练，但很慢
- GPU (CUDA): 快 10-100 倍
- Apple Silicon (MPS): 快 5-20 倍

### Q: 如何使用 GPU 训练？

系统会自动检测并使用可用的 GPU：
- NVIDIA GPU: 安装 CUDA 版本的 PyTorch
- Apple Silicon: 自动使用 MPS
- 无 GPU: 自动使用 CPU

### Q: 训练数据不够怎么办？

1. 收集更多截图
2. 使用 AI 辅助标注加速标注过程
3. 调整数据增强参数增加样本多样性

### Q: 模型准确率一直很低怎么办？

1. **首先检查坐标**:
   ```bash
   python training/tools/visualize_extracted_digits.py
   ```
   查看模型实际看到的内容

2. **检查标注数据**:
   打开几个 `*_labels.json` 文件，确认数值正确

3. **考虑替代方案**:
   - 使用传统 OCR (Tesseract)
   - 完全手动输入
   - 混合方法（OCR + 人工核对）

### Q: 如何备份/恢复模型？

**备份**:
```bash
cp models/digit_ocr_model.pth models/digit_ocr_model_backup.pth
cp models/coordinates.json models/coordinates_backup.json
```

**恢复**:
```bash
cp models/digit_ocr_model_backup.pth models/digit_ocr_model.pth
cp models/coordinates_backup.json models/coordinates.json
```

## 下一步

1. **收集更多数据**: 目标 50-100 张图像
2. **验证坐标**: 使用可视化工具检查
3. **重新训练**: 使用更多数据训练新模型
4. **测试评估**: 在真实数据上测试
5. **持续改进**: 根据反馈不断优化

---

**提示**: 模型训练是一个迭代过程，需要多次尝试和调整。不要期望一次就能达到完美效果。
