# 安装深度学习依赖

## 📦 需要安装的包

```bash
pip install torch torchvision opencv-python albumentations scikit-learn
```

### 各包说明

1. **torch** (PyTorch)
   - 深度学习框架
   - 支持 M 芯片 MPS 加速
   - 大小：~200 MB

2. **torchvision**
   - PyTorch 图像处理工具
   - 大小：~10 MB

3. **opencv-python**
   - OpenCV 图像处理库
   - 大小：~90 MB

4. **albumentations**
   - 数据增强库
   - 大小：~5 MB

5. **scikit-learn**
   - 机器学习工具（用于数据分割）
   - 大小：~30 MB

**总大小**：约 335 MB

**预计时间**：10-15 分钟（取决于网速）

## 🚀 开始安装

运行以下命令：

```bash
pip install torch torchvision opencv-python albumentations scikit-learn
```

## ✅ 验证安装

安装完成后，运行以下命令验证：

```bash
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'MPS available: {torch.backends.mps.is_available()}')"
```

应该看到：
```
PyTorch: 2.x.x
MPS available: True
```

如果 MPS available 是 True，说明可以使用 M 芯片加速！

## 📝 安装完成后

告诉我安装结果，我会继续创建剩余的训练脚本！
