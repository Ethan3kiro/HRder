"""
数据导出模块的属性测试

验证导出功能的正确性属性
"""
import pytest
from hypothesis import given, strategies as st, settings
import pandas as pd
from pathlib import Path
import tempfile
import os

from src.exporter import DataExporter
from tests.fixtures.sample_data import item_name_strategy, value_strategy, unit_strategy


@settings(max_examples=100, deadline=None)
@given(
    num_rows=st.integers(min_value=1, max_value=50),
    item_names=st.lists(item_name_strategy, min_size=1, max_size=20, unique=True),
)
def test_property_export_excel_completeness(num_rows, item_names):
    """
    Feature: transmitter-data-analyzer, Property 12: 导出功能完整性

    对于任何数据集，Excel导出操作应该生成包含所有数据的有效文件，
    且文件可以被正确读取，读取后的数据与原始数据一致

    **验证：需求 4.4, 5.5, 6.5**
    """
    # 生成测试数据
    num_items = min(num_rows, len(item_names))
    data = pd.DataFrame(
        {
            "item_name": item_names[:num_items],
            "value": [float(i * 10.5) for i in range(num_items)],
            "unit": ["V"] * num_items,
        }
    )

    exporter = DataExporter()

    # 使用临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_export.xlsx"

        # 导出数据
        exporter.export_to_excel(data, output_path)

        # 验证文件存在
        assert output_path.exists(), "导出的Excel文件应该存在"

        # 验证文件大小大于0
        assert output_path.stat().st_size > 0, "导出的Excel文件不应为空"

        # 读取文件并验证数据完整性
        read_data = pd.read_excel(output_path)

        # 验证行数一致
        assert len(read_data) == len(data), "读取的数据行数应与原始数据一致"

        # 验证列名一致
        assert set(read_data.columns) == set(data.columns), "读取的数据列名应与原始数据一致"

        # 验证数据项名称一致
        assert set(read_data["item_name"]) == set(data["item_name"]), "数据项名称应完整保留"


@settings(max_examples=100, deadline=None)
@given(
    num_rows=st.integers(min_value=1, max_value=50),
    item_names=st.lists(item_name_strategy, min_size=1, max_size=20, unique=True),
)
def test_property_export_csv_completeness(num_rows, item_names):
    """
    Feature: transmitter-data-analyzer, Property 12: 导出功能完整性

    对于任何数据集，CSV导出操作应该生成包含所有数据的有效文件，
    且文件可以被正确读取，读取后的数据与原始数据一致

    **验证：需求 4.4, 5.5, 6.5**
    """
    # 生成测试数据
    num_items = min(num_rows, len(item_names))
    data = pd.DataFrame(
        {
            "item_name": item_names[:num_items],
            "value": [float(i * 10.5) for i in range(num_items)],
            "unit": ["A"] * num_items,
        }
    )

    exporter = DataExporter()

    # 使用临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_export.csv"

        # 导出数据
        exporter.export_to_csv(data, output_path)

        # 验证文件存在
        assert output_path.exists(), "导出的CSV文件应该存在"

        # 验证文件大小大于0
        assert output_path.stat().st_size > 0, "导出的CSV文件不应为空"

        # 读取文件并验证数据完整性
        read_data = pd.read_csv(output_path, encoding="utf-8-sig")

        # 验证行数一致
        assert len(read_data) == len(data), "读取的数据行数应与原始数据一致"

        # 验证列名一致
        assert set(read_data.columns) == set(data.columns), "读取的数据列名应与原始数据一致"

        # 验证数据项名称一致
        assert set(read_data["item_name"]) == set(data["item_name"]), "数据项名称应完整保留"


@settings(max_examples=100, deadline=None)
@given(
    num_rows=st.integers(min_value=1, max_value=30),
    item_names=st.lists(item_name_strategy, min_size=1, max_size=15, unique=True),
)
def test_property_export_comparison_report_completeness(num_rows, item_names):
    """
    Feature: transmitter-data-analyzer, Property 12: 导出功能完整性

    对于任何对比数据集，格式化对比报告导出应该生成包含所有数据的有效Excel文件，
    且文件可以被正确读取

    **验证：需求 4.4, 5.5, 6.5**
    """
    # 生成对比数据
    num_items = min(num_rows, len(item_names))
    comparison_data = pd.DataFrame(
        {
            "item_name": item_names[:num_items],
            "value_month1": [float(i * 10.0) for i in range(num_items)],
            "value_month2": [float(i * 12.0) for i in range(num_items)],
            "unit": ["W"] * num_items,
            "absolute_change": [float(i * 2.0) for i in range(num_items)],
            "relative_change": [20.0] * num_items,
            "change_status": [
                "increase" if i % 3 == 0 else "decrease" if i % 3 == 1 else "no_change"
                for i in range(num_items)
            ],
        }
    )

    exporter = DataExporter()

    # 使用临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_comparison_report.xlsx"

        # 导出对比报告
        exporter.export_comparison_report(comparison_data, output_path)

        # 验证文件存在
        assert output_path.exists(), "导出的对比报告文件应该存在"

        # 验证文件大小大于0
        assert output_path.stat().st_size > 0, "导出的对比报告文件不应为空"

        # 读取文件并验证数据完整性
        read_data = pd.read_excel(output_path)

        # 验证行数一致
        assert len(read_data) == len(comparison_data), "读取的数据行数应与原始数据一致"

        # 验证列名一致
        assert set(read_data.columns) == set(comparison_data.columns), "读取的数据列名应与原始数据一致"

        # 验证数据项名称一致
        assert set(read_data["item_name"]) == set(
            comparison_data["item_name"]
        ), "数据项名称应完整保留"

        # 验证change_status列的值
        assert set(read_data["change_status"]) <= {
            "increase",
            "decrease",
            "no_change",
        }, "change_status应该只包含有效的状态值"


@settings(max_examples=100, deadline=None)
@given(data_size=st.integers(min_value=1, max_value=100))
def test_property_export_preserves_data_types(data_size):
    """
    Feature: transmitter-data-analyzer, Property 12: 导出功能完整性

    对于任何数据集，导出后再读取应该保持数据类型的正确性
    （数值类型应该是数值，文本类型应该是文本）

    **验证：需求 4.4, 5.5, 6.5**
    """
    # 生成测试数据
    data = pd.DataFrame(
        {
            "item_name": [f"Item_{i}" for i in range(data_size)],
            "value": [float(i * 1.5) for i in range(data_size)],
            "unit": ["V" if i % 2 == 0 else "A" for i in range(data_size)],
        }
    )

    exporter = DataExporter()

    # 使用临时文件测试Excel
    with tempfile.TemporaryDirectory() as tmpdir:
        excel_path = Path(tmpdir) / "test_types.xlsx"

        # 导出并读取Excel
        exporter.export_to_excel(data, excel_path)
        read_excel = pd.read_excel(excel_path)

        # 验证数值列是数值类型
        assert pd.api.types.is_numeric_dtype(read_excel["value"]), "value列应该是数值类型"

        # 验证文本列是对象类型
        assert pd.api.types.is_object_dtype(
            read_excel["item_name"]
        ), "item_name列应该是文本类型"

        # 测试CSV
        csv_path = Path(tmpdir) / "test_types.csv"

        # 导出并读取CSV
        exporter.export_to_csv(data, csv_path)
        read_csv = pd.read_csv(csv_path, encoding="utf-8-sig")

        # 验证数值列是数值类型
        assert pd.api.types.is_numeric_dtype(read_csv["value"]), "value列应该是数值类型"

        # 验证文本列是对象类型
        assert pd.api.types.is_object_dtype(read_csv["item_name"]), "item_name列应该是文本类型"
