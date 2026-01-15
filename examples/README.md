# 示例数据说明

本目录包含用于演示和测试的示例数据。

## 文件说明

### 示例数据库
- **sample_transmitter_data.db**: 包含6个月（2025-08 至 2026-01）的模拟发射机数据
  - 每月包含15个数据项
  - 数据项包括功率、电压、电流、温度等参数
  - 数据具有真实的数值范围和趋势变化

### 示例截图
`sample_images/` 目录包含3个模拟的发射机监控截图：
- **sample_transmitter_1.png**: 2026-01 月份数据
- **sample_transmitter_2.png**: 2025-12 月份数据
- **sample_transmitter_3.png**: 2025-11 月份数据

## 使用方法

### 1. 使用示例数据库测试系统

```bash
# 启动系统并指定示例数据库
python3 main.py --db-path examples/sample_transmitter_data.db
```

然后您可以：
- 查看已有的月度数据
- 进行两月对比分析
- 绘制趋势图表
- 导出数据报告

### 2. 使用示例截图测试OCR功能

在系统中选择"录入数据"功能，然后输入示例截图路径：
```
examples/sample_images/sample_transmitter_1.png
```

### 3. 重新生成示例数据

如果需要重新生成示例数据：

```bash
python3 scripts/generate_sample_data.py
```

这将创建新的示例数据库和截图，覆盖现有文件。

## 数据项说明

示例数据包含以下发射机参数：

| 数据项 | 单位 | 典型范围 | 说明 |
|--------|------|----------|------|
| Forward Power | W | 400-450 | 前向功率 |
| Reflected Power | W | 0.1-2.0 | 反射功率 |
| PA Voltage | V | 26-30 | 功放电压 |
| PA Current | A | 15-18 | 功放电流 |
| APC Volts | V | 3.0-4.5 | 自动功率控制电压 |
| Airflow % | % | 75-95 | 气流百分比 |
| FM EXC Power % | % | 85-100 | FM激励功率百分比 |
| Ambient Temp | °C | 20-35 | 环境温度 |
| IPA AB Current | A | 2.5-3.5 | IPA AB级电流 |
| IPA AB Voltage | V | 12-14 | IPA AB级电压 |
| IPA AB Power | W | 30-45 | IPA AB级功率 |
| Driver Power | W | 50-70 | 驱动功率 |
| Exciter Power | W | 10-15 | 激励功率 |
| VSWR | - | 1.0-1.5 | 驻波比 |
| Efficiency | % | 80-90 | 效率 |

## 注意事项

- 示例数据仅用于演示和测试，不代表真实的发射机运行数据
- 数据中包含了一些模拟的趋势变化（如温度的季节性变化）
- 示例截图使用简化的表格格式，实际截图可能更复杂
