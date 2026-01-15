"""
项目配置模块

定义全局配置参数和常量
"""
from pathlib import Path
from typing import Optional
import platform


class Config:
    """项目配置类"""

    # 版本信息
    VERSION = "0.1.0"

    # 数据库配置
    DEFAULT_DB_NAME = "transmitter_data.db"

    # 日志配置
    DEFAULT_LOG_DIR_NAME = "transmitter_logs"
    DEFAULT_LOG_LEVEL = "INFO"

    # OCR配置
    TESSERACT_PATHS = {
        "Darwin": "/usr/local/bin/tesseract",  # Mac
        "Windows": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        "Linux": "/usr/bin/tesseract",
    }

    # 支持的图像格式
    SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]

    # 月份格式
    MONTH_FORMAT = "%Y-%m"
    MONTH_REGEX = r"^\d{4}-\d{2}$"

    # 可视化配置
    FIGURE_SIZE = (12, 6)
    DPI = 100

    @staticmethod
    def get_default_db_path() -> Path:
        """
        获取默认数据库路径

        Returns:
            Mac: ~/Documents/transmitter_data.db
            Windows: C:/Users/用户名/Documents/transmitter_data.db
        """
        home = Path.home()
        documents = home / "Documents"
        documents.mkdir(exist_ok=True)
        return documents / Config.DEFAULT_DB_NAME

    @staticmethod
    def get_default_log_path() -> Path:
        """
        获取默认日志目录路径

        Returns:
            Mac: ~/Documents/transmitter_logs
            Windows: C:/Users/用户名/Documents/transmitter_logs
        """
        home = Path.home()
        documents = home / "Documents"
        log_dir = documents / Config.DEFAULT_LOG_DIR_NAME
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @staticmethod
    def get_tesseract_path() -> Optional[str]:
        """
        获取Tesseract可执行文件路径

        Returns:
            当前操作系统的默认Tesseract路径，如果不存在则返回None
        """
        system = platform.system()
        default_path = Config.TESSERACT_PATHS.get(system)

        if default_path and Path(default_path).exists():
            return default_path

        return None

    @staticmethod
    def is_supported_image(file_path: Path) -> bool:
        """
        检查文件是否为支持的图像格式

        Args:
            file_path: 文件路径

        Returns:
            是否为支持的图像格式
        """
        return file_path.suffix.lower() in Config.SUPPORTED_IMAGE_FORMATS


# 全局配置实例
config = Config()
