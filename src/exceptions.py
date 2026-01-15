"""
自定义异常类

定义系统中使用的所有自定义异常类型
"""
import logging
import sqlite3
from functools import wraps
from typing import Callable, Any


class TransmitterError(Exception):
    """基础异常类"""

    pass


class OCRError(TransmitterError):
    """OCR相关错误"""

    pass


class DatabaseError(TransmitterError):
    """数据库相关错误"""

    pass


class DataValidationError(TransmitterError):
    """数据验证错误"""

    pass


class FileError(TransmitterError):
    """文件操作错误"""

    pass


def handle_errors(func: Callable) -> Callable:
    """
    统一错误处理装饰器

    捕获常见异常并转换为自定义异常类型，同时记录错误日志。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数

    Example:
        >>> @handle_errors
        ... def process_file(path):
        ...     with open(path) as f:
        ...         return f.read()
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger("transmitter")
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            raise FileError(f"文件不存在: {e.filename}")
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            raise FileError(f"没有权限访问文件: {e.filename}")
        except sqlite3.Error as e:
            logger.error(f"数据库错误: {e}")
            raise DatabaseError(f"数据库操作失败: {str(e)}")
        except (ValueError, TypeError) as e:
            logger.error(f"数据验证错误: {e}")
            raise DataValidationError(f"数据格式错误: {str(e)}")
        except TransmitterError:
            # 已经是自定义异常，直接重新抛出
            raise
        except Exception as e:
            logger.exception(f"未预期的错误: {e}")
            raise TransmitterError(f"操作失败: {str(e)}")

    return wrapper
