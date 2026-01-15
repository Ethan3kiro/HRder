"""
OCR提取模块

从发射机监控系统的截图中提取结构化数据
"""
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

import numpy as np
import pandas as pd
from PIL import Image

# Handle pytesseract import with Python 3.14 compatibility
try:
    import pytesseract

    PYTESSERACT_AVAILABLE = True
except ImportError as e:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None
    import warnings

    warnings.warn(f"pytesseract import failed: {e}. OCR functionality will be limited.")

from src.exceptions import OCRError, FileError
from src.config import Config


logger = logging.getLogger("transmitter.ocr")


class OCRExtractor:
    """OCR数据提取器"""

    def __init__(self, tesseract_path: Optional[str] = None):
        """
        初始化OCR提取器

        Args:
            tesseract_path: Tesseract可执行文件路径（可选，自动检测）

        Raises:
            OCRError: Tesseract未安装或路径错误
        """
        if not PYTESSERACT_AVAILABLE:
            raise OCRError(
                "pytesseract模块不可用。这可能是由于Python版本兼容性问题。\n" "请确保安装了兼容的pytesseract版本。"
            )

        # 检测Tesseract安装
        if tesseract_path:
            self.tesseract_path = tesseract_path
        else:
            self.tesseract_path = self._detect_tesseract()

        # 设置pytesseract的tesseract路径
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            logger.info(f"Tesseract路径设置为: {self.tesseract_path}")
        else:
            # 尝试使用系统PATH中的tesseract
            if not self._is_tesseract_installed():
                raise OCRError(
                    "Tesseract-OCR未安装或无法找到。\n"
                    "请访问以下链接安装Tesseract:\n"
                    "Mac: brew install tesseract\n"
                    "Windows: https://github.com/UB-Mannheim/tesseract/wiki"
                )
            logger.info("使用系统PATH中的Tesseract")

    def _detect_tesseract(self) -> Optional[str]:
        """
        自动检测Tesseract安装路径

        Returns:
            Tesseract路径，如果未找到则返回None
        """
        # 首先尝试使用Config中定义的默认路径
        default_path = Config.get_tesseract_path()
        if default_path:
            logger.debug(f"找到Tesseract默认路径: {default_path}")
            return default_path

        # 尝试在系统PATH中查找
        tesseract_cmd = shutil.which("tesseract")
        if tesseract_cmd:
            logger.debug(f"在系统PATH中找到Tesseract: {tesseract_cmd}")
            return tesseract_cmd

        logger.warning("未找到Tesseract安装路径")
        return None

    def _is_tesseract_installed(self) -> bool:
        """
        检查Tesseract是否已安装

        Returns:
            是否已安装
        """
        try:
            # 尝试获取Tesseract版本
            version = pytesseract.get_tesseract_version()
            logger.info(f"检测到Tesseract版本: {version}")
            return True
        except Exception as e:
            logger.error(f"Tesseract检测失败: {e}")
            return False

    def extract_from_image(self, image_path: Path) -> pd.DataFrame:
        """
        从图像中提取表格数据

        Args:
            image_path: 图像文件路径

        Returns:
            包含item_name、value、unit三列的DataFrame

        Raises:
            FileNotFoundError: 图像文件不存在
            OCRError: OCR识别失败
        """
        # 验证文件存在
        if not image_path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        # 验证文件格式
        if not Config.is_supported_image(image_path):
            raise OCRError(
                f"不支持的图像格式: {image_path.suffix}\n"
                f"支持的格式: {', '.join(Config.SUPPORTED_IMAGE_FORMATS)}"
            )

        logger.info(f"开始提取图像: {image_path}")

        try:
            # 加载图像
            image = Image.open(image_path)

            # 预处理图像
            processed_image = self._preprocess_image(np.array(image))

            # 使用pytesseract提取文本
            # 使用image_to_data获取详细信息
            data = pytesseract.image_to_data(
                processed_image, output_type=pytesseract.Output.DICT, lang="eng"
            )

            # 解析表格结构并提取数据
            extracted_data = self._parse_table_data(data)

            logger.info(f"成功提取 {len(extracted_data)} 条数据")

            return extracted_data

        except Exception as e:
            logger.error(f"OCR提取失败: {e}")
            raise OCRError(f"OCR识别失败: {str(e)}")

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理（二值化、降噪）

        Args:
            image: 原始图像数组

        Returns:
            预处理后的图像数组
        """
        # 转换为PIL Image以便处理
        if len(image.shape) == 3:
            # 彩色图像，转换为灰度
            pil_image = Image.fromarray(image).convert("L")
        else:
            # 已经是灰度图像
            pil_image = Image.fromarray(image)

        # 转回numpy数组
        gray = np.array(pil_image)

        # 使用PIL的自适应阈值（通过对比度增强实现）
        # 简单的二值化处理
        from PIL import ImageEnhance

        pil_image = Image.fromarray(gray)

        # 增强对比度
        enhancer = ImageEnhance.Contrast(pil_image)
        enhanced = enhancer.enhance(2.0)

        return np.array(enhanced)

    def _parse_table_data(self, ocr_data: dict) -> pd.DataFrame:
        """
        解析OCR数据并提取表格内容

        Args:
            ocr_data: pytesseract返回的数据字典

        Returns:
            包含item_name、value、unit的DataFrame
        """
        items = []

        # 提取所有文本
        texts = ocr_data["text"]
        confidences = ocr_data["conf"]

        # 简单的解析策略：查找包含数值的文本
        current_item = None

        for i, text in enumerate(texts):
            text = text.strip()
            if not text or confidences[i] < 30:  # 过滤低置信度文本
                continue

            # 尝试解析为数值+单位
            try:
                value, unit = self._parse_value_unit(text)
                # 如果成功解析，且有前面的项目名称
                if current_item:
                    items.append(
                        {"item_name": current_item, "value": value, "unit": unit}
                    )
                    current_item = None
            except (ValueError, OCRError):
                # 不是数值，可能是项目名称
                if text and len(text) > 1:
                    current_item = text

        # 创建DataFrame
        if not items:
            logger.warning("未提取到任何数据项")
            return pd.DataFrame(columns=["item_name", "value", "unit"])

        return pd.DataFrame(items)

    def _parse_value_unit(self, text: str) -> Tuple[float, str]:
        """
        解析带单位的数值字符串

        Args:
            text: 原始文本（如"12.5V"、"407%"）

        Returns:
            (数值, 单位)元组

        Raises:
            ValueError: 无法解析为数值

        Examples:
            "12.5V" -> (12.5, "V")
            "407%" -> (407.0, "%")
            "28" -> (28.0, "")
            "28°C" -> (28.0, "°C")
            "6.1e-05V" -> (6.1e-05, "V")
        """
        text = text.strip()

        # 支持的单位模式
        # 匹配：数字（可能包含小数点、负号和科学计数法） + 可选的单位
        pattern = r"^(-?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*([A-Za-z%°]+)?$"

        match = re.match(pattern, text)
        if match:
            value_str = match.group(1)
            unit = match.group(2) if match.group(2) else ""

            try:
                value = float(value_str)
                return value, unit
            except ValueError:
                raise ValueError(f"无法将 '{value_str}' 转换为数值")

        raise ValueError(f"无法解析文本: '{text}'")
