"""
输入验证模块

提供统一的用户输入验证功能
"""
import re
from typing import Optional, List
from pathlib import Path


class InputValidator:
    """输入验证器"""

    @staticmethod
    def validate_month_format(month: str) -> bool:
        """
        验证月份格式是否为YYYY-MM

        Args:
            month: 月份字符串

        Returns:
            是否符合格式

        Examples:
            >>> InputValidator.validate_month_format("2026-01")
            True
            >>> InputValidator.validate_month_format("2026-1")
            False
            >>> InputValidator.validate_month_format("26-01")
            False
        """
        pattern = r"^\d{4}-\d{2}$"
        return bool(re.match(pattern, month))

    @staticmethod
    def validate_numeric_input(
        value: str, min_val: Optional[float] = None, max_val: Optional[float] = None
    ) -> Optional[float]:
        """
        验证数值输入

        Args:
            value: 输入字符串
            min_val: 最小值（可选）
            max_val: 最大值（可选）

        Returns:
            验证通过返回数值，否则返回None

        Examples:
            >>> InputValidator.validate_numeric_input("123.45")
            123.45
            >>> InputValidator.validate_numeric_input("123", min_val=0, max_val=100)
            None
            >>> InputValidator.validate_numeric_input("abc")
            None
        """
        try:
            num = float(value)

            if min_val is not None and num < min_val:
                return None

            if max_val is not None and num > max_val:
                return None

            return num

        except ValueError:
            return None

    @staticmethod
    def validate_integer_input(
        value: str, min_val: Optional[int] = None, max_val: Optional[int] = None
    ) -> Optional[int]:
        """
        验证整数输入

        Args:
            value: 输入字符串
            min_val: 最小值（可选）
            max_val: 最大值（可选）

        Returns:
            验证通过返回整数，否则返回None

        Examples:
            >>> InputValidator.validate_integer_input("123")
            123
            >>> InputValidator.validate_integer_input("123", min_val=1, max_val=10)
            None
            >>> InputValidator.validate_integer_input("12.5")
            None
        """
        try:
            num = int(value)

            if min_val is not None and num < min_val:
                return None

            if max_val is not None and num > max_val:
                return None

            return num

        except ValueError:
            return None

    @staticmethod
    def validate_choice(choice: str, valid_choices: List[str]) -> bool:
        """
        验证选项输入

        Args:
            choice: 用户选择
            valid_choices: 有效选项列表

        Returns:
            是否为有效选项

        Examples:
            >>> InputValidator.validate_choice("1", ["1", "2", "3"])
            True
            >>> InputValidator.validate_choice("4", ["1", "2", "3"])
            False
        """
        return choice in valid_choices

    @staticmethod
    def validate_file_path(path_str: str, must_exist: bool = True) -> Optional[Path]:
        """
        验证文件路径

        Args:
            path_str: 路径字符串
            must_exist: 是否必须存在

        Returns:
            验证通过返回Path对象，否则返回None

        Examples:
            >>> path = InputValidator.validate_file_path("/tmp/test.txt", must_exist=False)
            >>> isinstance(path, Path)
            True
        """
        try:
            path = Path(path_str).expanduser()

            if must_exist and not path.exists():
                return None

            return path

        except Exception:
            return None

    @staticmethod
    def validate_yes_no(value: str) -> Optional[bool]:
        """
        验证是/否输入

        Args:
            value: 输入字符串

        Returns:
            是返回True，否返回False，无效返回None

        Examples:
            >>> InputValidator.validate_yes_no("y")
            True
            >>> InputValidator.validate_yes_no("yes")
            True
            >>> InputValidator.validate_yes_no("n")
            False
            >>> InputValidator.validate_yes_no("no")
            False
            >>> InputValidator.validate_yes_no("maybe")
            None
        """
        value_lower = value.lower().strip()

        if value_lower in ["y", "yes", "是", "y"]:
            return True
        elif value_lower in ["n", "no", "否", "n"]:
            return False
        else:
            return None

    @staticmethod
    def validate_non_empty(value: str) -> bool:
        """
        验证非空输入

        Args:
            value: 输入字符串

        Returns:
            是否非空

        Examples:
            >>> InputValidator.validate_non_empty("hello")
            True
            >>> InputValidator.validate_non_empty("   ")
            False
            >>> InputValidator.validate_non_empty("")
            False
        """
        return bool(value and value.strip())
