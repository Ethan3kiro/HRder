# Windows 故障排除指南

本文档记录 Windows 系统上常见问题及解决方案。

## 安装问题

### 问题 1：找不到 Python 命令

**症状**：
```
'python' 不是内部或外部命令，也不是可运行的程序
```

**原因**：Python 未添加到系统 PATH 环境变量。

**解决方案**：

使用 `py` 启动器代替 `python` 命令：
```cmd
py --version
py -m pip install -r requirements.txt
py main_gui.py
```

或者重新安装 Python，勾选 "Add Python to PATH" 选项。

### 问题 2：中文乱码

**症状**：命令提示符中显示乱码。

**解决方案**：

这不影响功能。如果想修复显示，运行：
```cmd
chcp 65001
```

### 问题 3：pip 版本警告

**症状**：
```
WARNING: You are using pip version 21.2.4; however, version 25.3 is available.
```

**影响**：不影响使用，只是提示有新版本。

**解决方案（可选）**：
```cmd
py -m pip install --upgrade pip
```

### 问题 4：requirements 文件找不到

**症状**：
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

**原因**：不在项目根目录。

**解决方案**：

确保在项目根目录运行命令：
```cmd
cd C:\path\to\HarrisReader
install_simple.bat
```

### 问题 5：权限不足

**症状**：
```
ERROR: Could not install packages due to an EnvironmentError
```

**解决方案**：

方法 1：以管理员身份运行命令提示符

方法 2：使用 `--user` 参数：
```cmd
py -m pip install --user -r requirements.txt
py -m pip install --user -r requirements-gui.txt
```

### 问题 6：网络连接超时

**症状**：
```
ReadTimeoutError: HTTPSConnectionPool
```

**解决方案**：

使用国内镜像源：
```cmd
py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
py -m pip install -r requirements-gui.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 运行问题

### 问题 7：启动后立即关闭

**可能原因**：
1. 缺少依赖
2. Python 版本过低
3. 代码错误

**解决方案**：

在命令提示符中运行，查看错误信息：
```cmd
py main_gui.py
```

### 问题 8：ModuleNotFoundError

**症状**：
```
ModuleNotFoundError: No module named 'PyQt6'
```

**原因**：依赖未正确安装。

**解决方案**：

重新安装依赖：
```cmd
py -m pip install -r requirements.txt -r requirements-gui.txt
```

### 问题 9：数据库错误

**症状**：
```
sqlite3.OperationalError: unable to open database file
```

**原因**：没有写入权限或路径不存在。

**解决方案**：

1. 确保在项目目录运行
2. 检查 `data/` 目录是否存在
3. 以管理员身份运行

### 问题 10：OCR 功能不可用

**症状**：OCR 识别按钮禁用或报错。

**原因**：Tesseract OCR 未安装。

**解决方案**：

Tesseract 是可选的，可以：
1. 使用深度学习模型（勾选"使用辅助模型"）
2. 手动输入数据
3. 安装 Tesseract：https://github.com/UB-Mannheim/tesseract/wiki

## 深度学习模型问题

### 问题 11：模型加载失败

**症状**："使用辅助模型"复选框被禁用。

**原因**：PyTorch 未安装或模型文件不存在。

**解决方案**：

1. 检查模型文件是否存在：`models/best_model.pth`
2. 安装 PyTorch（参见 INSTALL_DL_DEPENDENCIES.md）
3. 不使用模型，直接手动输入数据

## 性能问题

### 问题 12：启动缓慢

**原因**：首次启动需要初始化数据库和加载模型。

**解决方案**：正常现象，后续启动会更快。

### 问题 13：界面卡顿

**可能原因**：
1. 数据量过大
2. 系统资源不足

**解决方案**：
1. 定期导出和清理旧数据
2. 关闭其他占用资源的程序

## 获取帮助

如果以上方案都无法解决问题：

1. 查看完整错误信息
2. 检查 Python 版本：`py --version`（需要 3.9+）
3. 验证依赖安装：`py verify_dependencies.py`
4. 查看日志文件：`logs/` 目录

## 快速命令参考

```cmd
# 检查 Python 版本
py --version

# 安装依赖
install_simple.bat

# 手动安装依赖
py -m pip install -r requirements.txt
py -m pip install -r requirements-gui.txt

# 升级 pip
py -m pip install --upgrade pip

# 验证依赖
py verify_dependencies.py

# 启动应用
py main_gui.py

# 使用国内镜像
py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 系统要求

- Windows 10 或更高版本
- Python 3.9 或更高版本
- 至少 4GB RAM
- 至少 500MB 可用磁盘空间
