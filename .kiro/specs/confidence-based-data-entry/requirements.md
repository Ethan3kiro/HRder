# 需求文档：基于置信度的智能辅助数据录入

## 简介

基于置信度的智能辅助数据录入功能是对现有发射机数据分析器的增强。当前系统已具备：
- 完整的PyQt6 GUI界面（src/gui/）
- 数据录入组件（DataEntryWidget）
- 传统OCR识别（pytesseract）
- 深度学习模型（models/digit_ocr_model.pth）
- 71个数据项的完整模板（7个COMBINER + 64个Z-Plane）

本功能将深度学习模型集成到现有的DataEntryWidget中，实现智能化的数据录入流程：根据模型的识别置信度自动判断，高置信度数据自动填入并标记为绿色，低置信度数据标记为黄色待确认，由用户手动验证或修改。这种混合模式既提高了数据录入效率，又保证了数据准确性。

## 术语表

- **System**: 发射机数据分析器系统
- **DataEntryWidget**: 现有的数据录入组件（src/gui/widgets/data_entry_widget.py）
- **DL_OCR_Model**: 深度学习OCR模型（models/digit_ocr_model.pth，基于DigitCNN架构）
- **DLOCRExtractor**: 新的深度学习OCR提取器类，封装模型推理逻辑
- **Confidence_Score**: 置信度分数，基于模型输出的softmax概率或预测误差估计（0-1之间的浮点数）
- **Confidence_Threshold**: 置信度阈值，用于区分高置信度和低置信度数据的临界值（默认0.85）
- **Auto_Fill_Field**: 自动填充字段，置信度高于阈值的数据项，在表格中显示为绿色背景
- **Manual_Review_Field**: 待审核字段，置信度低于阈值需要人工确认的数据项，在表格中显示为黄色背景
- **Hybrid_Entry_Mode**: 混合录入模式，结合自动识别和人工审核的数据录入方式
- **Cell_Coordinates**: 单元格坐标定义，已在test_dl_model.py中定义的71个数据项的位置信息

## 需求

### 需求 1: 深度学习OCR提取器实现

**用户故事:** 作为开发者，我希望创建一个DLOCRExtractor类来封装深度学习模型的推理逻辑，以便在DataEntryWidget中方便地使用模型进行识别。

#### 验收标准

1. THE System SHALL 创建src/dl_ocr_extractor.py文件，实现DLOCRExtractor类
2. WHEN DLOCRExtractor初始化 THEN THE System SHALL 自动加载models/digit_ocr_model.pth模型文件
3. WHEN 模型文件不存在或损坏 THEN THE DLOCRExtractor SHALL 抛出明确的异常信息
4. THE DLOCRExtractor SHALL 提供extract_from_image方法，接受图像路径和单元格坐标，返回识别结果和置信度
5. THE DLOCRExtractor SHALL 复用test_dl_model.py中已定义的get_cell_coordinates方法获取71个数据项的坐标
6. THE DLOCRExtractor SHALL 复用test_dl_model.py中已定义的preprocess_image方法进行图像预处理
7. THE DLOCRExtractor SHALL 支持MPS（Mac）、CUDA（NVIDIA GPU）和CPU三种设备
8. THE DLOCRExtractor SHALL 返回DataFrame，包含item_name、value、unit、confidence四列

### 需求 2: 置信度计算策略

**用户故事:** 作为开发者，我希望实现合理的置信度计算方法，以便准确评估模型预测的可靠性。

#### 验收标准

1. THE DLOCRExtractor SHALL 基于模型输出计算置信度分数
2. WHEN 模型输出为回归值 THEN THE System SHALL 使用预测方差或历史误差统计估算置信度
3. THE System SHALL 提供简单的置信度计算方法：confidence = 1.0 / (1.0 + abs(predicted_value - expected_range_center) / expected_range_width)
4. THE System SHALL 为不同数据项类型（Current、ISO Temp、COMBINER）设置不同的expected_range
5. THE System SHALL 记录每次预测的置信度分数到日志

### 需求 3: DataEntryWidget集成

**用户故事:** 作为用户，我希望在现有的数据录入界面中使用深度学习模型识别，以便享受智能辅助录入的便利。

#### 验收标准

1. THE DataEntryWidget SHALL 在初始化时尝试加载DLOCRExtractor
2. WHEN DLOCRExtractor加载成功 THEN THE System SHALL 在"🔍 OCR 识别"按钮旁显示"🤖 智能识别"按钮
3. WHEN 用户点击"🤖 智能识别"按钮 THEN THE System SHALL 使用DLOCRExtractor识别所有71个数据项
4. WHEN 识别完成 THEN THE System SHALL 根据置信度自动填充表格并设置单元格背景色
5. THE System SHALL 在OCR结果显示区域显示识别统计：自动填充X项（绿色）、待审核Y项（黄色）、未识别Z项（白色）
6. IF DLOCRExtractor加载失败 THEN THE System SHALL 隐藏"🤖 智能识别"按钮，仅保留传统OCR功能

### 需求 4: 表格单元格视觉标识

**用户故事:** 作为用户，我希望在数据录入表格中清晰地看到哪些数据是自动填充的、哪些需要我审核，以便高效完成数据录入任务。

#### 验收标准

1. WHEN 显示Auto_Fill_Field THEN THE System SHALL 设置单元格背景色为浅绿色（#e8f5e9）
2. WHEN 显示Manual_Review_Field THEN THE System SHALL 设置单元格背景色为浅黄色（#fff3e0）
3. WHEN 单元格未识别或留空 THEN THE System SHALL 保持白色背景
4. WHEN 用户手动修改任意单元格 THEN THE System SHALL 将背景色改为浅蓝色（#e3f2fd），表示"人工确认"
5. THE System SHALL 在表格上方显示图例：🟢 自动填充（高置信度） | 🟡 待审核（低置信度） | ⚪ 未识别 | 🔵 人工确认
6. THE System SHALL 允许用户点击单元格查看该项的置信度分数（通过tooltip显示）

### 需求 5: 快速审核工作流

**用户故事:** 作为用户，我希望能够快速浏览和确认所有待审核的数据项，以便高效完成人工审核流程。

#### 验收标准

1. THE System SHALL 在表格上方添加"⚡ 快速审核"按钮
2. WHEN 用户点击"⚡ 快速审核"按钮 THEN THE System SHALL 自动定位到第一个黄色（待审核）单元格
3. WHEN 用户按Tab键 THEN THE System SHALL 跳转到下一个待审核单元格
4. WHEN 用户按Shift+Tab键 THEN THE System SHALL 跳转到上一个待审核单元格
5. WHEN 所有待审核项审核完成 THEN THE System SHALL 显示提示"✓ 所有待审核项已完成"
6. THE System SHALL 在快速审核模式下显示进度：已审核X/总共Y项

### 需求 6: 数据保存与元数据记录

**用户故事:** 作为用户，我希望系统在保存数据时记录识别来源和置信度信息，以便后续分析和模型改进。

#### 验收标准

1. WHEN 用户点击"💾 保存到数据库"按钮 THEN THE System SHALL 检查是否存在未审核的黄色单元格
2. IF 存在未审核项 THEN THE System SHALL 提示用户"还有X项待审核（黄色），是否继续保存？"
3. WHEN 保存数据 THEN THE System SHALL 为每个数据项添加元数据字段：data_source（auto/manual/reviewed）和confidence_score
4. WHEN data_source为auto THEN THE System SHALL 表示该项由模型自动填充且未修改
5. WHEN data_source为manual THEN THE System SHALL 表示该项由用户手动输入
6. WHEN data_source为reviewed THEN THE System SHALL 表示该项由模型识别但经用户审核修改
7. THE System SHALL 将置信度分数和数据来源一并存储到数据库的monthly_data表

### 需求 7: 置信度阈值配置

**用户故事:** 作为用户，我希望能够在设置界面调整置信度阈值，以便根据实际使用情况优化自动填充和人工审核的平衡点。

#### 验收标准

1. THE SettingsWidget SHALL 添加"智能识别设置"分组
2. THE System SHALL 提供默认Confidence_Threshold值为0.85（85%）
3. WHEN 用户在设置界面修改阈值 THEN THE System SHALL 验证输入值在0.0到1.0之间
4. WHEN 阈值保存成功 THEN THE System SHALL 通过SettingsManager持久化到配置
5. THE System SHALL 在设置界面显示阈值说明："阈值越高，自动填充越保守；阈值越低，自动填充越激进"
6. THE System SHALL 提供"恢复默认"按钮，将阈值重置为0.85

### 需求 8: 模型性能监控

**用户故事:** 作为用户，我希望了解模型的识别速度和资源占用情况，以便评估系统性能。

#### 验收标准

1. WHEN DL_OCR_Model执行推理 THEN THE System SHALL 记录每次推理的耗时
2. THE System SHALL 在日志中记录模型加载时间、内存占用、推理时间
3. WHEN 识别完成 THEN THE System SHALL 在界面显示"识别耗时：X秒"
4. THE System SHALL 提供性能报告，显示平均推理时间、最慢推理时间
5. IF 推理时间超过5秒 THEN THE System SHALL 提示用户考虑使用GPU加速或优化图像尺寸

### 需求 9: 回退机制与容错

**用户故事:** 作为用户，我希望在深度学习模型不可用时系统仍能正常工作，以便保证业务连续性。

#### 验收标准

1. IF DL_OCR_Model加载失败 THEN THE System SHALL 自动切换到传统OCR模式（pytesseract）
2. WHEN 使用传统OCR模式 THEN THE System SHALL 将所有识别结果标记为Manual_Review_Field（置信度设为0.5）
3. THE System SHALL 在界面显著位置提示当前使用的识别模式
4. WHEN 用户手动切换识别模式 THEN THE System SHALL 保存用户偏好到配置文件
5. THE System SHALL 提供"重新加载模型"功能，允许用户在修复模型文件后重新尝试加载

### 需求 10: 用户反馈与模型改进

**用户故事:** 作为用户，我希望能够标记识别错误的数据项，以便为模型改进提供训练数据。

#### 验收标准

1. WHEN 用户修改Auto_Fill_Field THEN THE System SHALL 记录该项为"识别错误"
2. THE System SHALL 提供"导出错误样本"功能，生成包含原始图像、错误识别结果、正确结果的数据集
3. THE System SHALL 统计识别错误率，按数据项类型分类显示
4. THE System SHALL 允许用户为错误样本添加备注说明
5. THE System SHALL 提供"提交反馈"功能，将错误样本打包用于模型重训练

### 需求 11: 快捷键与操作优化

**用户故事:** 作为用户，我希望使用快捷键快速完成审核操作，以便提高数据录入效率。

#### 验收标准

1. THE System SHALL 支持Tab键跳转到下一个Manual_Review_Field
2. THE System SHALL 支持Shift+Tab键跳转到上一个Manual_Review_Field
3. THE System SHALL 支持Enter键确认当前数据项并跳转到下一项
4. THE System SHALL 支持Ctrl+S（Mac: Cmd+S）快捷键保存数据
5. THE System SHALL 在界面底部显示快捷键提示面板

### 需求 12: 批量导入与历史数据迁移

**用户故事:** 作为用户，我希望能够批量处理多张截图，以便一次性完成多个月份的数据录入。

#### 验收标准

1. WHEN 用户选择批量导入模式 THEN THE System SHALL 允许选择多个截图文件
2. WHEN 批量识别完成 THEN THE System SHALL 显示所有月份的识别结果汇总
3. THE System SHALL 允许用户逐月审核数据，或一次性审核所有待审核项
4. WHEN 批量保存数据 THEN THE System SHALL 按月份分别存储到数据库
5. THE System SHALL 显示批量处理进度条和预计剩余时间
