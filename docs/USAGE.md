# 使用说明

本文档详细介绍发射机数据分析器的使用方法和工作流程。

## 目录

- [启动系统](#启动系统)
- [主要功能](#主要功能)
- [工作流程示例](#工作流程示例)
- [命令行参数](#命令行参数)
- [数据格式要求](#数据格式要求)
- [最佳实践](#最佳实践)

## 启动系统

### 基本启动

```bash
# 使用默认配置启动
python3 main.py
```

系统将：
1. 检查依赖是否安装完整
2. 初始化日志系统
3. 创建或连接默认数据库（`~/Documents/transmitter_data.db`）
4. 显示主菜单

### 使用示例数据启动

```bash
# 首次使用建议先生成示例数据
python3 scripts/generate_sample_data.py

# 使用示例数据库启动
python3 main.py --db-path examples/sample_transmitter_data.db
```

### 自定义配置启动

```bash
# 指定数据库路径
python3 main.py --db-path /path/to/custom.db

# 设置日志级别
python3 main.py --log-level DEBUG

# 组合使用
python3 main.py --db-path /path/to/custom.db --log-level INFO
```

## 主要功能

系统启动后会显示主菜单：

```
========================================
发射机数据分析器
========================================
1. 录入数据
2. 两月对比
3. 绘制趋势
4. 数据管理
5. 退出
========================================
请选择功能 (1-5):
```

### 1. 录入数据

从发射机截图中提取数据并存储到数据库。

#### 操作步骤

1. 选择菜单选项 `1`
2. 输入截图文件路径（支持PNG、JPG格式）
3. 输入月份（YYYY-MM格式，如：2026-01）
4. 系统自动提取数据并显示结果
5. 确认是否保存到数据库

#### 示例

```
请选择功能 (1-5): 1

=== 数据录入 ===
请输入截图文件路径: examples/sample_images/sample_transmitter_1.png
请输入月份 (YYYY-MM): 2026-01

正在提取数据...
✓ 成功提取 8 条数据

提取结果预览：
         item_name   value unit
0    Forward Power   425.3    W
1  Reflected Power     1.2    W
2       PA Voltage    28.5    V
3       PA Current    16.8    A
...

是否保存到数据库？(y/n): y
✓ 数据已保存
```

#### 注意事项

- 截图应清晰可读，避免模糊或倾斜
- 如果月份数据已存在，系统会提示是否覆盖
- 提取失败的数据项会被跳过并记录警告

### 2. 两月对比

对比任意两个月的数据，分析参数变化。

#### 操作步骤

1. 选择菜单选项 `2`
2. 查看可用月份列表
3. 输入第一个月份（较早）
4. 输入第二个月份（较晚）
5. 查看对比结果
6. 选择是否导出报告或生成图表

#### 示例

```
请选择功能 (1-5): 2

=== 两月对比 ===
可用月份: 2025-08, 2025-09, 2025-10, 2025-11, 2025-12, 2026-01

请输入第一个月份: 2025-12
请输入第二个月份: 2026-01

正在分析数据...

对比结果：
         item_name  value_2025-12  value_2026-01  absolute_change  relative_change change_status
0    Forward Power         430.1         425.3             -4.8            -1.12%      decrease
1  Reflected Power           0.8           1.2              0.4            50.00%      increase
2       PA Voltage          29.0          28.5             -0.5            -1.72%      decrease
...

变化统计：
- 增长项: 3
- 下降项: 4
- 无变化: 1

是否导出对比报告？(y/n): y
请输入导出路径 (默认: comparison_2025-12_vs_2026-01.xlsx):
✓ 报告已导出

是否生成对比图表？(y/n): y
请输入图表路径 (默认: comparison_chart.png):
✓ 图表已生成
```

#### 对比结果说明

- **absolute_change**: 绝对变化量 = 后值 - 前值
- **relative_change**: 相对变化率 = (后值 - 前值) / 前值 × 100%
- **change_status**: 
  - `increase`: 增长（红色标注）
  - `decrease`: 下降（绿色标注）
  - `no_change`: 无变化（灰色标注）

### 3. 绘制趋势

绘制数据项的月度变化趋势图。

#### 操作步骤

1. 选择菜单选项 `3`
2. 查看可用数据项列表
3. 选择要绘制的数据项（可多选）
4. 选择时间范围（可选）
5. 设置阈值线（可选）
6. 选择图表类型（交互式/静态）
7. 查看或导出图表

#### 示例

```
请选择功能 (1-5): 3

=== 趋势可视化 ===
可用数据项:
1. Forward Power
2. Reflected Power
3. PA Voltage
4. PA Current
5. Ambient Temp
...

请输入数据项编号 (多个用逗号分隔): 1,3,5
已选择: Forward Power, PA Voltage, Ambient Temp

是否限制时间范围？(y/n): n

是否设置阈值线？(y/n): y
Forward Power 阈值: 400
PA Voltage 阈值: 27
Ambient Temp 阈值: 30

选择图表类型:
1. 交互式图表 (Plotly)
2. 静态图表 (Matplotlib)
请选择 (1-2): 1

正在生成图表...
✓ 图表已生成并在浏览器中打开

是否保存图表？(y/n): y
请输入保存路径 (默认: trend_chart.html):
✓ 图表已保存
```

#### 趋势图特性

**交互式图表（Plotly）**:
- 可缩放和平移
- 悬停显示详细数据
- 可切换显示/隐藏数据系列
- 支持导出为PNG、SVG、HTML

**静态图表（Matplotlib）**:
- 适合打印和报告
- 支持PNG、PDF格式
- 自定义样式和颜色

### 4. 数据管理

管理数据库中的数据，包括查询、删除和导出。

#### 子菜单

```
=== 数据管理 ===
1. 查询月度数据
2. 查询数据项历史
3. 删除月度数据
4. 导出数据
5. 返回主菜单
```

#### 4.1 查询月度数据

查看指定月份的所有数据。

```
请选择功能 (1-5): 1
请输入月份 (YYYY-MM): 2026-01

2026-01 月度数据：
         item_name   value unit
0    Forward Power   425.3    W
1  Reflected Power     1.2    W
...
共 15 条记录
```

#### 4.2 查询数据项历史

查看指定数据项的历史记录。

```
请选择功能 (1-5): 2
请输入数据项名称: Forward Power

Forward Power 历史记录：
      month   value unit
0  2025-08   445.2    W
1  2025-09   442.8    W
2  2025-10   438.5    W
...
```

#### 4.3 删除月度数据

删除指定月份的所有数据。

```
请选择功能 (1-5): 3
请输入要删除的月份: 2025-08

警告：此操作将删除 2025-08 的所有数据，无法恢复！
确认删除？(y/n): y
✓ 已删除 15 条记录
```

#### 4.4 导出数据

导出数据到Excel或CSV文件。

```
请选择功能 (1-5): 4

导出选项:
1. 导出指定月份数据
2. 导出所有数据
3. 导出数据项历史

请选择 (1-3): 1
请输入月份: 2026-01

选择导出格式:
1. Excel (.xlsx)
2. CSV (.csv)
请选择 (1-2): 1

请输入导出路径 (默认: data_2026-01.xlsx):
✓ 数据已导出
```

## 命令行参数

### 查看帮助

```bash
python3 main.py --help
```

输出：
```
usage: main.py [-h] [--db-path DB_PATH] [--log-level LOG_LEVEL] 
               [--check-deps] [--version]

发射机数据分析器

optional arguments:
  -h, --help            显示帮助信息
  --db-path DB_PATH     数据库文件路径
  --log-level LOG_LEVEL 日志级别 (DEBUG, INFO, WARNING, ERROR)
  --check-deps          检查系统依赖
  --version             显示版本信息
```

### 常用参数

#### --db-path

指定数据库文件路径。

```bash
# 使用自定义数据库
python3 main.py --db-path /path/to/database.db

# 使用示例数据库
python3 main.py --db-path examples/sample_transmitter_data.db
```

#### --log-level

设置日志详细程度。

```bash
# 调试模式（最详细）
python3 main.py --log-level DEBUG

# 信息模式（默认）
python3 main.py --log-level INFO

# 警告模式（仅显示警告和错误）
python3 main.py --log-level WARNING

# 错误模式（仅显示错误）
python3 main.py --log-level ERROR
```

#### --check-deps

检查系统依赖是否满足。

```bash
python3 main.py --check-deps
```

#### --version

显示版本信息。

```bash
python3 main.py --version
```

## 数据格式要求

### 截图要求

为了获得最佳的OCR识别效果，截图应满足：

1. **清晰度**: 分辨率至少 800x600，文字清晰可读
2. **格式**: PNG、JPG、JPEG格式
3. **内容**: 包含表格结构，数据项名称和数值清晰分离
4. **背景**: 白色或浅色背景，避免复杂背景
5. **方向**: 正向，避免旋转或倾斜

### 推荐的截图布局

```
Parameter Name          Value    Unit
─────────────────────────────────────
Forward Power           425.3    W
Reflected Power         1.2      W
PA Voltage              28.5     V
PA Current              16.8     A
...
```

### 月份格式

月份必须使用 `YYYY-MM` 格式：

- ✓ 正确: `2026-01`, `2025-12`, `2024-03`
- ✗ 错误: `2026-1`, `01-2026`, `2026/01`, `Jan 2026`

### 数据项命名

- 使用有意义的英文名称
- 避免特殊字符（除了 `%`、`°` 等单位符号）
- 保持命名一致性（同一参数在不同月份使用相同名称）

## 工作流程示例

### 场景1: 首次使用

```bash
# 1. 生成示例数据
python3 scripts/generate_sample_data.py

# 2. 使用示例数据启动系统
python3 main.py --db-path examples/sample_transmitter_data.db

# 3. 在菜单中选择 "2. 两月对比"
# 4. 对比 2025-12 和 2026-01
# 5. 导出对比报告

# 6. 在菜单中选择 "3. 绘制趋势"
# 7. 选择 Forward Power 和 PA Voltage
# 8. 生成交互式趋势图
```

### 场景2: 月度数据录入

```bash
# 1. 准备本月的发射机截图
# 2. 启动系统
python3 main.py

# 3. 选择 "1. 录入数据"
# 4. 输入截图路径: /path/to/screenshot.png
# 5. 输入月份: 2026-02
# 6. 确认保存数据

# 7. 选择 "2. 两月对比"
# 8. 对比上月 (2026-01) 和本月 (2026-02)
# 9. 导出对比报告给管理层
```

### 场景3: 趋势分析

```bash
# 1. 启动系统
python3 main.py

# 2. 选择 "3. 绘制趋势"
# 3. 选择关键参数（如 Forward Power, PA Voltage, Ambient Temp）
# 4. 设置阈值线（如 Forward Power > 400W）
# 5. 生成交互式图表
# 6. 分析趋势，识别异常

# 7. 如发现异常，选择 "4. 数据管理" → "2. 查询数据项历史"
# 8. 查看详细历史数据
```

## 最佳实践

### 数据录入

1. **定期录入**: 建议每月固定时间录入数据，保持数据连续性
2. **截图标准化**: 使用相同的截图方式和格式
3. **数据验证**: 录入后检查提取结果，确保准确性
4. **备份数据库**: 定期备份数据库文件

### 数据对比

1. **选择相邻月份**: 对比相邻月份更容易发现趋势
2. **关注关键参数**: 重点关注功率、温度等关键参数的变化
3. **保存报告**: 导出对比报告用于存档和汇报
4. **设置阈值**: 对重要参数设置合理的阈值

### 趋势分析

1. **长期趋势**: 至少使用6个月数据分析长期趋势
2. **分类分析**: 按模块（功率、温度、电压）分类分析
3. **异常检测**: 使用阈值线快速识别异常值
4. **定期审查**: 每季度审查趋势图，制定维护计划

### 数据管理

1. **定期清理**: 删除不需要的旧数据
2. **数据导出**: 定期导出数据到Excel进行深度分析
3. **数据备份**: 使用版本控制管理数据库文件
4. **文档记录**: 记录重要的数据变化和维护操作

## 故障排查

如果遇到问题，请参考：
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 常见问题排查
- [INSTALL.md](INSTALL.md) - 安装问题
- 项目Issue列表

## 下一步

- 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 了解常见问题
- 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统架构
- 查看 [CONTRIBUTING.md](CONTRIBUTING.md) 参与项目开发
