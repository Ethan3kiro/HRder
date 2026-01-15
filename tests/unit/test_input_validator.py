"""
输入验证模块的单元测试
"""
import pytest
from pathlib import Path
from src.input_validator import InputValidator


class TestInputValidator:
    """InputValidator类的测试"""

    def test_validate_month_format_valid(self):
        """测试有效的月份格式"""
        assert InputValidator.validate_month_format("2026-01") is True
        assert InputValidator.validate_month_format("2025-12") is True
        assert InputValidator.validate_month_format("2020-06") is True

    def test_validate_month_format_invalid(self):
        """测试无效的月份格式"""
        assert InputValidator.validate_month_format("2026-1") is False
        assert InputValidator.validate_month_format("26-01") is False
        assert InputValidator.validate_month_format("2026/01") is False
        assert InputValidator.validate_month_format("202601") is False
        assert InputValidator.validate_month_format("") is False

    def test_validate_numeric_input_valid(self):
        """测试有效的数值输入"""
        assert InputValidator.validate_numeric_input("123.45") == 123.45
        assert InputValidator.validate_numeric_input("0") == 0.0
        assert InputValidator.validate_numeric_input("-10.5") == -10.5

    def test_validate_numeric_input_with_range(self):
        """测试带范围的数值输入"""
        assert InputValidator.validate_numeric_input("50", min_val=0, max_val=100) == 50
        assert InputValidator.validate_numeric_input("0", min_val=0, max_val=100) == 0
        assert InputValidator.validate_numeric_input("100", min_val=0, max_val=100) == 100
        assert (
            InputValidator.validate_numeric_input("150", min_val=0, max_val=100) is None
        )
        assert (
            InputValidator.validate_numeric_input("-10", min_val=0, max_val=100) is None
        )

    def test_validate_numeric_input_invalid(self):
        """测试无效的数值输入"""
        assert InputValidator.validate_numeric_input("abc") is None
        assert InputValidator.validate_numeric_input("12.34.56") is None
        assert InputValidator.validate_numeric_input("") is None

    def test_validate_integer_input_valid(self):
        """测试有效的整数输入"""
        assert InputValidator.validate_integer_input("123") == 123
        assert InputValidator.validate_integer_input("0") == 0
        assert InputValidator.validate_integer_input("-10") == -10

    def test_validate_integer_input_with_range(self):
        """测试带范围的整数输入"""
        assert InputValidator.validate_integer_input("5", min_val=1, max_val=10) == 5
        assert InputValidator.validate_integer_input("1", min_val=1, max_val=10) == 1
        assert InputValidator.validate_integer_input("10", min_val=1, max_val=10) == 10
        assert (
            InputValidator.validate_integer_input("11", min_val=1, max_val=10) is None
        )
        assert InputValidator.validate_integer_input("0", min_val=1, max_val=10) is None

    def test_validate_integer_input_invalid(self):
        """测试无效的整数输入"""
        assert InputValidator.validate_integer_input("12.5") is None
        assert InputValidator.validate_integer_input("abc") is None
        assert InputValidator.validate_integer_input("") is None

    def test_validate_choice_valid(self):
        """测试有效的选项输入"""
        choices = ["1", "2", "3"]
        assert InputValidator.validate_choice("1", choices) is True
        assert InputValidator.validate_choice("2", choices) is True
        assert InputValidator.validate_choice("3", choices) is True

    def test_validate_choice_invalid(self):
        """测试无效的选项输入"""
        choices = ["1", "2", "3"]
        assert InputValidator.validate_choice("4", choices) is False
        assert InputValidator.validate_choice("0", choices) is False
        assert InputValidator.validate_choice("", choices) is False

    def test_validate_file_path_not_required_to_exist(self):
        """测试文件路径验证（不要求存在）"""
        path = InputValidator.validate_file_path("/tmp/test.txt", must_exist=False)
        assert isinstance(path, Path)
        assert path == Path("/tmp/test.txt")

    def test_validate_file_path_with_home_expansion(self):
        """测试文件路径验证（波浪号展开）"""
        path = InputValidator.validate_file_path("~/test.txt", must_exist=False)
        assert isinstance(path, Path)
        assert "~" not in str(path)

    def test_validate_yes_no_yes(self):
        """测试是的输入"""
        assert InputValidator.validate_yes_no("y") is True
        assert InputValidator.validate_yes_no("Y") is True
        assert InputValidator.validate_yes_no("yes") is True
        assert InputValidator.validate_yes_no("YES") is True
        assert InputValidator.validate_yes_no("是") is True

    def test_validate_yes_no_no(self):
        """测试否的输入"""
        assert InputValidator.validate_yes_no("n") is False
        assert InputValidator.validate_yes_no("N") is False
        assert InputValidator.validate_yes_no("no") is False
        assert InputValidator.validate_yes_no("NO") is False
        assert InputValidator.validate_yes_no("否") is False

    def test_validate_yes_no_invalid(self):
        """测试无效的是/否输入"""
        assert InputValidator.validate_yes_no("maybe") is None
        assert InputValidator.validate_yes_no("ok") is None
        assert InputValidator.validate_yes_no("") is None

    def test_validate_non_empty_valid(self):
        """测试非空输入"""
        assert InputValidator.validate_non_empty("hello") is True
        assert InputValidator.validate_non_empty("123") is True
        assert InputValidator.validate_non_empty("  text  ") is True

    def test_validate_non_empty_invalid(self):
        """测试空输入"""
        assert InputValidator.validate_non_empty("") is False
        assert InputValidator.validate_non_empty("   ") is False
        assert InputValidator.validate_non_empty("\t\n") is False
