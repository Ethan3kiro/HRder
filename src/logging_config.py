"""
日志配置模块

提供统一的日志配置和管理功能，支持文件日志和控制台日志。
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_default_log_path() -> Path:
    """
    获取默认日志目录路径

    Returns:
        Mac: ~/Documents/transmitter_logs
        Windows: C:/Users/用户名/Documents/transmitter_logs
    """
    home = Path.home()
    documents = home / "Documents"
    log_dir = documents / "transmitter_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    配置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录路径（可选，使用默认路径）
        log_to_file: 是否记录到文件
        log_to_console: 是否输出到控制台

    Returns:
        配置好的Logger实例

    Example:
        >>> logger = setup_logging(log_level="DEBUG")
        >>> logger.info("系统启动")
    """
    # 获取日志目录
    if log_dir is None:
        log_dir = get_default_log_path()
    else:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

    # 生成日志文件名（按日期）
    log_file = log_dir / f"transmitter_{datetime.now():%Y%m%d}.log"

    # 创建logger
    logger = logging.getLogger("transmitter")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 清除已有的handlers（避免重复配置）
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件handler
    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 控制台handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 防止日志传播到root logger
    logger.propagate = False

    logger.info(f"日志系统初始化完成 - 日志级别: {log_level}")
    if log_to_file:
        logger.info(f"日志文件: {log_file}")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称（可选，默认使用'transmitter'）

    Returns:
        Logger实例

    Example:
        >>> logger = get_logger('ocr')
        >>> logger.debug("开始OCR识别")
    """
    if name:
        return logging.getLogger(f"transmitter.{name}")
    return logging.getLogger("transmitter")


# 模块级别的logger实例
logger = get_logger()
