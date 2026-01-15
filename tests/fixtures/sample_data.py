"""
模拟数据生成器

用于生成测试数据和Hypothesis策略
"""
import pandas as pd
from datetime import date
from hypothesis import strategies as st
from typing import List, Dict, Any


# 常见的发射机数据项名称
COMMON_ITEM_NAMES = [
    "Forward Power",
    "Reflected Power",
    "PA Current",
    "PA Voltage",
    "APC Volts",
    "Airflow %",
    "FM EXC Power %",
    "Ambient Temp",
    "IPA AB Current",
    "IPA AB Voltage",
    "IPA AB Power",
    "Driver Power",
    "Exciter Power",
    "VSWR",
    "Temperature",
]

# 单位列表
COMMON_UNITS = ["V", "A", "W", "%", "°C", "dB", ""]

# 数据项分类
ITEM_CATEGORIES = {
    "power": [
        "Forward Power",
        "Reflected Power",
        "PA Power",
        "Driver Power",
        "Exciter Power",
    ],
    "voltage": ["PA Voltage", "APC Volts", "IPA AB Voltage"],
    "current": ["PA Current", "IPA AB Current"],
    "temperature": ["Ambient Temp", "Temperature"],
    "percentage": ["Airflow %", "FM EXC Power %"],
}


# Hypothesis策略定义

# 数据项名称策略
item_name_strategy = st.sampled_from(COMMON_ITEM_NAMES)

# 数值策略（根据实际发射机数据范围）
value_strategy = st.floats(
    min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
)

# 单位策略
unit_strategy = st.sampled_from(COMMON_UNITS)

# 月份策略（YYYY-MM格式）
month_strategy = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)).map(
    lambda d: d.strftime("%Y-%m")
)

# 完整数据记录策略
data_record_strategy = st.builds(
    dict, item_name=item_name_strategy, value=value_strategy, unit=unit_strategy
)


# DataFrame策略
def dataframe_strategy(min_rows: int = 1, max_rows: int = 20):
    """生成DataFrame的策略"""
    return st.lists(data_record_strategy, min_size=min_rows, max_size=max_rows).map(
        lambda records: pd.DataFrame(records)
    )


# 辅助函数


def generate_sample_dataframe(num_items: int = 10) -> pd.DataFrame:
    """
    生成示例DataFrame

    Args:
        num_items: 数据项数量

    Returns:
        包含item_name、value、unit的DataFrame
    """
    import random

    items = random.sample(COMMON_ITEM_NAMES, min(num_items, len(COMMON_ITEM_NAMES)))
    data = []

    for item in items:
        # 根据数据项类型生成合理的数值和单位
        if "Power" in item:
            value = random.uniform(0, 500)
            unit = "W"
        elif "Voltage" in item or "Volts" in item:
            value = random.uniform(0, 50)
            unit = "V"
        elif "Current" in item:
            value = random.uniform(0, 20)
            unit = "A"
        elif "Temp" in item:
            value = random.uniform(15, 45)
            unit = "°C"
        elif "%" in item:
            value = random.uniform(0, 100)
            unit = "%"
        else:
            value = random.uniform(0, 100)
            unit = ""

        data.append({"item_name": item, "value": round(value, 2), "unit": unit})

    return pd.DataFrame(data)


def generate_monthly_data(month: str, num_items: int = 10) -> pd.DataFrame:
    """
    生成指定月份的模拟数据

    Args:
        month: 月份字符串（YYYY-MM格式）
        num_items: 数据项数量

    Returns:
        包含月度数据的DataFrame
    """
    df = generate_sample_dataframe(num_items)
    df["month"] = month
    return df


def generate_comparison_data(
    month1: str, month2: str, num_items: int = 10, change_ratio: float = 0.1
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    生成两个月的对比数据

    Args:
        month1: 第一个月份
        month2: 第二个月份
        num_items: 数据项数量
        change_ratio: 变化比例（0-1之间）

    Returns:
        (第一个月数据, 第二个月数据)
    """
    import random

    df1 = generate_monthly_data(month1, num_items)
    df2 = df1.copy()
    df2["month"] = month2

    # 随机改变一些数值
    for idx in df2.index:
        if random.random() < change_ratio:
            original_value = df2.loc[idx, "value"]
            change_factor = random.uniform(0.8, 1.2)
            df2.loc[idx, "value"] = round(original_value * change_factor, 2)

    return df1, df2
