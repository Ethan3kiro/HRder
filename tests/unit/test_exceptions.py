"""
异常处理单元测试

测试异常类型的抛出、捕获和错误消息的清晰性
"""
import pytest
import logging
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from src.exceptions import (
    TransmitterError,
    OCRError,
    DatabaseError,
    DataValidationError,
    FileError,
    handle_errors,
)
from src.logging_config import setup_logging


class TestExceptionHierarchy:
    """测试异常类层次结构"""

    def test_transmitter_error_is_base_exception(self):
        """测试TransmitterError是基础异常类"""
        error = TransmitterError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_ocr_error_inherits_from_transmitter_error(self):
        """测试OCRError继承自TransmitterError"""
        error = OCRError("OCR failed")
        assert isinstance(error, TransmitterError)
        assert isinstance(error, Exception)
        assert str(error) == "OCR failed"

    def test_database_error_inherits_from_transmitter_error(self):
        """测试DatabaseError继承自TransmitterError"""
        error = DatabaseError("Database connection failed")
        assert isinstance(error, TransmitterError)
        assert isinstance(error, Exception)
        assert str(error) == "Database connection failed"

    def test_data_validation_error_inherits_from_transmitter_error(self):
        """测试DataValidationError继承自TransmitterError"""
        error = DataValidationError("Invalid data format")
        assert isinstance(error, TransmitterError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid data format"

    def test_file_error_inherits_from_transmitter_error(self):
        """测试FileError继承自TransmitterError"""
        error = FileError("File not found")
        assert isinstance(error, TransmitterError)
        assert isinstance(error, Exception)
        assert str(error) == "File not found"


class TestHandleErrorsDecorator:
    """测试handle_errors装饰器"""

    def test_decorator_catches_file_not_found_error(self):
        """测试装饰器捕获FileNotFoundError"""

        @handle_errors
        def read_file(path):
            with open(path) as f:
                return f.read()

        with pytest.raises(FileError) as exc_info:
            read_file("/nonexistent/file.txt")

        assert "文件不存在" in str(exc_info.value)

    def test_decorator_catches_permission_error(self):
        """测试装饰器捕获PermissionError"""

        @handle_errors
        def access_file():
            raise PermissionError("Permission denied")

        with pytest.raises(FileError) as exc_info:
            access_file()

        assert "没有权限访问文件" in str(exc_info.value)

    def test_decorator_catches_sqlite_error(self):
        """测试装饰器捕获sqlite3.Error"""

        @handle_errors
        def database_operation():
            raise sqlite3.Error("Database is locked")

        with pytest.raises(DatabaseError) as exc_info:
            database_operation()

        assert "数据库操作失败" in str(exc_info.value)

    def test_decorator_catches_value_error(self):
        """测试装饰器捕获ValueError"""

        @handle_errors
        def parse_value(value):
            return int(value)

        with pytest.raises(DataValidationError) as exc_info:
            parse_value("not a number")

        assert "数据格式错误" in str(exc_info.value)

    def test_decorator_catches_type_error(self):
        """测试装饰器捕获TypeError"""

        @handle_errors
        def add_numbers(a, b):
            return a + b

        with pytest.raises(DataValidationError) as exc_info:
            add_numbers("string", 5)

        assert "数据格式错误" in str(exc_info.value)

    def test_decorator_reraises_transmitter_error(self):
        """测试装饰器重新抛出TransmitterError"""

        @handle_errors
        def custom_error():
            raise OCRError("Custom OCR error")

        with pytest.raises(OCRError) as exc_info:
            custom_error()

        assert str(exc_info.value) == "Custom OCR error"

    def test_decorator_catches_generic_exception(self):
        """测试装饰器捕获通用异常"""

        @handle_errors
        def unknown_error():
            raise RuntimeError("Unknown error")

        with pytest.raises(TransmitterError) as exc_info:
            unknown_error()

        assert "操作失败" in str(exc_info.value)

    def test_decorator_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""

        @handle_errors
        def my_function():
            """This is my function"""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function"

    def test_decorator_returns_value_on_success(self):
        """测试装饰器在成功时返回值"""

        @handle_errors
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"


class TestErrorLogging:
    """测试错误日志记录"""

    def test_file_error_is_logged(self):
        """测试FileError被记录到日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = setup_logging(
                log_level="DEBUG", log_dir=log_dir, log_to_console=False
            )

            @handle_errors
            def failing_function():
                raise FileNotFoundError("test.txt")

            with pytest.raises(FileError):
                failing_function()

            # 检查日志文件
            log_files = list(log_dir.glob("transmitter_*.log"))
            assert len(log_files) > 0

            log_content = log_files[0].read_text(encoding="utf-8")
            assert "ERROR" in log_content
            assert "文件未找到" in log_content

            # 清理
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def test_database_error_is_logged(self):
        """测试DatabaseError被记录到日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = setup_logging(
                log_level="DEBUG", log_dir=log_dir, log_to_console=False
            )

            @handle_errors
            def failing_function():
                raise sqlite3.Error("Database error")

            with pytest.raises(DatabaseError):
                failing_function()

            # 检查日志文件
            log_files = list(log_dir.glob("transmitter_*.log"))
            assert len(log_files) > 0

            log_content = log_files[0].read_text(encoding="utf-8")
            assert "ERROR" in log_content
            assert "数据库错误" in log_content

            # 清理
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def test_validation_error_is_logged(self):
        """测试DataValidationError被记录到日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = setup_logging(
                log_level="DEBUG", log_dir=log_dir, log_to_console=False
            )

            @handle_errors
            def failing_function():
                raise ValueError("Invalid value")

            with pytest.raises(DataValidationError):
                failing_function()

            # 检查日志文件
            log_files = list(log_dir.glob("transmitter_*.log"))
            assert len(log_files) > 0

            log_content = log_files[0].read_text(encoding="utf-8")
            assert "ERROR" in log_content
            assert "数据验证错误" in log_content

            # 清理
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def test_generic_error_includes_stack_trace(self):
        """测试通用错误包含堆栈跟踪"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = setup_logging(
                log_level="DEBUG", log_dir=log_dir, log_to_console=False
            )

            @handle_errors
            def failing_function():
                raise RuntimeError("Unexpected error")

            with pytest.raises(TransmitterError):
                failing_function()

            # 检查日志文件
            log_files = list(log_dir.glob("transmitter_*.log"))
            assert len(log_files) > 0

            log_content = log_files[0].read_text(encoding="utf-8")
            assert "ERROR" in log_content
            assert "未预期的错误" in log_content
            # 堆栈跟踪应该包含Traceback
            assert "Traceback" in log_content or "RuntimeError" in log_content

            # 清理
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestErrorMessages:
    """测试错误消息的清晰性"""

    def test_file_error_message_is_clear(self):
        """测试FileError消息清晰"""
        error = FileError("文件不存在: /path/to/file.txt")
        assert "文件不存在" in str(error)
        assert "/path/to/file.txt" in str(error)

    def test_database_error_message_is_clear(self):
        """测试DatabaseError消息清晰"""
        error = DatabaseError("数据库操作失败: table not found")
        assert "数据库操作失败" in str(error)
        assert "table not found" in str(error)

    def test_validation_error_message_is_clear(self):
        """测试DataValidationError消息清晰"""
        error = DataValidationError("数据格式错误: expected integer, got string")
        assert "数据格式错误" in str(error)
        assert "expected integer" in str(error)

    def test_ocr_error_message_is_clear(self):
        """测试OCRError消息清晰"""
        error = OCRError("OCR识别失败: image quality too low")
        assert "OCR识别失败" in str(error)
        assert "image quality too low" in str(error)

    def test_generic_error_message_is_clear(self):
        """测试通用错误消息清晰"""
        error = TransmitterError("操作失败: unexpected condition")
        assert "操作失败" in str(error)
        assert "unexpected condition" in str(error)


class TestErrorHandlingInContext:
    """测试实际使用场景中的错误处理"""

    def test_multiple_errors_in_sequence(self):
        """测试连续多个错误的处理"""
        errors_caught = []

        @handle_errors
        def operation1():
            raise FileNotFoundError("file1.txt")

        @handle_errors
        def operation2():
            raise ValueError("Invalid value")

        @handle_errors
        def operation3():
            raise sqlite3.Error("Database error")

        # 捕获所有错误
        try:
            operation1()
        except FileError as e:
            errors_caught.append(type(e))

        try:
            operation2()
        except DataValidationError as e:
            errors_caught.append(type(e))

        try:
            operation3()
        except DatabaseError as e:
            errors_caught.append(type(e))

        # 验证所有错误都被正确捕获和转换
        assert len(errors_caught) == 3
        assert FileError in errors_caught
        assert DataValidationError in errors_caught
        assert DatabaseError in errors_caught

    def test_nested_error_handling(self):
        """测试嵌套错误处理"""

        @handle_errors
        def inner_function():
            raise ValueError("Inner error")

        @handle_errors
        def outer_function():
            try:
                inner_function()
            except DataValidationError:
                # 重新抛出为不同类型的错误
                raise OCRError("OCR processing failed due to validation error")

        with pytest.raises(OCRError) as exc_info:
            outer_function()

        assert "OCR processing failed" in str(exc_info.value)
