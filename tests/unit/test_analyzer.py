"""
数据分析模块单元测试
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.analyzer import DataAnalyzer
from src.database import TransmitterDatabase
from src.exceptions import DataValidationError


class TestDataAnalyzer:
    """数据分析器单元测试"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()
        return db

    @pytest.fixture
    def analyzer(self, db):
        """创建数据分析器实例"""
        return DataAnalyzer(db)

    @pytest.fixture
    def sample_data(self, db):
        """插入示例数据"""
        # 第一个月的数据
        data1 = pd.DataFrame(
            {
                "item_name": ["Forward Power", "PA Voltage", "Ambient Temp"],
                "value": [100.0, 12.5, 25.0],
                "unit": ["W", "V", "°C"],
            }
        )
        db.insert_monthly_data("2026-01", data1)

        # 第二个月的数据（有变化）
        data2 = pd.DataFrame(
            {
                "item_name": ["Forward Power", "PA Voltage", "Ambient Temp"],
                "value": [110.0, 12.5, 28.0],
                "unit": ["W", "V", "°C"],
            }
        )
        db.insert_monthly_data("2026-02", data2)

        # 第三个月的数据
        data3 = pd.DataFrame(
            {
                "item_name": ["Forward Power", "PA Voltage", "Ambient Temp"],
                "value": [105.0, 13.0, 26.0],
                "unit": ["W", "V", "°C"],
            }
        )
        db.insert_monthly_data("2026-03", data3)

        return db

    def test_calculate_absolute_change(self, analyzer):
        """测试绝对变化量计算"""
        result = analyzer._calculate_absolute_change(100.0, 110.0)
        assert result == 10.0

        result = analyzer._calculate_absolute_change(100.0, 90.0)
        assert result == -10.0

        result = analyzer._calculate_absolute_change(100.0, 100.0)
        assert result == 0.0

    def test_calculate_relative_change(self, analyzer):
        """测试相对变化率计算"""
        result = analyzer._calculate_relative_change(100.0, 110.0)
        assert abs(result - 10.0) < 1e-6

        result = analyzer._calculate_relative_change(100.0, 90.0)
        assert abs(result - (-10.0)) < 1e-6

        result = analyzer._calculate_relative_change(100.0, 100.0)
        assert abs(result - 0.0) < 1e-6

    def test_calculate_relative_change_zero_division(self, analyzer):
        """测试除以零的情况"""
        result = analyzer._calculate_relative_change(0.0, 10.0)
        assert result == float("inf")

        result = analyzer._calculate_relative_change(0.0, -10.0)
        assert result == float("-inf")

        result = analyzer._calculate_relative_change(0.0, 0.0)
        assert result == 0.0

    def test_determine_change_status(self, analyzer):
        """测试变化状态判断"""
        assert analyzer._determine_change_status(10.0) == "increase"
        assert analyzer._determine_change_status(-10.0) == "decrease"
        assert analyzer._determine_change_status(0.005) == "no_change"
        assert analyzer._determine_change_status(-0.005) == "no_change"

    def test_compare_two_months_basic(self, sample_data, analyzer):
        """测试基本的两月对比功能"""
        result = analyzer.compare_two_months("2026-01", "2026-02", device_id=1)

        # 验证结果结构
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert set(result.columns) == {
            "item_name",
            "value_month1",
            "value_month2",
            "unit",
            "absolute_change",
            "relative_change",
            "change_status",
            "missing_in",
        }

        # 验证Forward Power的变化
        fp_row = result[result["item_name"] == "Forward Power"].iloc[0]
        assert fp_row["value_month1"] == 100.0
        assert fp_row["value_month2"] == 110.0
        assert fp_row["absolute_change"] == 10.0
        assert abs(fp_row["relative_change"] - 10.0) < 1e-6
        assert fp_row["change_status"] == "increase"

        # 验证PA Voltage无变化
        pv_row = result[result["item_name"] == "PA Voltage"].iloc[0]
        assert pv_row["change_status"] == "no_change"

        # 验证Ambient Temp的变化
        at_row = result[result["item_name"] == "Ambient Temp"].iloc[0]
        assert at_row["change_status"] == "increase"

    def test_compare_two_months_with_missing_items(self, db, analyzer):
        """测试有缺失项的两月对比"""
        # 第一个月有3个数据项
        data1 = pd.DataFrame(
            {
                "item_name": ["Item A", "Item B", "Item C"],
                "value": [10.0, 20.0, 30.0],
                "unit": ["V", "V", "V"],
            }
        )
        db.insert_monthly_data("2026-01", data1)

        # 第二个月只有2个数据项
        data2 = pd.DataFrame(
            {
                "item_name": ["Item A", "Item B"],
                "value": [15.0, 25.0],
                "unit": ["V", "V"],
            }
        )
        db.insert_monthly_data("2026-02", data2)

        result = analyzer.compare_two_months("2026-01", "2026-02", device_id=1)

        # 验证结果包含所有数据项
        assert len(result) == 3

        # 验证缺失项被标记
        item_c = result[result["item_name"] == "Item C"].iloc[0]
        assert pd.notna(item_c["missing_in"])
        assert item_c["missing_in"] == "2026-02"
        assert item_c["change_status"] == "missing"

    def test_compare_two_months_empty_month(self, db, analyzer):
        """测试空月份的对比"""
        data1 = pd.DataFrame({"item_name": ["Item A"], "value": [10.0], "unit": ["V"]})
        db.insert_monthly_data("2026-01", data1)

        with pytest.raises(DataValidationError, match="没有数据"):
            analyzer.compare_two_months("2026-01", "2026-02", device_id=1)

    def test_calculate_statistics(self, sample_data, analyzer):
        """测试统计分析功能"""
        stats = analyzer.calculate_statistics("Forward Power", device_id=1)

        # 验证统计指标
        assert stats["count"] == 3
        assert abs(stats["mean"] - 105.0) < 1e-6
        assert stats["min"] == 100.0
        assert stats["max"] == 110.0
        assert stats["median"] == 105.0
        assert "std" in stats
        assert "q25" in stats
        assert "q75" in stats

    def test_calculate_statistics_with_date_range(self, sample_data, analyzer):
        """测试指定日期范围的统计分析"""
        stats = analyzer.calculate_statistics(
            "Forward Power", start_month="2026-02", end_month="2026-03"
        )

        # 只包含2月和3月的数据
        assert stats["count"] == 2
        assert abs(stats["mean"] - 107.5) < 1e-6

    def test_calculate_statistics_no_data(self, db, analyzer):
        """测试没有数据的统计分析"""
        with pytest.raises(DataValidationError, match="没有历史记录"):
            analyzer.calculate_statistics("Nonexistent Item", device_id=1)

    def test_detect_anomalies(self, db, analyzer):
        """测试异常值检测"""
        # 插入包含异常值的数据
        months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
        values = [100.0, 102.0, 101.0, 200.0, 103.0, 99.0]  # 200.0是明显的异常值

        for month, value in zip(months, values):
            data = pd.DataFrame(
                {"item_name": ["Test Item"], "value": [value], "unit": ["W"]}
            )
            db.insert_monthly_data(month, data)

        anomalies = analyzer.detect_anomalies("Test Item", device_id=1, threshold=2.0)

        # 验证检测到异常值
        assert len(anomalies) > 0
        assert any(month == "2026-04" for month, _ in anomalies)

    def test_detect_anomalies_no_anomalies(self, sample_data, analyzer):
        """测试没有异常值的情况"""
        anomalies = analyzer.detect_anomalies("PA Voltage", device_id=1, threshold=2.0)

        # PA Voltage的值变化不大，应该没有异常值
        assert len(anomalies) == 0

    def test_detect_anomalies_insufficient_data(self, db, analyzer):
        """测试数据不足的异常检测"""
        # 只插入2条数据
        data = pd.DataFrame(
            {"item_name": ["Test Item"], "value": [100.0], "unit": ["W"]}
        )
        db.insert_monthly_data("2026-01", data)

        data = pd.DataFrame(
            {"item_name": ["Test Item"], "value": [110.0], "unit": ["W"]}
        )
        db.insert_monthly_data("2026-02", data)

        anomalies = analyzer.detect_anomalies("Test Item", device_id=1)

        # 数据不足，应该返回空列表
        assert len(anomalies) == 0

    def test_detect_anomalies_zero_std(self, db, analyzer):
        """测试标准差为零的情况"""
        # 插入相同值的数据
        for i in range(5):
            data = pd.DataFrame(
                {"item_name": ["Test Item"], "value": [100.0], "unit": ["W"]}
            )
            db.insert_monthly_data(f"2026-0{i+1}", data)

        anomalies = analyzer.detect_anomalies("Test Item", device_id=1)

        # 标准差为0，应该没有异常值
        assert len(anomalies) == 0
