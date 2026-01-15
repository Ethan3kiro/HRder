"""
日志配置模块单元测试
"""
import pytest
from pathlib import Path
import logging
from src.logging_config import setup_logging, get_logger, get_default_log_path


class TestLoggingConfig:
    """日志配置测试类"""

    def test_get_default_log_path(self):
        """测试获取默认日志路径"""
        log_path = get_default_log_path()

        assert isinstance(log_path, Path)
        assert log_path.exists()
        assert log_path.is_dir()
        assert "transmitter_logs" in str(log_path)

    def test_setup_logging_basic(self, tmp_path):
        """测试基本日志配置"""
        logger = setup_logging(
            log_level="INFO", log_dir=tmp_path, log_to_file=True, log_to_console=False
        )

        assert isinstance(logger, logging.Logger)
        assert logger.name == "transmitter"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_file_creation(self, tmp_path):
        """测试日志文件创建"""
        logger = setup_logging(
            log_level="DEBUG", log_dir=tmp_path, log_to_file=True, log_to_console=False
        )

        # 写入一条日志
        logger.info("测试日志消息")

        # 检查日志文件是否创建
        log_files = list(tmp_path.glob("transmitter_*.log"))
        assert len(log_files) > 0

        # 检查日志内容
        log_content = log_files[0].read_text(encoding="utf-8")
        assert "测试日志消息" in log_content

    def test_setup_logging_levels(self, tmp_path):
        """测试不同日志级别"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger = setup_logging(
                log_level=level,
                log_dir=tmp_path,
                log_to_file=False,
                log_to_console=False,
            )
            assert logger.level == getattr(logging, level)

    def test_get_logger(self):
        """测试获取logger实例"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "transmitter"

        # 测试带名称的logger
        named_logger = get_logger("test_module")
        assert named_logger.name == "transmitter.test_module"

    def test_logging_no_duplicate_handlers(self, tmp_path):
        """测试多次配置不会产生重复的handlers"""
        logger1 = setup_logging(log_dir=tmp_path, log_to_file=False)
        handler_count1 = len(logger1.handlers)

        logger2 = setup_logging(log_dir=tmp_path, log_to_file=False)
        handler_count2 = len(logger2.handlers)

        # 应该清除旧的handlers，所以数量应该相同
        assert handler_count1 == handler_count2
