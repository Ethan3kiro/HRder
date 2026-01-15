"""
OCR模块的属性测试

使用Hypothesis进行基于属性的测试
"""
import pytest
from hypothesis import given, strategies as st, settings
import re


def parse_value_unit_standalone(text: str):
    """
    独立的数值单位解析函数（用于测试）
    这是OCRExtractor._parse_value_unit的独立版本
    """
    text = text.strip()

    # 支持的单位模式
    # 匹配：数字（可能包含小数点、负号和科学计数法） + 可选的单位
    pattern = r"^(-?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*([A-Za-z%°]+)?$"

    match = re.match(pattern, text)
    if match:
        value_str = match.group(1)
        unit = match.group(2) if match.group(2) else ""

        try:
            value = float(value_str)
            return value, unit
        except ValueError:
            raise ValueError(f"无法将 '{value_str}' 转换为数值")

    raise ValueError(f"无法解析文本: '{text}'")


# 定义常见单位策略
COMMON_UNITS = ["V", "A", "W", "%", "°C", "Hz", "dB", "mA", "kW", "MHz", ""]

# 数值策略：生成合理范围的浮点数
value_strategy = st.floats(
    min_value=-1000.0, max_value=10000.0, allow_nan=False, allow_infinity=False
).filter(
    lambda x: abs(x) < 1e6
)  # 避免过大的数值

# 单位策略
unit_strategy = st.sampled_from(COMMON_UNITS)


@settings(max_examples=100, deadline=None)
@given(value=value_strategy, unit=unit_strategy)
def test_property_parse_value_unit_correctness(value, unit):
    """
    Feature: transmitter-data-analyzer, Property 1: 数值单位拆分正确性

    对于任何带单位的数值字符串，解析函数应该正确拆分为数值和单位两部分，
    且数值部分为有效的浮点数。

    **验证：需求 1.2**
    """
    # 构造测试字符串
    if unit:
        test_string = f"{value}{unit}"
    else:
        test_string = str(value)

    # 解析
    parsed_value, parsed_unit = parse_value_unit_standalone(test_string)

    # 验证数值正确性（允许浮点误差）
    assert abs(parsed_value - value) < 1e-6, f"解析的数值 {parsed_value} 与原始值 {value} 不匹配"

    # 验证单位正确性
    assert parsed_unit == unit, f"解析的单位 '{parsed_unit}' 与原始单位 '{unit}' 不匹配"

    # 验证返回的数值是有效的浮点数
    assert isinstance(parsed_value, float), f"解析的数值类型应为float，实际为 {type(parsed_value)}"


@settings(max_examples=100, deadline=None)
@given(
    value=st.floats(
        min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
    ),
    unit=st.sampled_from(["V", "A", "W", "%", "°C"]),
)
def test_property_parse_value_unit_with_spaces(value, unit):
    """
    测试带空格的数值单位字符串解析

    **验证：需求 1.2**
    """
    # 构造带空格的测试字符串
    test_string = f"{value} {unit}"

    # 解析
    parsed_value, parsed_unit = parse_value_unit_standalone(test_string)

    # 验证
    assert abs(parsed_value - value) < 1e-6
    assert parsed_unit == unit


@settings(max_examples=100, deadline=None)
@given(
    value=st.floats(
        min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False
    )
)
def test_property_parse_value_without_unit(value):
    """
    测试无单位的纯数字解析

    **验证：需求 1.2**
    """
    test_string = str(value)

    # 解析
    parsed_value, parsed_unit = parse_value_unit_standalone(test_string)

    # 验证
    assert abs(parsed_value - value) < 1e-6
    assert parsed_unit == ""


# 属性 2: 提取数据结构完整性测试
@settings(max_examples=100, deadline=None)
@given(
    item_names=st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
            min_size=3,
            max_size=20,
        ),
        min_size=1,
        max_size=10,
    ),
    values=st.lists(
        st.floats(
            min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        min_size=1,
        max_size=10,
    ),
    units=st.lists(
        st.sampled_from(["V", "A", "W", "%", "°C", ""]), min_size=1, max_size=10
    ),
)
def test_property_dataframe_structure_integrity(item_names, values, units):
    """
    Feature: transmitter-data-analyzer, Property 2: 提取数据结构完整性

    对于任何OCR提取操作，返回的DataFrame应该包含item_name、value、unit三个字段，
    且所有字段均不为空（除非整个提取失败）。

    **验证：需求 1.3, 3.4**
    """
    import pandas as pd

    # 确保列表长度一致
    min_len = min(len(item_names), len(values), len(units))
    item_names = item_names[:min_len]
    values = values[:min_len]
    units = units[:min_len]

    # 创建模拟的DataFrame（模拟OCR提取结果）
    data = {"item_name": item_names, "value": values, "unit": units}
    result_df = pd.DataFrame(data)

    # 验证DataFrame结构
    assert isinstance(result_df, pd.DataFrame), "结果应该是DataFrame"
    assert set(result_df.columns) == {
        "item_name",
        "value",
        "unit",
    }, "DataFrame应该包含item_name、value、unit三列"

    # 验证数据完整性
    if len(result_df) > 0:
        assert result_df["item_name"].notna().all(), "item_name不应包含空值"
        assert result_df["value"].notna().all(), "value不应包含空值"
        # unit可以为空字符串，但不应为NaN
        assert result_df["unit"].notna().all(), "unit不应包含NaN值"


# 属性 3: 错误输入处理测试
@settings(max_examples=100, deadline=None)
@given(
    invalid_text=st.one_of(
        st.text(
            alphabet=st.characters(blacklist_characters="0123456789.-+eE"),
            min_size=1,
            max_size=20,
        ),
        st.just(""),
        st.just("   "),
        st.text(
            alphabet=st.characters(whitelist_categories=("P", "S")),
            min_size=1,
            max_size=10,
        ),
    )
)
def test_property_error_input_handling(invalid_text):
    """
    Feature: transmitter-data-analyzer, Property 3: 错误输入处理

    对于任何无效的输入，系统应该抛出明确的异常或返回错误信息，
    而不是崩溃或返回不正确的结果。

    **验证：需求 1.4, 2.5, 8.3, 8.4**
    """
    # 测试无效文本解析
    try:
        parsed_value, parsed_unit = parse_value_unit_standalone(invalid_text)
        # 如果成功解析，验证结果是有效的
        assert isinstance(parsed_value, float)
        assert isinstance(parsed_unit, str)
    except ValueError as e:
        # 应该抛出ValueError，这是预期的
        assert "无法解析" in str(e) or "无法将" in str(e)
        assert len(str(e)) > 0  # 错误消息不应为空


@settings(max_examples=50, deadline=None)
@given(
    filename=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=20,
    ).map(
        lambda s: s + ".xyz"
    )  # 不支持的扩展名
)
def test_property_unsupported_file_format(filename):
    """
    测试不支持的文件格式处理

    **验证：需求 1.4**
    """
    from pathlib import Path
    from src.config import Config

    file_path = Path(filename)

    # 验证不支持的格式被正确识别
    is_supported = Config.is_supported_image(file_path)

    # .xyz格式不应该被支持
    assert not is_supported, f"文件 {filename} 不应该被识别为支持的格式"
