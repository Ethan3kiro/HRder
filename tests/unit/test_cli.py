"""
CLI模块的单元测试

测试命令行界面的各个功能流程
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import pandas as pd
from io import StringIO

from src.cli import TransmitterCLI
from src.exceptions import OCRError, DatabaseError, DataValidationError, FileError


class TestTransmitterCLI:
    """CLI单元测试类"""

    @pytest.fixture
    def mock_cli(self):
        """创建带有mock依赖的CLI实例"""
        with patch("src.cli.TransmitterDatabase") as mock_db_class, patch(
            "src.cli.OCRExtractor"
        ) as mock_ocr_class, patch(
            "src.cli.DataAnalyzer"
        ) as mock_analyzer_class, patch(
            "src.cli.DataVisualizer"
        ) as mock_viz_class, patch(
            "src.cli.DataExporter"
        ) as mock_exp_class:
            # 创建mock实例
            mock_db = Mock()
            mock_db_class.return_value = mock_db

            mock_ocr = Mock()
            mock_ocr_class.return_value = mock_ocr

            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer

            mock_viz = Mock()
            mock_viz_class.return_value = mock_viz

            mock_exp = Mock()
            mock_exp_class.return_value = mock_exp

            cli = TransmitterCLI()

            # 附加mock对象以便测试访问
            cli.mock_db = mock_db
            cli.mock_ocr = mock_ocr
            cli.mock_analyzer = mock_analyzer
            cli.mock_viz = mock_viz
            cli.mock_exp = mock_exp

            yield cli

    def test_cli_initialization(self, mock_cli):
        """测试CLI初始化"""
        assert mock_cli.database is not None
        assert mock_cli.ocr_extractor is not None
        assert mock_cli.analyzer is not None
        assert mock_cli.visualizer is not None
        assert mock_cli.exporter is not None
        assert mock_cli.running is True

    def test_show_main_menu(self, mock_cli, capsys):
        """测试主菜单显示"""
        mock_cli.show_main_menu()

        captured = capsys.readouterr()
        assert "主菜单" in captured.out
        assert "1. 录入数据" in captured.out
        assert "2. 两月对比" in captured.out
        assert "3. 绘制趋势" in captured.out
        assert "4. 数据管理" in captured.out
        assert "5. 退出" in captured.out

    def test_validate_menu_choice_valid(self, mock_cli):
        """测试有效菜单选项验证"""
        assert mock_cli._validate_menu_choice("1", 1, 5) == 1
        assert mock_cli._validate_menu_choice("3", 1, 5) == 3
        assert mock_cli._validate_menu_choice("5", 1, 5) == 5

    def test_validate_menu_choice_invalid(self, mock_cli):
        """测试无效菜单选项验证"""
        assert mock_cli._validate_menu_choice("0", 1, 5) is None
        assert mock_cli._validate_menu_choice("6", 1, 5) is None
        assert mock_cli._validate_menu_choice("abc", 1, 5) is None
        assert mock_cli._validate_menu_choice("", 1, 5) is None

    def test_validate_yes_no_yes(self, mock_cli):
        """测试"是"输入验证"""
        assert mock_cli._validate_yes_no("y") is True
        assert mock_cli._validate_yes_no("Y") is True
        assert mock_cli._validate_yes_no("yes") is True
        assert mock_cli._validate_yes_no("YES") is True

    def test_validate_yes_no_no(self, mock_cli):
        """测试"否"输入验证"""
        assert mock_cli._validate_yes_no("n") is False
        assert mock_cli._validate_yes_no("N") is False
        assert mock_cli._validate_yes_no("no") is False
        assert mock_cli._validate_yes_no("NO") is False

    def test_validate_yes_no_invalid(self, mock_cli):
        """测试无效是/否输入"""
        assert mock_cli._validate_yes_no("maybe") is None
        assert mock_cli._validate_yes_no("123") is None
        assert mock_cli._validate_yes_no("") is None

    def test_safe_float_input_valid(self, mock_cli):
        """测试有效浮点数输入"""
        with patch("builtins.input", return_value="12.5"):
            result = mock_cli._safe_float_input("test")
            assert result == 12.5

        with patch("builtins.input", return_value="-3.14"):
            result = mock_cli._safe_float_input("test")
            assert result == -3.14

    def test_safe_float_input_invalid(self, mock_cli):
        """测试无效浮点数输入"""
        with patch("builtins.input", return_value="abc"):
            result = mock_cli._safe_float_input("test")
            assert result is None

        with patch("builtins.input", return_value=""):
            result = mock_cli._safe_float_input("test")
            assert result is None

    def test_handle_data_entry_ocr_unavailable(self, mock_cli, capsys):
        """测试OCR不可用时的数据录入"""
        mock_cli.ocr_extractor = None

        mock_cli.handle_data_entry()

        captured = capsys.readouterr()
        assert "OCR提取器不可用" in captured.out

    def test_handle_data_entry_file_not_found(self, mock_cli):
        """测试文件不存在的错误处理"""
        with patch("builtins.input", side_effect=["nonexistent.png", "q"]):
            mock_cli.handle_data_entry()

        # 应该不会抛出异常，而是提示错误并允许重新输入

    def test_handle_data_entry_success(self, mock_cli):
        """测试成功的数据录入流程"""
        # 准备测试数据
        test_image_path = Path("test.png")
        test_month = "2026-01"

        # Mock提取的数据
        extracted_data = pd.DataFrame(
            {
                "item_name": ["Voltage", "Current"],
                "value": [12.5, 2.3],
                "unit": ["V", "A"],
            }
        )

        mock_cli.mock_ocr.extract_from_image.return_value = extracted_data
        mock_cli.mock_db.query_by_month.return_value = pd.DataFrame()  # 没有现有数据

        # 模拟用户输入
        with patch(
            "builtins.input",
            side_effect=[str(test_image_path), test_month, "y"],  # 图像路径  # 月份  # 确认保存
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "src.config.Config.is_supported_image", return_value=True
        ):
            mock_cli.handle_data_entry()

        # 验证调用
        mock_cli.mock_ocr.extract_from_image.assert_called_once()
        mock_cli.mock_db.insert_monthly_data.assert_called_once_with(
            test_month, extracted_data, overwrite=False
        )

    def test_handle_comparison_insufficient_data(self, mock_cli, capsys):
        """测试数据不足时的两月对比"""
        mock_cli.mock_db.get_available_months.return_value = ["2026-01"]  # 只有一个月

        mock_cli.handle_comparison()

        captured = capsys.readouterr()
        assert "至少需要两个月份的数据" in captured.out

    def test_handle_comparison_success(self, mock_cli):
        """测试成功的两月对比流程"""
        # 准备测试数据
        available_months = ["2026-01", "2026-02", "2026-03"]
        comparison_result = pd.DataFrame(
            {
                "item_name": ["Voltage", "Current"],
                "value_month1": [12.5, 2.3],
                "value_month2": [13.0, 2.5],
                "unit": ["V", "A"],
                "absolute_change": [0.5, 0.2],
                "relative_change": [4.0, 8.7],
                "change_status": ["increase", "increase"],
                "missing_in": [None, None],
            }
        )

        mock_cli.mock_db.get_available_months.return_value = available_months
        mock_cli.mock_analyzer.compare_two_months.return_value = comparison_result

        # 模拟用户输入
        with patch(
            "builtins.input", side_effect=["1", "2", "4"]  # 选择第一个月份  # 选择第二个月份  # 返回主菜单
        ):
            mock_cli.handle_comparison()

        # 验证调用
        mock_cli.mock_analyzer.compare_two_months.assert_called_once_with(
            "2026-01", "2026-02"
        )

    def test_handle_trend_visualization_no_data(self, mock_cli, capsys):
        """测试没有数据时的趋势可视化"""
        mock_cli.mock_db.get_all_items.return_value = []

        mock_cli.handle_trend_visualization()

        captured = capsys.readouterr()
        assert "没有数据项" in captured.out

    def test_handle_trend_visualization_success(self, mock_cli):
        """测试成功的趋势可视化流程"""
        # 准备测试数据
        all_items = ["Voltage", "Current", "Power"]
        available_months = ["2026-01", "2026-02", "2026-03"]

        mock_cli.mock_db.get_all_items.return_value = all_items
        mock_cli.mock_db.get_available_months.return_value = available_months

        # 模拟用户输入
        with patch(
            "builtins.input",
            side_effect=[
                "1,2",  # 选择数据项1和2
                "n",  # 不指定时间范围
                "n",  # 不设置阈值
                "trend.png",  # 输出文件路径
                "n",  # 不使用交互式图表
            ],
        ):
            mock_cli.handle_trend_visualization()

        # 验证调用
        mock_cli.mock_viz.plot_trend_chart.assert_called_once()
        call_args = mock_cli.mock_viz.plot_trend_chart.call_args
        assert call_args[1]["item_names"] == ["Voltage", "Current"]

    def test_handle_data_management_menu(self, mock_cli):
        """测试数据管理菜单"""
        # 模拟用户输入：选择返回主菜单
        with patch("builtins.input", return_value="5"):
            mock_cli.handle_data_management()

        # 应该正常返回，不抛出异常

    def test_query_monthly_data(self, mock_cli):
        """测试查询月度数据"""
        # 准备测试数据
        available_months = ["2026-01", "2026-02"]
        month_data = pd.DataFrame(
            {
                "item_name": ["Voltage", "Current"],
                "value": [12.5, 2.3],
                "unit": ["V", "A"],
            }
        )

        mock_cli.mock_db.get_available_months.return_value = available_months
        mock_cli.mock_db.query_by_month.return_value = month_data

        # 模拟用户输入
        with patch("builtins.input", return_value="1"):
            mock_cli._query_monthly_data()

        # 验证调用
        mock_cli.mock_db.query_by_month.assert_called_once_with("2026-01")

    def test_query_item_history(self, mock_cli):
        """测试查询数据项历史"""
        # 准备测试数据
        all_items = ["Voltage", "Current"]
        item_history = pd.DataFrame(
            {"month": ["2026-01", "2026-02"], "value": [12.5, 13.0], "unit": ["V", "V"]}
        )

        mock_cli.mock_db.get_all_items.return_value = all_items
        mock_cli.mock_db.query_by_item.return_value = item_history
        mock_cli.mock_analyzer.calculate_statistics.return_value = {
            "mean": 12.75,
            "std": 0.25,
            "min": 12.5,
            "max": 13.0,
            "median": 12.75,
        }

        # 模拟用户输入
        with patch("builtins.input", return_value="1"):
            mock_cli._query_item_history()

        # 验证调用
        mock_cli.mock_db.query_by_item.assert_called_once_with("Voltage")
        mock_cli.mock_analyzer.calculate_statistics.assert_called_once_with("Voltage")

    def test_delete_monthly_data(self, mock_cli):
        """测试删除月度数据"""
        # 准备测试数据
        available_months = ["2026-01", "2026-02"]

        mock_cli.mock_db.get_available_months.return_value = available_months
        mock_cli.mock_db.delete_month.return_value = 5  # 删除了5条记录

        # 模拟用户输入
        with patch("builtins.input", side_effect=["1", "y"]):  # 选择月份1，确认删除
            mock_cli._delete_monthly_data()

        # 验证调用
        mock_cli.mock_db.delete_month.assert_called_once_with("2026-01")

    def test_export_monthly_data_excel(self, mock_cli):
        """测试导出月度数据为Excel"""
        # 准备测试数据
        available_months = ["2026-01"]
        month_data = pd.DataFrame(
            {"item_name": ["Voltage"], "value": [12.5], "unit": ["V"]}
        )

        mock_cli.mock_db.get_available_months.return_value = available_months
        mock_cli.mock_db.query_by_month.return_value = month_data

        # 模拟用户输入
        with patch("builtins.input", side_effect=["1", "1", "output.xlsx"]):
            mock_cli._export_monthly_data()

        # 验证调用
        mock_cli.mock_exp.export_to_excel.assert_called_once()

    def test_export_monthly_data_csv(self, mock_cli):
        """测试导出月度数据为CSV"""
        # 准备测试数据
        available_months = ["2026-01"]
        month_data = pd.DataFrame(
            {"item_name": ["Voltage"], "value": [12.5], "unit": ["V"]}
        )

        mock_cli.mock_db.get_available_months.return_value = available_months
        mock_cli.mock_db.query_by_month.return_value = month_data

        # 模拟用户输入
        with patch("builtins.input", side_effect=["1", "2", "output.csv"]):
            mock_cli._export_monthly_data()

        # 验证调用
        mock_cli.mock_exp.export_to_csv.assert_called_once()

    def test_error_handling_ocr_error(self, mock_cli):
        """测试OCR错误处理"""
        test_image_path = Path("test.png")

        mock_cli.mock_ocr.extract_from_image.side_effect = OCRError("OCR failed")

        with patch(
            "builtins.input", side_effect=[str(test_image_path), "2026-01"]
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "src.config.Config.is_supported_image", return_value=True
        ):
            # 应该捕获异常并显示错误消息，而不是崩溃
            mock_cli.handle_data_entry()

    def test_error_handling_database_error(self, mock_cli):
        """测试数据库错误处理"""
        mock_cli.mock_db.get_available_months.side_effect = DatabaseError(
            "Database error"
        )

        # 应该捕获异常并显示错误消息，而不是崩溃
        mock_cli.handle_comparison()
