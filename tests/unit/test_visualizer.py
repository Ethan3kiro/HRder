"""
数据可视化模块单元测试
"""
import pytest
import pandas as pd
from pathlib import Path

from src.visualizer import DataVisualizer, STYLE_CONFIG
from src.database import TransmitterDatabase
from src.exceptions import DataValidationError, FileError


class TestDataVisualizer:
    """数据可视化器单元测试"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()
        return db

    @pytest.fixture
    def visualizer(self, db):
        """创建数据可视化器实例"""
        return DataVisualizer(db)

    @pytest.fixture
    def sample_data(self, db):
        """插入示例数据"""
        # 插入多个月份的数据
        months = ["2026-01", "2026-02", "2026-03"]
        for i, month in enumerate(months):
            data = pd.DataFrame(
                {
                    "item_name": ["Forward Power", "PA Voltage", "Ambient Temp"],
                    "value": [100.0 + i * 5, 12.5 + i * 0.5, 25.0 + i],
                    "unit": ["W", "V", "°C"],
                }
            )
            db.insert_monthly_data(month, data)

        return db

    def test_visualizer_initialization(self, visualizer):
        """测试可视化器初始化"""
        assert visualizer.database is not None

    def test_style_config(self):
        """测试样式配置"""
        assert "figure_size" in STYLE_CONFIG
        assert "color_increase" in STYLE_CONFIG
        assert "color_decrease" in STYLE_CONFIG
        assert "color_no_change" in STYLE_CONFIG
        assert STYLE_CONFIG["color_increase"] == "#FF4444"
        assert STYLE_CONFIG["color_decrease"] == "#44FF44"

    def test_categorize_item_power(self, visualizer):
        """测试功率类别分类"""
        assert visualizer._categorize_item("Forward Power") == "power"
        assert visualizer._categorize_item("Reflected Power") == "power"
        assert visualizer._categorize_item("PA Watt") == "power"

    def test_categorize_item_temperature(self, visualizer):
        """测试温度类别分类"""
        assert visualizer._categorize_item("Ambient Temp") == "temperature"
        assert visualizer._categorize_item("Temperature Sensor") == "temperature"
        assert visualizer._categorize_item("Temp Monitor") == "temperature"

    def test_categorize_item_voltage(self, visualizer):
        """测试电压类别分类"""
        assert visualizer._categorize_item("PA Voltage") == "voltage"
        assert visualizer._categorize_item("Supply Volt") == "voltage"
        assert visualizer._categorize_item("Voltage Monitor") == "voltage"

    def test_categorize_item_current(self, visualizer):
        """测试电流类别分类"""
        assert visualizer._categorize_item("PA Current") == "current"
        assert visualizer._categorize_item("Supply Amp") == "current"
        assert visualizer._categorize_item("Current Draw") == "current"

    def test_categorize_item_other(self, visualizer):
        """测试其他类别分类"""
        assert visualizer._categorize_item("Airflow %") == "other"
        assert visualizer._categorize_item("Random Item") == "other"

    def test_plot_comparison_chart_basic(self, sample_data, visualizer, tmp_path):
        """测试基本对比图表生成"""
        from src.analyzer import DataAnalyzer

        analyzer = DataAnalyzer(sample_data)
        comparison_df = analyzer.compare_two_months("2026-01", "2026-02")

        output_path = tmp_path / "comparison.png"
        visualizer.plot_comparison_chart(comparison_df, output_path)

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_comparison_chart_missing_columns(self, visualizer, tmp_path):
        """测试缺少必需列的对比图表"""
        # 创建缺少必需列的DataFrame
        invalid_df = pd.DataFrame(
            {
                "item_name": ["Item A"],
                "value_month1": [10.0]
                # 缺少 value_month2 和 change_status
            }
        )

        output_path = tmp_path / "comparison.png"

        with pytest.raises(DataValidationError, match="缺少必需字段"):
            visualizer.plot_comparison_chart(invalid_df, output_path)

    def test_plot_comparison_chart_empty_data(self, visualizer, tmp_path):
        """测试空数据的对比图表"""
        # 创建只有缺失项的DataFrame
        empty_df = pd.DataFrame(
            {
                "item_name": ["Item A"],
                "value_month1": [10.0],
                "value_month2": [None],
                "unit": ["V"],
                "absolute_change": [None],
                "relative_change": [None],
                "change_status": ["missing"],
                "missing_in": ["2026-02"],
            }
        )

        output_path = tmp_path / "comparison.png"

        # 应该不会抛出异常，但也不会生成图表
        visualizer.plot_comparison_chart(empty_df, output_path)

    def test_plot_trend_chart_single_item(self, sample_data, visualizer, tmp_path):
        """测试单个数据项的趋势图"""
        output_path = tmp_path / "trend.png"

        visualizer.plot_trend_chart(
            item_names=["Forward Power"], output_path=output_path, interactive=False
        )

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_trend_chart_multiple_items(self, sample_data, visualizer, tmp_path):
        """测试多个数据项的趋势图"""
        output_path = tmp_path / "trend_multi.png"

        visualizer.plot_trend_chart(
            item_names=["Forward Power", "PA Voltage", "Ambient Temp"],
            output_path=output_path,
            interactive=False,
        )

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_trend_chart_with_threshold(self, sample_data, visualizer, tmp_path):
        """测试带阈值线的趋势图"""
        output_path = tmp_path / "trend_threshold.png"

        visualizer.plot_trend_chart(
            item_names=["Forward Power"],
            threshold=105.0,
            output_path=output_path,
            interactive=False,
        )

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_trend_chart_with_date_range(self, sample_data, visualizer, tmp_path):
        """测试指定日期范围的趋势图"""
        output_path = tmp_path / "trend_range.png"

        visualizer.plot_trend_chart(
            item_names=["Forward Power"],
            start_month="2026-02",
            end_month="2026-03",
            output_path=output_path,
            interactive=False,
        )

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_trend_chart_empty_item_list(self, visualizer, tmp_path):
        """测试空数据项列表"""
        output_path = tmp_path / "trend.png"

        with pytest.raises(DataValidationError, match="至少需要指定一个数据项"):
            visualizer.plot_trend_chart(
                item_names=[], output_path=output_path, interactive=False
            )

    def test_plot_trend_chart_nonexistent_item(self, sample_data, visualizer, tmp_path):
        """测试不存在的数据项"""
        output_path = tmp_path / "trend.png"

        # 不应该抛出异常，只是记录警告
        visualizer.plot_trend_chart(
            item_names=["Nonexistent Item"], output_path=output_path, interactive=False
        )

    def test_plot_category_trends_power(self, sample_data, visualizer, tmp_path):
        """测试功率类别趋势图"""
        output_path = tmp_path / "category_power.png"

        visualizer.plot_category_trends(category="power", output_path=output_path)

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_category_trends_temperature(self, sample_data, visualizer, tmp_path):
        """测试温度类别趋势图"""
        output_path = tmp_path / "category_temp.png"

        visualizer.plot_category_trends(category="temperature", output_path=output_path)

        # 验证文件已创建
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_category_trends_invalid_category(
        self, sample_data, visualizer, tmp_path
    ):
        """测试无效类别"""
        output_path = tmp_path / "category.png"

        with pytest.raises(DataValidationError, match="无效的类别"):
            visualizer.plot_category_trends(
                category="invalid_category", output_path=output_path
            )

    def test_plot_category_trends_no_items(self, db, visualizer, tmp_path):
        """测试没有该类别数据项的情况"""
        # 插入一些不属于current类别的数据
        data = pd.DataFrame(
            {"item_name": ["Forward Power"], "value": [100.0], "unit": ["W"]}
        )
        db.insert_monthly_data("2026-01", data)

        output_path = tmp_path / "category.png"

        with pytest.raises(DataValidationError, match="没有找到类别"):
            visualizer.plot_category_trends(category="current", output_path=output_path)

    def test_plot_category_trends_empty_database(self, db, visualizer, tmp_path):
        """测试空数据库"""
        output_path = tmp_path / "category.png"

        with pytest.raises(DataValidationError, match="数据库中没有数据项"):
            visualizer.plot_category_trends(category="power", output_path=output_path)
