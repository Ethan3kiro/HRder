"""
OCR提取模块 V4 - 全图扫描+智能匹配

不依赖固定坐标，而是扫描整个图像识别所有数字，然后根据位置智能匹配到数据项
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

logger = logging.getLogger("transmitter.ocr_v4")


try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    import warnings
    warnings.warn("opencv-python not available. Using PIL for image preprocessing.")


class OCRExtractorV4:
    """OCR数据提取器 V4 - 全图扫描+智能匹配"""
    
    # 需要提取的 COMBINER ISO TEMPERATURES 数据项
    COMBINER_ITEMS = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    # Z-Plane 模块列表
    ZPLANE_MODULES = ['A', 'B', 'C', 'D']
    
    # 每个 Z-Plane 的行数
    ZPLANE_ROWS = 8
    
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
    
    def _scan_all_numbers(self, image: Image.Image) -> List[Dict]:
        """
        扫描图像中的所有数字及其位置
        
        Args:
            image: PIL图像对象
        
        Returns:
            数字列表，每个元素包含 text, x, y, w, h, confidence, x_percent, y_percent
        """
        logger.info("扫描图像中的所有数字...")
        
        # 预处理图像以提高识别率
        image_array = np.array(image)
        
        if CV2_AVAILABLE:
            # 转换为灰度图
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # 放大图像
            scale_factor = 2.0
            width = int(gray.shape[1] * scale_factor)
            height = int(gray.shape[0] * scale_factor)
            scaled = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
            
            # 二值化
            _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            processed_image = Image.fromarray(binary)
        else:
            processed_image = image.convert('L')
            scale_factor = 2.0
            new_size = (int(processed_image.width * scale_factor), int(processed_image.height * scale_factor))
            processed_image = processed_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 使用 Tesseract 获取所有文本的位置
        data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT, lang='eng')
        
        numbers = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue
            
            conf = int(data['conf'][i])
            if conf < 30:  # 跳过低置信度的识别
                continue
            
            # 调整坐标（因为图像被放大了）
            x = int(data['left'][i] / scale_factor)
            y = int(data['top'][i] / scale_factor)
            w = int(data['width'][i] / scale_factor)
            h = int(data['height'][i] / scale_factor)
            
            # 尝试解析为数字
            try:
                # 清理文本
                cleaned = text.replace(',', '.').replace('O', '0').replace('o', '0')
                value = float(cleaned)
                
                numbers.append({
                    'text': text,
                    'value': value,
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'conf': conf,
                    'x_percent': x / image.width,
                    'y_percent': y / image.height,
                    'x_center': (x + w / 2) / image.width,
                    'y_center': (y + h / 2) / image.height
                })
                
                logger.debug(f"识别到数字: {value} at ({x}, {y}), conf={conf}")
            
            except ValueError:
                # 不是数字，跳过
                pass
        
        logger.info(f"共识别到 {len(numbers)} 个数字")
        return numbers
    
    def _find_combiner_numbers(self, numbers: List[Dict], image_width: int, image_height: int) -> List[Dict]:
        """
        从识别的数字中找出 COMBINER 数据
        
        策略：COMBINER 数据通常在图像上半部分，横向排列
        """
        # COMBINER 区域大致在 y < 0.4 的位置
        combiner_candidates = [n for n in numbers if n['y_percent'] < 0.4]
        
        if not combiner_candidates:
            logger.warning("未找到 COMBINER 候选数字")
            return []
        
        # 按 Y 坐标分组，找到同一行的数字
        y_tolerance = 30  # Y 坐标容差（像素）
        rows = []
        
        for num in combiner_candidates:
            found_row = False
            for row in rows:
                if abs(num['y'] - row[0]['y']) < y_tolerance:
                    row.append(num)
                    found_row = True
                    break
            if not found_row:
                rows.append([num])
        
        # 找到数字最多的行（应该是 COMBINER 行）
        if not rows:
            return []
        
        combiner_row = max(rows, key=len)
        combiner_row.sort(key=lambda x: x['x'])  # 按 X 坐标排序
        
        logger.info(f"找到 COMBINER 行，包含 {len(combiner_row)} 个数字")
        
        # 匹配到数据项
        items = []
        for i, num in enumerate(combiner_row):
            if i < len(self.COMBINER_ITEMS):
                items.append({
                    'item_name': self.COMBINER_ITEMS[i],
                    'value': num['value'],
                    'unit': '°C'
                })
        
        return items
    
    def _find_zplane_numbers(self, numbers: List[Dict], module: str, image_width: int, image_height: int) -> List[Dict]:
        """
        从识别的数字中找出 Z-Plane 数据
        
        策略：Z-Plane 数据在图像下半部分，分为4列（A, B, C, D）
        """
        # Z-Plane 区域大致在 y > 0.4 的位置
        zplane_candidates = [n for n in numbers if n['y_percent'] > 0.4]
        
        if not zplane_candidates:
            logger.warning(f"未找到 Z-Plane {module} 候选数字")
            return []
        
        # 根据模块确定 X 范围
        module_index = self.ZPLANE_MODULES.index(module)
        x_start = module_index * 0.25
        x_end = (module_index + 1) * 0.25
        
        # 筛选该模块的数字
        module_numbers = [n for n in zplane_candidates if x_start <= n['x_center'] < x_end]
        
        if not module_numbers:
            logger.warning(f"未找到 Z-Plane {module} 的数字")
            return []
        
        # 按 Y 坐标排序
        module_numbers.sort(key=lambda x: x['y'])
        
        logger.info(f"找到 Z-Plane {module} 的 {len(module_numbers)} 个数字")
        
        # 按行分组（每行应该有2个数字：Current 和 ISO Temp）
        rows = []
        y_tolerance = 20
        
        for num in module_numbers:
            found_row = False
            for row in rows:
                if abs(num['y'] - row[0]['y']) < y_tolerance:
                    row.append(num)
                    found_row = True
                    break
            if not found_row:
                rows.append([num])
        
        # 为每行的数字排序（按 X 坐标）
        for row in rows:
            row.sort(key=lambda x: x['x'])
        
        # 匹配到数据项
        items = []
        for row_num, row in enumerate(rows, 1):
            if row_num > self.ZPLANE_ROWS:
                break
            
            # 第一个数字是 Current，第二个是 ISO Temp
            if len(row) >= 1:
                items.append({
                    'item_name': f'Z-Plane {module}-Current-{row_num}',
                    'value': row[0]['value'],
                    'unit': 'A'
                })
            
            if len(row) >= 2:
                items.append({
                    'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                    'value': row[1]['value'],
                    'unit': '°C'
                })
        
        return items
    
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
            
            # 扫描所有数字
            all_numbers = self._scan_all_numbers(image)
            
            if not all_numbers:
                logger.warning("未识别到任何数字")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            items = []
            
            # 提取 COMBINER 数据
            logger.info("匹配 COMBINER ISO TEMPERATURES 数据...")
            combiner_data = self._find_combiner_numbers(all_numbers, image.width, image.height)
            items.extend(combiner_data)
            
            # 提取 Z-Plane 数据
            for module in self.ZPLANE_MODULES:
                logger.info(f"匹配 Z-Plane {module} 数据...")
                zplane_data = self._find_zplane_numbers(all_numbers, module, image.width, image.height)
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


# 为了向后兼容，创建一个别名
OCRExtractor = OCRExtractorV4
