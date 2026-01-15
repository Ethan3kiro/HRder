"""
端到端集成测试

验证完整的数据处理工作流程
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from src.database import TransmitterDatabase
from src.analyzer import DataAnalyzer
from src.visualizer import DataVisualizer
from src.exporter import DataExporter


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_data_month1(self):
        """第一个月的示例数据"""
        return pd.DataFrame(
            {
                "item_name": ["Forward Power", "PA Voltage", "Ambient Temp"],
                "value": [100.0, 12.5, 25.0],
                "unit": ["W", "V", "°C"],
            }
        )

    @pytest.fixture
    def sample_data_month2(self):
        """第二个月的示例数据"""
        return pd.DataFrame(
            {
                "item_name": ["Forward Power", "PA Voltage", "Ambient Temp"],
                "value": [105.0, 12.8, 26.5],
                "unit": ["W", "V", "°C"],
            }
        )

    def test_complete_data_workflow(
        self, temp_dir, sample_data_month1, sample_data_month2
    ):
        """测试完整的数据处理工作流"""
        # 1. 初始化数据库
        db_path = temp_dir / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 2. 插入第一个月数据
        db.insert_monthly_data("2026-01", sample_data_month1, device_id=1)

        # 3. 验证数据已存储
        result = db.query_by_month("2026-01")
        assert len(result) == 3
        assert set(result["item_name"]) == {
            "Forward Power",
            "PA Voltage",
            "Ambient Temp",
        }

        # 4. 插入第二个月数据
        db.insert_monthly_data("2026-02", sample_data_month2, device_id=1)

        # 5. 使用分析器进行对比
        analyzer = DataAnalyzer(db)
        comparison = analyzer.compare_two_months("2026-01", "2026-02", device_id=1)

        # 6. 验证对比结果
        assert len(comparison) == 3
        assert "absolute_change" in comparison.columns
        assert "relative_change" in comparison.columns
        assert "change_status" in comparison.columns

        # 验证具体变化
        forward_power = comparison[comparison["item_name"] == "Forward Power"].iloc[0]
        assert forward_power["absolute_change"] == 5.0
        assert abs(forward_power["relative_change"] - 5.0) < 0.01
        assert forward_power["change_status"] == "increase"

        # 7. 导出对比报告
        exporter = DataExporter()
        report_path = temp_dir / "comparison_report.xlsx"
        exporter.export_comparison_report(comparison, report_path)
        assert report_path.exists()

        # 8. 生成可视化图表
        visualizer = DataVisualizer(db)
        chart_path = temp_dir / "comparison_chart.png"
        visualizer.plot_comparison_chart(comparison, chart_path)
        assert chart_path.exists()

        # 9. 生成趋势图
        trend_path = temp_dir / "trend_chart.png"
        visualizer.plot_trend_chart(
            ["Forward Power"], output_path=trend_path, interactive=False
        )
        assert trend_path.exists()

        # 10. 清理：删除数据
        deleted_count = db.delete_month("2026-01")
        assert deleted_count == 3

        # 验证删除后数据不存在
        result = db.query_by_month("2026-01")
        assert len(result) == 0

    def test_multi_month_trend_analysis(self, temp_dir):
        """测试多月趋势分析"""
        # 初始化数据库
        db_path = temp_dir / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 插入多个月的数据
        months = ["2026-01", "2026-02", "2026-03", "2026-04"]
        values = [100.0, 105.0, 103.0, 108.0]

        for month, value in zip(months, values):
            data = pd.DataFrame(
                {"item_name": ["Forward Power"], "value": [value], "unit": ["W"]}
            )
            db.insert_monthly_data(month, data)

        # 使用分析器计算统计信息
        analyzer = DataAnalyzer(db)
        stats = analyzer.calculate_statistics("Forward Power")

        # 验证统计结果
        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert stats["min"] == 100.0
        assert stats["max"] == 108.0
        assert abs(stats["mean"] - 104.0) < 0.01

        # 生成趋势图
        visualizer = DataVisualizer(db)
        trend_path = temp_dir / "multi_month_trend.png"
        visualizer.plot_trend_chart(
            ["Forward Power"], output_path=trend_path, interactive=False
        )
        assert trend_path.exists()

    def test_data_export_workflow(self, temp_dir, sample_data_month1):
        """测试数据导出工作流"""
        # 初始化数据库
        db_path = temp_dir / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 插入数据
        db.insert_monthly_data("2026-01", sample_data_month1, device_id=1)

        # 查询数据
        result = db.query_by_month("2026-01")

        # 导出为Excel
        exporter = DataExporter()
        excel_path = temp_dir / "export.xlsx"
        exporter.export_to_excel(result, excel_path)
        assert excel_path.exists()

        # 导出为CSV
        csv_path = temp_dir / "export.csv"
        exporter.export_to_csv(result, csv_path)
        assert csv_path.exists()

        # 验证导出的数据可以读回
        df_excel = pd.read_excel(excel_path)
        assert len(df_excel) == 3

        df_csv = pd.read_csv(csv_path)
        assert len(df_csv) == 3

    def test_error_handling_workflow(self, temp_dir):
        """测试错误处理工作流"""
        from src.exceptions import DataValidationError

        # 初始化数据库
        db_path = temp_dir / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 测试查询不存在的月份
        result = db.query_by_month("2099-12")
        assert len(result) == 0

        # 测试对比不存在的月份 - 应该抛出异常
        analyzer = DataAnalyzer(db)
        with pytest.raises(DataValidationError):
            analyzer.compare_two_months("2099-01", "2099-02", device_id=1)

        # 测试无效的月份格式
        invalid_data = pd.DataFrame(
            {"item_name": ["Test"], "value": [1.0], "unit": ["V"]}
        )

        with pytest.raises(ValueError):
            db.insert_monthly_data("invalid-format", invalid_data, device_id=1)

    def test_module_integration(self, temp_dir, sample_data_month1, sample_data_month2):
        """测试模块间集成"""
        # 初始化所有模块
        db_path = temp_dir / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        analyzer = DataAnalyzer(db)
        visualizer = DataVisualizer(db)
        exporter = DataExporter()

        # 插入数据
        db.insert_monthly_data("2026-01", sample_data_month1, device_id=1)
        db.insert_monthly_data("2026-02", sample_data_month2, device_id=1)

        # 分析器使用数据库
        comparison = analyzer.compare_two_months("2026-01", "2026-02", device_id=1)
        assert len(comparison) > 0

        # 可视化器使用数据库
        chart_path = temp_dir / "integration_chart.png"
        visualizer.plot_comparison_chart(comparison, chart_path)
        assert chart_path.exists()

        # 导出器使用分析结果
        report_path = temp_dir / "integration_report.xlsx"
        exporter.export_comparison_report(comparison, report_path)
        assert report_path.exists()

        # 验证所有模块协同工作
        assert db.get_available_months() == ["2026-01", "2026-02"]
        assert len(db.get_all_items()) == 3
