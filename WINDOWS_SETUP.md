# Windows 快速设置指南

本指南专门针对 Windows 用户，帮助你快速设置和运行发射机数据分析器。

## 第一步：安装 Python

### 推荐方式：从 Python 官网安装

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.9 或更高版本
3. **重要**：安装时勾选 "Add Python to PATH"
4. 点击 "Install Now"

### 验证安装

打开命令提示符（Win+R，输入 `cmd`），运行：

```cmd
py --version
```

应该显示类似：`Python 3.11.x`

## 第二步：获取项目代码

### 方式1：从 Gitee 克隆

```cmd
git clone https://gitee.com/ethanzhang915025/harris-reader.git
cd harris-reader
```

### 方式2：下载 ZIP

1. 访问 https://gitee.com/ethanzhang915025/harris-reader
2. 点击"克隆/下载" → "下载 ZIP"
3. 解压到任意目录
4. 在该目录打开命令提示符

## 第三步：安装依赖

### 自动安装（推荐）

双击运行 `install_simple.bat`，或在命令提示符中运行：

```cmd
install_simple.bat
```

这个脚本会自动安装所有必需的依赖包。

### 手动安装（如果自动安装失败）

```cmd
py -m pip install -r requirements.txt
py -m pip install -r requirements-gui.txt
```

## 第四步：启动应用

### 方式1：双击启动（最简单）

双击 `start_gui.bat` 文件

### 方式2：命令行启动

```cmd
start_gui.bat
```

或者：

```cmd
py main_gui.py
```

## 常见问题解决

### 问题1：找不到 Python 命令

**症状**：
```
'python' 不是内部或外部命令
```

**解决方案**：
1. 使用 `py` 命令代替 `python`
2. 或者重新安装 Python，勾选 "Add Python to PATH"

### 问题2：pip 安装失败

**症状**：
```
pip install 超时或失败
```

**解决方案**：使用国内镜像源

```cmd
py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题3：权限不足

**症状**：
```
ERROR: Could not install packages due to an EnvironmentError
```

**解决方案**：
1. 以管理员身份运行命令提示符
2. 或者添加 `--user` 参数：

```cmd
py -m pip install --user -r requirements.txt
```

### 问题4：中文乱码

**解决方案**：在命令提示符中运行：

```cmd
chcp 65001
```

然后重新运行脚本。

## 深度学习模型（可选）

如果需要使用深度学习辅助功能，参见 [INSTALL_DL_DEPENDENCIES.md](INSTALL_DL_DEPENDENCIES.md)

基本使用不需要安装深度学习依赖。

## 下一步

安装完成后，查看：
- [QUICK_START.md](QUICK_START.md) - 5分钟快速上手
- [README.md](README.md) - 完整功能说明
- [TRAINING.md](TRAINING.md) - 模型训练指南

## 需要帮助？

如果遇到其他问题：
1. 查看 [DEPENDENCIES.md](DEPENDENCIES.md) 详细依赖说明
2. 检查 Python 版本是否 >= 3.9
3. 确认网络连接正常
4. 尝试使用管理员权限运行

## 快速命令参考

```cmd
# 检查 Python 版本
py --version

# 安装依赖
py -m pip install -r requirements.txt

# 启动应用
py main_gui.py

# 验证依赖
py verify_dependencies.py
```
