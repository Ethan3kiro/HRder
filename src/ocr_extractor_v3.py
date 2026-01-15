"""
OCR提取模块 V3 - 基于坐标的精确提取

采用坐标定位方法，针对固定格式的发射机监控界面
"""
import re
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

import numpy as np
import pandas as pd
from PIL import Image

# Handle pytesseract import
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

logger = logging.getLogger("transmitter.ocr_v3")


try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    import warnings
    warnings.warn("opencv-python not available. Using PIL for image preprocessing.")


class OCRExtractorV3:
    """OCR数据提取器 V3 - 基于坐标的精确提取"""
    
    # 需要提取的 COMBINER ISO TEMPERATURES 数据项
    COMBINER_ITEMS = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    # Z-Plane 模块列表
    ZPLANE_MODULES = ['A', 'B', 'C', 'D']
    
    # 每个 Z-Plane 的行数
    ZPLANE_ROWS = 8
    
    # 坐标配置（需要根据实际截图调整）
    # 这些是相对坐标，会根据图像大小自动缩放
    COMBINER_REGION = {
        'x': 0.25,  # 左边界（图像宽度的百分比）
        'y': 0.25,  # 上边界（图像高度的百分比）
        'width': 0.50,  # 区域宽度
        'height': 0.08  # 区域高度
    }
    
    ZPLANE_REGIONS = {
        'A': {'x': 0.02, 'y': 0.52, 'width': 0.23, 'height': 0.35},
        'B': {'x': 0.27, 'y': 0.52, 'width': 0.23, 'height': 0.35},
        'C': {'x': 0.52, 'y': 0.52, 'width': 0.23, 'height': 0.35},
        'D': {'x': 0.77, 'y': 0.52, 'width': 0.23, 'height': 0.35}
    }
    
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
                "pytesseract模块不可用。请确保安装了兼容的pytesseract版本。"
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
            if not self._is_tesseract_installed():
                raise OCRError(
                    "Tesseract-OCR未安装或无法找到。\n"
                    "请访问以下链接安装Tesseract:\n"
                    "Mac: brew install tesseract\n"
                    "Windows: https://github.com/UB-Mannheim/tesseract/wiki"
                )
            logger.info("使用系统PATH中的Tesseract")
    
    def _detect_tesseract(self) -> Optional[str]:
        """自动检测Tesseract安装路径"""
        default_path = Config.get_tesseract_path()
        if default_path:
            logger.debug(f"找到Tesseract默认路径: {default_path}")
            return default_path
        
        tesseract_cmd = shutil.which("tesseract")
        if tesseract_cmd:
            logger.debug(f"在系统PATH中找到Tesseract: {tesseract_cmd}")
            return tesseract_cmd
        
        logger.warning("未找到Tesseract安装路径")
        return None
    
    def _is_tesseract_installed(self) -> bool:
        """检查Tesseract是否已安装"""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"检测到Tesseract版本: {version}")
            return True
        except Exception as e:
            logger.error(f"Tesseract检测失败: {e}")
            return False
    
    def _preprocess_cell(self, cell_image: np.ndarray) -> np.ndarray:
        """
        预处理单个单元格图像
        
        Args:
            cell_image: 单元格图像数组
        
        Returns:
            预处理后的图像数组
        """
        if CV2_AVAILABLE:
            # 转换为灰度图
            if len(cell_image.shape) == 3:
                gray = cv2.cvtColor(cell_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = cell_image
            
            # 放大图像
            scale_factor = 3.0
            width = int(gray.shape[1] * scale_factor)
            height = int(gray.shape[0] * scale_factor)
            gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
        else:
            # 使用 PIL 预处理
            from PIL import ImageEnhance
            
            if len(cell_image.shape) == 3:
                pil_image = Image.fromarray(cell_image).convert('L')
            else:
                pil_image = Image.fromarray(cell_image)
            
            # 放大图像
            scale_factor = 3.0
            new_size = (int(pil_image.width * scale_factor), int(pil_image.height * scale_factor))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 增强对比度
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(2.5)
            
            # 二值化
            threshold = 128
            pil_image = pil_image.point(lambda x: 255 if x > threshold else 0, mode='1')
            
            return np.array(pil_image)
    
    def _extract_number_from_cell(self, cell_image: np.ndarray) -> Optional[float]:
        """
        从单元格图像中提取数字
        
        Args:
            cell_image: 单元格图像数组
        
        Returns:
            提取的数字，如果无法识别则返回None
        """
        # 预处理单元格
        processed = self._preprocess_cell(cell_image)
        
        # 使用数字白名单配置
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-'
        
        try:
            text = pytesseract.image_to_string(processed, config=custom_config).strip()
            
            # 清理文本
            text = text.replace(' ', '').replace('\n', '')
            
            # 尝试转换为浮点数
            if text and text != '-':
                # 处理负数
                value = float(text)
                return value
        except Exception as e:
            logger.debug(f"无法从单元格提取数字: {e}")
        
        return None
    
    def _crop_region(self, image: np.ndarray, region: Dict) -> np.ndarray:
        """
        根据相对坐标裁剪图像区域
        
        Args:
            image: 原始图像数组
            region: 区域配置字典 {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.4}
        
        Returns:
            裁剪后的图像数组
        """
        height, width = image.shape[:2]
        
        x1 = int(width * region['x'])
        y1 = int(height * region['y'])
        x2 = int(width * (region['x'] + region['width']))
        y2 = int(height * (region['y'] + region['height']))
        
        return image[y1:y2, x1:x2]
    
    def extract_from_image(self, image_path: Path) -> pd.DataFrame:
        """
        从图像中提取指定的数据项
        
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
            image_array = np.array(image)
            
            items = []
            
            # 提取 COMBINER 数据
            logger.info("提取 COMBINER ISO TEMPERATURES 数据...")
            combiner_data = self._extract_combiner_by_coordinates(image_array)
            items.extend(combiner_data)
            
            # 提取 Z-Plane 数据
            for module in self.ZPLANE_MODULES:
                logger.info(f"提取 Z-Plane {module} 数据...")
                zplane_data = self._extract_zplane_by_coordinates(image_array, module)
                items.extend(zplane_data)
            
            # 创建DataFrame
            if not items:
                logger.warning("未提取到任何数据项")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            df = pd.DataFrame(items)
            logger.info(f"成功提取 {len(df)} 条数据")
            
            return df
        
        except Exception as e:
            logger.error(f"OCR提取失败: {e}")
            raise OCRError(f"OCR识别失败: {str(e)}")
    
    def _extract_combiner_by_coordinates(self, image: np.ndarray) -> List[Dict]:
        """
        基于坐标提取 COMBINER 数据
        
        Args:
            image: 图像数组
        
        Returns:
            数据项列表
        """
        items = []
        
        # 裁剪 COMBINER 区域
        combiner_region = self._crop_region(image, self.COMBINER_REGION)
        
        # 将区域分成7列（对应7个数据项）
        height, width = combiner_region.shape[:2]
        col_width = width // 7
        
        for i, item_name in enumerate(self.COMBINER_ITEMS):
            # 裁剪单个单元格
            x1 = i * col_width
            x2 = (i + 1) * col_width
            cell = combiner_region[:, x1:x2]
            
            # 提取数字
            value = self._extract_number_from_cell(cell)
            
            if value is not None:
                items.append({
                    'item_name': item_name,
                    'value': value,
                    'unit': '°C'
                })
                logger.debug(f"提取 COMBINER {item_name}: {value}°C")
            else:
                logger.warning(f"无法提取 COMBINER {item_name}")
        
        return items
    
    def _extract_zplane_by_coordinates(self, image: np.ndarray, module: str) -> List[Dict]:
        """
        基于坐标提取 Z-Plane 数据
        
        Args:
            image: 图像数组
            module: 模块名称 (A, B, C, D)
        
        Returns:
            数据项列表
        """
        items = []
        
        # 裁剪 Z-Plane 区域
        region_config = self.ZPLANE_REGIONS[module]
        zplane_region = self._crop_region(image, region_config)
        
        # 将区域分成行和列
        height, width = zplane_region.shape[:2]
        
        # 跳过标题行，从数据行开始
        header_height = int(height * 0.15)  # 标题占15%
        data_region = zplane_region[header_height:, :]
        
        data_height = data_region.shape[0]
        row_height = data_height // self.ZPLANE_ROWS
        
        # 列宽度（Current, Temp, Gate, ISO Temp）
        col_width = width // 4
        current_col = 0  # Current 列索引
        iso_temp_col = 3  # ISO Temp 列索引
        
        for row_num in range(1, self.ZPLANE_ROWS + 1):
            # 计算行的位置
            y1 = (row_num - 1) * row_height
            y2 = row_num * row_height
            
            # 提取 Current 单元格
            current_x1 = current_col * col_width
            current_x2 = (current_col + 1) * col_width
            current_cell = data_region[y1:y2, current_x1:current_x2]
            current_value = self._extract_number_from_cell(current_cell)
            
            # 提取 ISO Temp 单元格
            iso_x1 = iso_temp_col * col_width
            iso_x2 = (iso_temp_col + 1) * col_width
            iso_cell = data_region[y1:y2, iso_x1:iso_x2]
            iso_value = self._extract_number_from_cell(iso_cell)
            
            # 添加数据
            if current_value is not None:
                items.append({
                    'item_name': f'Z-Plane {module}-Current-{row_num}',
                    'value': current_value,
                    'unit': 'A'
                })
                logger.debug(f"Z-Plane {module} Row {row_num} Current: {current_value}A")
            else:
                logger.warning(f"无法提取 Z-Plane {module} Row {row_num} Current")
            
            if iso_value is not None:
                items.append({
                    'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                    'value': iso_value,
                    'unit': '°C'
                })
                logger.debug(f"Z-Plane {module} Row {row_num} ISO Temp: {iso_value}°C")
            else:
                logger.warning(f"无法提取 Z-Plane {module} Row {row_num} ISO Temp")
        
        return items


# 为了向后兼容，创建一个别名
OCRExtractor = OCRExtractorV3
