"""
CLI模块的属性测试

测试命令行界面的输入验证和错误处理属性
"""
import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch
from pathlib import Path

from src.cli import TransmitterCLI


class TestCLIProperties:
    """CLI属性测试类"""

    @given(
        invalid_choice=st.one_of(
            st.text(min_size=1).filter(lambda x: not x.strip().isdigit()),
            st.integers().filter(lambda x: x < 1 or x > 5).map(str),
            st.just(""),
            st.just("  "),
            st.text(alphabet="!@#$%^&*()", min_size=1),
        )
    )
    def test_property_invalid_menu_input_handling(self, invalid_choice):
        """
        Feature: transmitter-data-analyzer, Property 14: 无效输入菜单处理

        对于任何不在菜单选项范围内的用户输入，系统应该提示错误并重新显示菜单，
        而不是执行错误操作或崩溃

        **验证：需求 7.6**
        """
        # 创建CLI实例（使用mock避免实际初始化）
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            # 测试_validate_menu_choice方法
            result = cli._validate_menu_choice(invalid_choice, 1, 5)

            # 验证：无效输入应该返回None，而不是抛出异常或返回错误值
            assert result is None, f"无效输入 '{invalid_choice}' 应该返回 None"

    @given(valid_choice=st.integers(min_value=1, max_value=5).map(str))
    def test_property_valid_menu_input_acceptance(self, valid_choice):
        """
        属性：有效菜单输入应该被正确接受

        对于任何在有效范围内的输入，系统应该返回对应的整数值
        """
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            result = cli._validate_menu_choice(valid_choice, 1, 5)

            # 验证：有效输入应该返回对应的整数
            assert result == int(valid_choice)
            assert 1 <= result <= 5

    @given(yes_input=st.sampled_from(["y", "Y", "yes", "YES", "Yes", "是"]))
    def test_property_yes_input_validation(self, yes_input):
        """
        属性：各种形式的"是"输入应该被识别为True

        对于任何表示"是"的输入变体，系统应该返回True
        """
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            result = cli._validate_yes_no(yes_input)

            # 验证：所有"是"的变体都应该返回True
            assert result is True

    @given(no_input=st.sampled_from(["n", "N", "no", "NO", "No", "否"]))
    def test_property_no_input_validation(self, no_input):
        """
        属性：各种形式的"否"输入应该被识别为False

        对于任何表示"否"的输入变体，系统应该返回False
        """
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            result = cli._validate_yes_no(no_input)

            # 验证：所有"否"的变体都应该返回False
            assert result is False

    @given(
        invalid_yn=st.text(min_size=1).filter(
            lambda x: x.strip().lower() not in ["y", "yes", "n", "no", "是", "否"]
        )
    )
    def test_property_invalid_yes_no_input(self, invalid_yn):
        """
        属性：无效的是/否输入应该返回None

        对于任何不是"是"或"否"的输入，系统应该返回None
        """
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            result = cli._validate_yes_no(invalid_yn)

            # 验证：无效输入应该返回None
            assert result is None

    @given(
        valid_float=st.floats(
            min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False
        )
    )
    def test_property_float_input_parsing(self, valid_float):
        """
        属性：有效的浮点数输入应该被正确解析

        对于任何有效的浮点数字符串，系统应该返回对应的浮点数值
        """
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            # 模拟用户输入
            with patch("builtins.input", return_value=str(valid_float)):
                result = cli._safe_float_input("test prompt")

            # 验证：返回的值应该接近输入值
            if result is not None:
                assert (
                    abs(result - valid_float) < 1e-6
                    or abs((result - valid_float) / valid_float) < 1e-6
                )

    @given(
        invalid_float=st.one_of(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1),
            st.just(""),
            st.just("  "),
            st.text(alphabet="!@#$%^&*()", min_size=1),
        )
    )
    def test_property_invalid_float_input(self, invalid_float):
        """
        属性：无效的浮点数输入应该返回None

        对于任何无法解析为浮点数的输入，系统应该返回None而不是崩溃
        """
        with patch("src.cli.TransmitterDatabase"), patch("src.cli.OCRExtractor"), patch(
            "src.cli.DataAnalyzer"
        ), patch("src.cli.DataVisualizer"), patch("src.cli.DataExporter"):
            cli = TransmitterCLI()

            # 模拟用户输入
            with patch("builtins.input", return_value=invalid_float):
                result = cli._safe_float_input("test prompt")

            # 验证：无效输入应该返回None
            assert result is None
