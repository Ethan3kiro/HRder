"""
数据可视化模块属性测试

使用Hypothesis进行基于属性的测试
"""
import pytest
from hypothesis import given, strategies as st, settings
import tempfile
from pathlib import Path

from src.visualizer import DataVisualizer
from src.database import TransmitterDatabase


class TestVisualizerProperties:
    """数据可视化器属性测试"""

    @given(
        item_name=st.sampled_from(
            [
                "Forward Power",
                "Reflected Power",
                "PA Power",  # power
                "Ambient Temp",
                "Temperature",
                "Temp Sensor",  # temperature
                "PA Voltage",
                "Supply Voltage",
                "Voltage Monitor",  # voltage
                "PA Current",
                "Supply Current",
                "Current Draw",  # current
                "Airflow %",
                "FM EXC Power %",
                "Random Item",  # other
            ]
        )
    )
    @settings(max_examples=100)
    def test_property_item_categorization(self, item_name):
        """
        Feature: transmitter-data-analyzer, Property 13: 数据项分类正确性

        对于任何数据项名称，分类函数应该根据关键词（如"voltage"、"temperature"、"power"）
        将其归类到正确的模块类别

        **验证：需求 6.4**
        """
        # 创建临时数据库
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            db = TransmitterDatabase(db_path)
            db.initialize_database()

            visualizer = DataVisualizer(db)

            # 执行分类
            category = visualizer._categorize_item(item_name)

            # 验证分类结果
            item_lower = item_name.lower()

            # 验证电流类别（优先检查）
            if "current" in item_lower or "amp" in item_lower:
                assert (
                    category == "current"
                ), f"数据项 '{item_name}' 应该被分类为 'current'，实际为 '{category}'"
            # 验证功率类别
            elif "power" in item_lower or "watt" in item_lower:
                assert (
                    category == "power"
                ), f"数据项 '{item_name}' 应该被分类为 'power'，实际为 '{category}'"
            # 验证温度类别
            elif any(
                keyword in item_lower
                for keyword in ["temp", "temperature", "°c", "celsius"]
            ):
                assert (
                    category == "temperature"
                ), f"数据项 '{item_name}' 应该被分类为 'temperature'，实际为 '{category}'"
            # 验证电压类别
            elif "voltage" in item_lower or "volt" in item_lower:
                assert (
                    category == "voltage"
                ), f"数据项 '{item_name}' 应该被分类为 'voltage'，实际为 '{category}'"

            # 验证返回的类别是有效的
            valid_categories = ["power", "temperature", "voltage", "current", "other"]
            assert category in valid_categories, f"分类结果 '{category}' 不在有效类别列表中"

            db.close()
