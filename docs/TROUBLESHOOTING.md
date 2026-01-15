# 常见问题排查

本文档列出了使用发射机数据分析器时可能遇到的常见问题及解决方案。

## 目录

- [安装问题](#安装问题)
- [OCR识别问题](#ocr识别问题)
- [数据库问题](#数据库问题)
- [数据处理问题](#数据处理问题)
- [可视化问题](#可视化问题)
- [性能问题](#性能问题)
- [日志和调试](#日志和调试)

## 安装问题

### Q1: Python版本不兼容

**症状**: 运行时提示Python版本过低或语法错误。

**原因**: 系统要求Python 3.8或更高版本。

**解决方案**:

```bash
# 检查Python版本
python3 --version

# 如果版本低于3.8，升级Python
# Mac:
brew upgrade python3

# Windows: 从官网下载最新版本安装
```

### Q2: pip安装依赖失败

**症状**: `pip install -r requirements.txt` 报错。

**常见错误和解决方案**:

#### 错误1: 网络超时

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 错误2: 权限不足

```bash
# 不要使用sudo，使用虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### 错误3: 编译错误（某些包需要编译）

```bash
# Mac: 安装Xcode命令行工具
xcode-select --install

# Windows: 安装Visual C++ Build Tools
# 下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Q3: Tesseract未找到

**症状**: 
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**解决方案**:

**Mac**:
```bash
# 安装Tesseract
brew install tesseract

# 验证安装
which tesseract
tesseract --version
```

**Windows**:
1. 下载安装程序: https://github.com/UB-Mannheim/tesseract/wiki
2. 安装到默认路径: `C:\Program Files\Tesseract-OCR`
3. 添加到PATH环境变量
4. 重启命令提示符

**手动指定路径**:
```python
# 在代码中指定Tesseract路径
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## OCR识别问题

### Q4: OCR识别率低

**症状**: 提取的数据不准确或缺失。

**可能原因和解决方案**:

#### 原因1: 图像质量差

**解决方案**:
- 使用高分辨率截图（至少800x600）
- 确保文字清晰，避免模糊
- 使用白色或浅色背景
- 避免图像压缩过度

#### 原因2: 图像格式问题

**解决方案**:
```bash
# 转换图像格式
# 使用图像编辑器将图像转换为PNG格式
# PNG格式通常有更好的识别效果
```

#### 原因3: 表格结构复杂

**解决方案**:
- 简化截图内容，只包含必要的数据表格
- 避免包含图表、按钮等干扰元素
- 确保表格行列对齐清晰

### Q5: 特定字符识别错误

**症状**: 某些字符（如°、%）识别错误。

**解决方案**:

1. **检查Tesseract语言包**:
```bash
# Mac
brew reinstall tesseract

# Windows: 重新安装Tesseract，确保安装了英文语言包
```

2. **图像预处理**:
系统已内置图像预处理功能，如果仍有问题，可以手动调整截图：
- 增加对比度
- 调整亮度
- 使用更大的字体

### Q6: 数值单位拆分错误

**症状**: "12.5V" 被识别为 "12.5" 和 "V"，但拆分不正确。

**解决方案**:

1. **检查OCR输出**:
```bash
# 启用DEBUG日志查看OCR原始输出
python3 main.py --log-level DEBUG
```

2. **调整截图格式**:
- 确保数值和单位之间有适当的间距
- 或者确保数值和单位紧密相连（无空格）

3. **查看日志**:
```bash
# 日志文件位置
# Mac: ~/Documents/transmitter_logs/
# Windows: C:\Users\用户名\Documents\transmitter_logs\

# 查看最新日志
tail -f ~/Documents/transmitter_logs/transmitter_*.log
```

## 数据库问题

### Q7: 数据库文件损坏

**症状**: 
```
DatabaseError: database disk image is malformed
```

**解决方案**:

1. **尝试修复数据库**:
```bash
# 使用SQLite命令行工具
sqlite3 transmitter_data.db "PRAGMA integrity_check;"

# 如果有错误，尝试导出和重建
sqlite3 transmitter_data.db ".dump" | sqlite3 new_database.db
```

2. **从备份恢复**:
```bash
# 如果有备份，直接替换
cp backup/transmitter_data.db ~/Documents/transmitter_data.db
```

3. **重新创建数据库**:
```bash
# 删除损坏的数据库（注意：数据将丢失）
rm ~/Documents/transmitter_data.db

# 重新启动系统，将自动创建新数据库
python3 main.py
```

### Q8: 数据库权限问题

**症状**: 
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**:

**Mac/Linux**:
```bash
# 检查文件权限
ls -l ~/Documents/transmitter_data.db

# 修改权限
chmod 644 ~/Documents/transmitter_data.db

# 检查目录权限
chmod 755 ~/Documents
```

**Windows**:
1. 右键数据库文件 → 属性
2. 安全选项卡 → 编辑
3. 确保当前用户有"完全控制"权限

### Q9: 重复数据问题

**症状**: 插入数据时提示月份已存在。

**解决方案**:

1. **覆盖现有数据**:
```
是否覆盖已存在的数据？(y/n): y
```

2. **先删除再插入**:
```
主菜单 → 4. 数据管理 → 3. 删除月度数据
输入要删除的月份
然后重新录入数据
```

3. **查询现有数据**:
```
主菜单 → 4. 数据管理 → 1. 查询月度数据
检查现有数据是否正确
```

## 数据处理问题

### Q10: 月份格式错误

**症状**: 
```
ValueError: 月份格式错误，请使用YYYY-MM格式
```

**解决方案**:

使用正确的格式：
- ✓ 正确: `2026-01`, `2025-12`
- ✗ 错误: `2026-1`, `01-2026`, `2026/01`

### Q11: 对比结果为空

**症状**: 两月对比时提示没有共同数据项。

**原因**: 两个月份的数据项名称不匹配。

**解决方案**:

1. **检查数据项名称**:
```
主菜单 → 4. 数据管理 → 1. 查询月度数据
分别查询两个月份的数据
检查数据项名称是否一致
```

2. **标准化数据项名称**:
- 确保同一参数在不同月份使用相同名称
- 注意大小写敏感
- 注意空格和特殊字符

3. **重新录入数据**:
如果数据项名称不一致，可能需要重新录入数据。

### Q12: 数值异常

**症状**: 某些数值明显不合理（如负数、超大值）。

**解决方案**:

1. **检查OCR识别**:
```bash
# 启用DEBUG日志
python3 main.py --log-level DEBUG

# 查看OCR原始输出
# 检查是否是识别错误
```

2. **手动修正**:
```
主菜单 → 4. 数据管理 → 3. 删除月度数据
删除错误数据
重新录入或手动编辑数据库
```

3. **使用SQLite工具手动编辑**:
```bash
sqlite3 ~/Documents/transmitter_data.db
sqlite> UPDATE transmitter_data SET value = 425.3 WHERE month = '2026-01' AND item_name = 'Forward Power';
sqlite> .quit
```

## 可视化问题

### Q13: 图表无法显示

**症状**: 生成图表时出错或图表为空。

**解决方案**:

#### 问题1: 缺少数据

```
主菜单 → 4. 数据管理 → 2. 查询数据项历史
确认数据项有足够的历史数据（至少2个月）
```

#### 问题2: Plotly无法打开浏览器

```bash
# 使用静态图表代替
选择图表类型时选择 "2. 静态图表 (Matplotlib)"

# 或者手动打开HTML文件
open trend_chart.html  # Mac
start trend_chart.html  # Windows
```

#### 问题3: 中文显示乱码

```python
# 在可视化模块中配置中文字体
# Mac
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# Windows
plt.rcParams['font.sans-serif'] = ['SimHei']
```

### Q14: 图表导出失败

**症状**: 保存图表时出错。

**解决方案**:

1. **检查路径权限**:
```bash
# 确保目标目录存在且有写入权限
mkdir -p ~/Documents/charts
chmod 755 ~/Documents/charts
```

2. **使用绝对路径**:
```
请输入保存路径: /Users/username/Documents/chart.png
```

3. **检查磁盘空间**:
```bash
# Mac/Linux
df -h

# Windows
dir
```

## 性能问题

### Q15: OCR提取速度慢

**症状**: 处理大图像时耗时很长。

**解决方案**:

1. **优化图像尺寸**:
```bash
# 使用图像编辑器调整图像大小
# 推荐尺寸: 1200x900 或更小
# 保持文字清晰的前提下尽量减小尺寸
```

2. **裁剪图像**:
```bash
# 只保留包含数据表格的区域
# 去除不必要的边框、标题等
```

3. **使用更快的硬件**:
- OCR处理是CPU密集型操作
- 使用更快的CPU可以显著提升速度

### Q16: 数据库查询慢

**症状**: 查询大量数据时响应慢。

**解决方案**:

1. **重建索引**:
```bash
sqlite3 ~/Documents/transmitter_data.db
sqlite> REINDEX;
sqlite> VACUUM;
sqlite> .quit
```

2. **清理旧数据**:
```
主菜单 → 4. 数据管理 → 3. 删除月度数据
删除不需要的旧数据
```

3. **优化查询**:
- 使用时间范围限制查询
- 避免查询所有历史数据

## 日志和调试

### Q17: 如何查看详细日志

**日志文件位置**:
- Mac: `~/Documents/transmitter_logs/transmitter_YYYYMMDD.log`
- Windows: `C:\Users\用户名\Documents\transmitter_logs\transmitter_YYYYMMDD.log`

**查看日志**:

```bash
# Mac/Linux
tail -f ~/Documents/transmitter_logs/transmitter_*.log

# Windows PowerShell
Get-Content -Path "C:\Users\用户名\Documents\transmitter_logs\transmitter_*.log" -Wait
```

**启用DEBUG日志**:

```bash
python3 main.py --log-level DEBUG
```

### Q18: 如何报告Bug

如果遇到无法解决的问题，请提供以下信息：

1. **系统信息**:
```bash
# 操作系统和版本
uname -a  # Mac/Linux
systeminfo  # Windows

# Python版本
python3 --version

# Tesseract版本
tesseract --version
```

2. **错误信息**:
- 完整的错误堆栈
- 相关的日志片段

3. **重现步骤**:
- 详细描述操作步骤
- 提供示例数据（如果可能）

4. **环境信息**:
```bash
# Python包版本
pip list

# 依赖检查结果
python3 main.py --check-deps
```

## 获取更多帮助

如果本文档未能解决您的问题：

1. 查看 [INSTALL.md](INSTALL.md) - 安装相关问题
2. 查看 [USAGE.md](USAGE.md) - 使用方法
3. 查看项目Issue列表 - 搜索类似问题
4. 提交新Issue - 附上详细信息

## 预防性维护

为了避免问题发生，建议：

1. **定期备份数据库**:
```bash
# 每月备份一次
cp ~/Documents/transmitter_data.db ~/Documents/backup/transmitter_data_$(date +%Y%m).db
```

2. **定期更新依赖**:
```bash
pip install --upgrade -r requirements.txt
```

3. **定期清理日志**:
```bash
# 删除30天前的日志
find ~/Documents/transmitter_logs/ -name "*.log" -mtime +30 -delete
```

4. **监控磁盘空间**:
```bash
# 确保有足够的磁盘空间
df -h ~/Documents
```

5. **验证数据完整性**:
```bash
# 定期运行测试
pytest tests/integration/
```
