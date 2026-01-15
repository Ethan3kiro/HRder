# Windows 深度学习依赖安装指南

如果你需要使用深度学习模型功能，需要额外安装 PyTorch 和相关依赖。

## 快速安装（推荐）

### 方法1：使用 py 启动器（最可靠）

```cmd
py -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
py -m pip install -r requirements-training.txt
```

### 方法2：直接使用 pip

如果 Python 已添加到 PATH：

```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-training.txt
```

### 方法3：使用完整路径

找到你的 Python 安装路径（通常在以下位置之一）：
- `C:\Python39\`
- `C:\Python310\`
- `C:\Python311\`
- `C:\Python312\`
- `%LOCALAPPDATA%\Programs\Python\Python39\`

然后运行：

```cmd
"C:\Python311\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
"C:\Python311\python.exe" -m pip install -r requirements-training.txt
```

## 验证安装

运行以下命令验证 PyTorch 是否安装成功：

```cmd
py -c "import torch; print(f'PyTorch {torch.__version__} 安装成功')"
```

## 常见问题

### 问题1：找不到 Python 命令

**解决方案**：使用 `py` 启动器，这是 Windows 上最可靠的方式。

### 问题2：pip 不是内部或外部命令

**解决方案**：使用 `py -m pip` 而不是直接使用 `pip`。

### 问题3：网络连接超时

**解决方案**：使用国内镜像源：

```cmd
py -m pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题4：权限不足

**解决方案**：以管理员身份运行命令提示符，或添加 `--user` 参数：

```cmd
py -m pip install --user torch torchvision
```

## GPU 支持（可选）

如果你有 NVIDIA GPU 并想使用 GPU 加速训练：

1. 安装 CUDA Toolkit（11.8 或 12.1）
2. 安装对应版本的 PyTorch：

```cmd
py -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 不安装深度学习依赖

如果你只需要使用传统 OCR 功能，不需要安装这些依赖。系统会自动检测并禁用深度学习模型功能。
