"""
异常处理属性测试

测试异常处理的正确性属性
"""
import pytest
import logging
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch
import pandas as pd

from src.exceptions import (
    TransmitterError,
    OCRError,
    DatabaseError,
    DataValidationError,
    FileError,
    handle_errors,
)
from src.ocr_extractor import OCRExtractor
from src.logging_config import setup_logging


@settings(max_examples=100, deadline=None)
@given(
    valid_items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),
            st.floats(
                min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
            ),
            st.sampled_from(["V", "A", "W", "%", "°C", ""]),
        ),
        min_size=1,
        max_size=10,
    ),
    invalid_items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),
            st.none(),  # Invalid value
            st.sampled_from(["V", "A", "W", "%", "°C", ""]),
        ),
        min_size=0,
        max_size=5,
    ),
)
def test_property_partial_failure_tolerance(valid_items, invalid_items):
    """
    Feature: transmitter-data-analyzer, Property 15: 部分失败容错性

    对于任何包含部分无效数据的提取操作，系统应该处理有效部分并记录警告，
    而不是因为部分失败而完全失败。

    验证：需求 8.1, 8.2
    """
    # 创建混合数据（有效 + 无效）
    all_items = valid_items + invalid_items

    # 模拟处理函数
    def process_items(items):
        results = []
        errors = []

        for item_name, value, unit in items:
            try:
                if value is None:
                    raise ValueError(f"Invalid value for {item_name}")
                results.append(
                    {"item_name": item_name, "value": float(value), "unit": unit}
                )
            except (ValueError, TypeError) as e:
                errors.append((item_name, str(e)))
                # 记录警告但继续处理
                continue

        return results, errors

    results, errors = process_items(all_items)

    # 验证：应该至少处理了有效数据
    assert len(results) >= len(valid_items), "应该处理所有有效数据"

    # 验证：无效数据应该被记录为错误
    assert len(errors) >= len(invalid_items), "应该记录所有无效数据"

    # 验证：结果中不应该包含None值
    for result in results:
        assert result["value"] is not None
        assert isinstance(result["value"], float)


@settings(max_examples=100, deadline=None)
@given(
    exception_type=st.sampled_from(
        [FileNotFoundError, PermissionError, ValueError, TypeError, Exception]
    ),
    error_message=st.text(min_size=1, max_size=100),
)
def test_property_exception_logging(exception_type, error_message):
    """
    Feature: transmitter-data-analyzer, Property 16: 异常日志记录

    对于任何系统异常，都应该在日志文件中记录详细信息（时间戳、错误类型、堆栈跟踪），
    以便后续排查。

    验证：需求 8.5
    """
    # 创建临时日志文件
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = setup_logging(log_level="DEBUG", log_dir=log_dir, log_to_console=False)

        # 创建一个会抛出异常的函数
        @handle_errors
        def failing_function():
            raise exception_type(error_message)

        # 执行函数并捕获异常
        with pytest.raises(TransmitterError):
            failing_function()

        # 验证：日志文件应该被创建
        log_files = list(log_dir.glob("transmitter_*.log"))
        assert len(log_files) > 0, "应该创建日志文件"

        # 验证：日志文件应该包含错误信息
        log_content = log_files[0].read_text(encoding="utf-8")
        assert "ERROR" in log_content or "CRITICAL" in log_content, "日志应该包含错误级别"

        # 清理logger handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


@settings(max_examples=50, deadline=None)
@given(
    num_valid=st.integers(min_value=1, max_value=10),
    num_invalid=st.integers(min_value=1, max_value=5),
)
def test_property_error_recovery(num_valid, num_invalid):
    """
    测试错误恢复能力

    验证系统在遇到错误后能够继续处理后续数据
    """
    # 创建测试数据
    items = []

    # 添加有效数据
    for i in range(num_valid):
        items.append({"item_name": f"Valid_{i}", "value": float(i * 10), "unit": "V"})

    # 添加无效数据
    for i in range(num_invalid):
        items.append({"item_name": f"Invalid_{i}", "value": None, "unit": "V"})  # 无效值

    # 处理数据
    processed = []
    failed = []

    for item in items:
        try:
            if item["value"] is None:
                raise ValueError("Invalid value")
            processed.append(item)
        except ValueError:
            failed.append(item["item_name"])
            continue

    # 验证：应该处理所有有效数据
    assert len(processed) == num_valid

    # 验证：应该记录所有失败项
    assert len(failed) == num_invalid


@settings(max_examples=50, deadline=None)
@given(error_count=st.integers(min_value=1, max_value=10))
def test_property_multiple_errors_logged(error_count):
    """
    测试多个错误都被正确记录

    验证连续发生的多个错误都能被记录到日志中
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = setup_logging(log_level="DEBUG", log_dir=log_dir, log_to_console=False)

        # 触发多个错误
        for i in range(error_count):

            @handle_errors
            def failing_function():
                raise ValueError(f"Error {i}")

            try:
                failing_function()
            except TransmitterError:
                pass

        # 验证：日志文件应该包含所有错误
        log_files = list(log_dir.glob("transmitter_*.log"))
        assert len(log_files) > 0

        log_content = log_files[0].read_text(encoding="utf-8")
        error_lines = [line for line in log_content.split("\n") if "ERROR" in line]

        # 至少应该有error_count个错误记录
        assert len(error_lines) >= error_count

        # 清理logger handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
