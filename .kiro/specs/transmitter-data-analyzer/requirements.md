# 需求文档

## 简介

发射机数据分析器是一个跨平台的Python工具，用于从发射机监控系统的截图中提取数据，实现月度数据存储、历史对比、趋势可视化和结果导出的完整工作流程。该工具专为单用户月度数据录入场景设计，支持Mac和Windows系统。

## 术语表

- **System**: 发射机数据分析器系统
- **OCR_Engine**: 光学字符识别引擎（pytesseract + Tesseract-OCR）
- **Database**: SQLite数据库
- **Screenshot**: 发射机监控系统的图表截图文件
- **Data_Item**: 数据项，包含名称、数值和单位的结构化数据
- **Monthly_Record**: 月度记录，特定月份的完整数据集
- **Comparison_Report**: 对比报告，两个月度数据的差异分析结果
- **Trend_Chart**: 趋势图表，展示数据项随时间变化的可视化图表

## 需求

### 需求 1: 数据提取

**用户故事:** 作为用户，我希望从发射机截图中自动提取结构化数据，以便快速录入月度数据而无需手动输入。

#### 验收标准

1. WHEN 用户提供PNG或JPG格式的截图文件路径 THEN THE OCR_Engine SHALL 识别截图中的表格结构并提取文本内容
2. WHEN OCR_Engine提取到带单位的数值（如"12.5V"、"407%"、"19°C"）THEN THE System SHALL 将其拆分为纯数字数值和单位两部分
3. WHEN 提取完成 THEN THE System SHALL 返回包含数据项名称、数值和单位三个字段的结构化DataFrame
4. IF 截图文件不存在或格式不支持 THEN THE System SHALL 返回明确的错误信息并终止提取流程
5. THE System SHALL 支持不同排版格式的发射机表格截图

### 需求 2: 跨平台文件路径处理

**用户故事:** 作为用户，我希望工具能在Mac和Windows系统上无缝运行，以便在不同操作系统间切换使用。

#### 验收标准

1. THE System SHALL 使用Python的pathlib模块统一处理Mac和Windows的文件路径分隔符
2. WHEN 在Mac系统运行 THEN THE Database SHALL 默认存储在~/Documents/transmitter_data.db
3. WHEN 在Windows系统运行 THEN THE Database SHALL 默认存储在C:\Users\用户名\Documents\transmitter_data.db
4. THE System SHALL 自动检测Tesseract-OCR的安装路径（Mac和Windows的不同默认路径）
5. IF Tesseract-OCR未安装或路径错误 THEN THE System SHALL 提供清晰的安装指引

### 需求 3: 月度数据存储

**用户故事:** 作为用户，我希望将提取的数据按月份存储到数据库中，以便积累历史数据用于后续分析。

#### 验收标准

1. WHEN 首次运行系统 THEN THE Database SHALL 自动创建包含以下字段的数据表：id（主键）、month（YYYY-MM格式）、item_name（数据项名称）、value（数值）、unit（单位）、create_time（录入时间戳）
2. WHEN 用户录入月度数据 THEN THE System SHALL 验证月份格式是否为YYYY-MM
3. IF 数据库中已存在相同月份的数据 THEN THE System SHALL 提示用户选择覆盖或取消操作
4. WHEN 录入数据 THEN THE System SHALL 确保所有数据项的完整性（名称、数值、单位均不为空）
5. THE System SHALL 记录每条数据的录入时间戳

### 需求 4: 数据查询与管理

**用户故事:** 作为用户，我希望能够查询、删除和导出数据库中的月度数据，以便管理历史记录。

#### 验收标准

1. WHEN 用户按月份查询 THEN THE System SHALL 返回该月份所有数据项的DataFrame
2. WHEN 用户按数据项名称查询 THEN THE System SHALL 返回该数据项所有月份的历史记录
3. WHEN 用户删除指定月份数据 THEN THE System SHALL 从数据库中移除该月份的所有记录并返回删除成功确认
4. WHEN 用户导出指定月份数据 THEN THE System SHALL 生成包含所有数据项的Excel文件
5. IF 查询的月份或数据项不存在 THEN THE System SHALL 返回空结果并提示用户

### 需求 5: 两月数据对比

**用户故事:** 作为用户，我希望对比任意两个月的数据并标注变化项，以便快速识别发射机参数的变化趋势。

#### 验收标准

1. WHEN 用户选择数据库中的任意两个月份 THEN THE System SHALL 按数据项名称匹配两月数据
2. WHEN 匹配成功 THEN THE System SHALL 计算绝对变化量（后值 - 前值）和相对变化率（(后值 - 前值) / 前值 × 100%）
3. WHEN 生成对比表格 THEN THE System SHALL 使用颜色标注变化状态：红色表示增长、绿色表示下降、灰色表示无变化
4. WHEN 生成对比图表 THEN THE System SHALL 绘制柱状图展示两月数值，并在有变化的柱子上标注变化量和变化率
5. THE System SHALL 支持将对比表格导出为Excel或CSV格式
6. IF 两个月份的数据项不完全匹配 THEN THE System SHALL 仅对比共同存在的数据项并提示缺失项

### 需求 6: 月度趋势可视化

**用户故事:** 作为用户，我希望绘制数据项的月度变化趋势图，以便直观了解参数的长期变化规律。

#### 验收标准

1. WHEN 用户选择单个或多个数据项 THEN THE System SHALL 使用plotly绘制交互式月度变化折线图
2. WHEN 绘制趋势图 THEN THE System SHALL 在每个数据点标注"月份 + 数值"信息
3. WHEN 用户设置阈值线 THEN THE System SHALL 在图表中绘制阈值线，并将超标数值标记为红色
4. THE System SHALL 支持按模块分类绘制趋势图（如电源模块、温度模块、功率模块）
5. WHEN 用户导出趋势图 THEN THE System SHALL 支持PNG和PDF两种格式
6. THE System SHALL 使用matplotlib生成静态趋势图作为备选方案

### 需求 7: 命令行交互界面

**用户故事:** 作为用户，我希望通过简洁的命令行菜单操作系统，以便快速完成数据录入和分析任务。

#### 验收标准

1. WHEN 系统启动 THEN THE System SHALL 显示主菜单，包含以下选项：1-录入数据、2-两月对比、3-绘制趋势、4-数据管理、5-退出
2. WHEN 用户选择"录入数据" THEN THE System SHALL 提示输入截图文件路径和月份，然后执行数据提取和存储流程
3. WHEN 用户选择"两月对比" THEN THE System SHALL 显示可用月份列表，提示用户选择两个月份，然后生成对比报告
4. WHEN 用户选择"绘制趋势" THEN THE System SHALL 显示可用数据项列表，提示用户选择数据项和时间范围，然后生成趋势图
5. WHEN 用户选择"数据管理" THEN THE System SHALL 显示子菜单，包含查询、删除、导出功能
6. WHEN 用户输入无效选项 THEN THE System SHALL 提示错误并重新显示菜单

### 需求 8: 异常处理与健壮性

**用户故事:** 作为用户，我希望系统能够妥善处理各种异常情况，以便在遇到错误时获得清晰的提示而不是程序崩溃。

#### 验收标准

1. IF 截图中的数据项缺失或无法识别 THEN THE System SHALL 记录警告信息并继续处理其他数据项
2. IF 提取的数值格式异常（如包含非数字字符） THEN THE System SHALL 尝试清洗数据，失败则跳过该数据项并记录错误
3. IF 数据库文件损坏或无法访问 THEN THE System SHALL 提示用户检查文件权限或恢复备份
4. IF 用户输入的月份格式错误 THEN THE System SHALL 提示正确格式（YYYY-MM）并要求重新输入
5. WHEN 发生任何异常 THEN THE System SHALL 记录详细的错误日志到日志文件，包含时间戳和错误堆栈信息

### 需求 9: 依赖管理与环境配置

**用户故事:** 作为用户，我希望能够轻松安装和配置系统依赖，以便快速开始使用工具。

#### 验收标准

1. THE System SHALL 提供requirements.txt文件，列出所有Python依赖包及版本号
2. THE System SHALL 提供Mac和Windows系统的Tesseract-OCR安装指南文档
3. THE System SHALL 在首次运行时自动检测依赖是否安装完整，缺失则提示用户安装
4. THE System SHALL 提供数据库备份和恢复的操作说明
5. THE System SHALL 提供常见问题排查文档，包括pytesseract路径错误、数据库权限问题等解决方案

### 需求 10: 代码质量与可维护性

**用户故事:** 作为开发者，我希望代码结构清晰且易于理解，以便进行二次开发和功能扩展。

#### 验收标准

1. THE System SHALL 采用模块化设计，将数据提取、存储、对比、可视化功能分离到独立模块
2. THE System SHALL 为每个函数和类提供清晰的文档字符串，说明参数、返回值和功能
3. THE System SHALL 遵循PEP 8代码规范，保持代码风格一致
4. THE System SHALL 提供示例调用代码和模拟数据，无需依赖实际截图即可测试功能
5. THE System SHALL 避免过度封装，优先使用简洁直观的实现方式
