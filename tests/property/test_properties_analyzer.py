"""
数据分析模块属性测试

使用Hypothesis进行基于属性的测试
"""
import pytest
from hypothesis import given, strategies as st, settings
import pandas as pd
import math

from src.analyzer import DataAnalyzer
from src.database import TransmitterDatabase


class TestAnalyzerProperties:
    """数据分析器属性测试"""

    @given(
        value1=st.floats(
            min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False
        ),
        value2=st.floats(
            min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=100)
    def test_property_change_calculation(self, value1, value2):
        """
        Feature: transmitter-data-analyzer, Property 11: 变化量计算正确性

        对于任何匹配成功的数据项对，绝对变化量应该等于（后值 - 前值），
        相对变化率应该等于（(后值 - 前值) / 前值 × 100%）

        **验证：需求 5.2**
        """
        analyzer = DataAnalyzer(database=None)

        # 计算绝对变化量
        absolute_change = analyzer._calculate_absolute_change(value1, value2)

        # 计算相对变化率
        relative_change = analyzer._calculate_relative_change(value1, value2)

        # 验证绝对变化量
        expected_absolute = value2 - value1
        assert (
            abs(absolute_change - expected_absolute) < 1e-6
        ), f"绝对变化量计算错误: 期望 {expected_absolute}, 实际 {absolute_change}"

        # 验证相对变化率
        expected_relative = ((value2 - value1) / value1) * 100
        assert (
            abs(relative_change - expected_relative) < 1e-6
        ), f"相对变化率计算错误: 期望 {expected_relative}, 实际 {relative_change}"

    @given(
        num_items=st.integers(min_value=5, max_value=15),
        num_missing=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=100)
    def test_property_data_item_matching(self, num_items, num_missing):
        """
        Feature: transmitter-data-analyzer, Property 10: 数据项匹配正确性

        对于任意两个月份的对比操作，系统应该按数据项名称匹配数据，
        只对比两月都存在的数据项，并正确识别缺失项

        **验证：需求 5.1, 5.6**
        """
        from tests.fixtures.sample_data import COMMON_ITEM_NAMES
        import random
        import tempfile
        from pathlib import Path

        # 创建临时数据库
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            db = TransmitterDatabase(db_path)
            db.initialize_database()

            # 生成测试数据
            items = random.sample(
                COMMON_ITEM_NAMES, min(num_items, len(COMMON_ITEM_NAMES))
            )

            # 第一个月的数据
            data1 = pd.DataFrame(
                {
                    "item_name": items,
                    "value": [random.uniform(10, 100) for _ in items],
                    "unit": ["V"] * len(items),
                }
            )

            # 第二个月的数据（移除一些项）
            items2 = items.copy()
            if num_missing > 0 and len(items2) > num_missing:
                items_to_remove = random.sample(items2, min(num_missing, len(items2)))
                items2 = [item for item in items2 if item not in items_to_remove]

            data2 = pd.DataFrame(
                {
                    "item_name": items2,
                    "value": [random.uniform(10, 100) for _ in items2],
                    "unit": ["V"] * len(items2),
                }
            )

            # 插入数据
            db.insert_monthly_data("2026-01", data1)
            db.insert_monthly_data("2026-02", data2)

            # 执行对比
            analyzer = DataAnalyzer(db)
            result = analyzer.compare_two_months("2026-01", "2026-02")

            # 验证：结果应该包含所有数据项（包括缺失的）
            assert len(result) == len(set(items) | set(items2)), "对比结果应该包含两个月的所有数据项"

            # 验证：共同存在的数据项应该有变化量计算
            common_items = set(items) & set(items2)
            for item in common_items:
                item_row = result[result["item_name"] == item]
                assert not item_row.empty, f"数据项 {item} 应该在结果中"
                assert pd.notna(
                    item_row["absolute_change"].iloc[0]
                ), f"数据项 {item} 应该有绝对变化量"
                assert pd.notna(
                    item_row["relative_change"].iloc[0]
                ), f"数据项 {item} 应该有相对变化率"

            # 验证：缺失项应该被正确标记
            missing_items = (set(items) | set(items2)) - (set(items) & set(items2))
            for item in missing_items:
                item_row = result[result["item_name"] == item]
                if not item_row.empty:
                    assert pd.notna(
                        item_row["missing_in"].iloc[0]
                    ), f"缺失数据项 {item} 应该被标记"

            db.close()
