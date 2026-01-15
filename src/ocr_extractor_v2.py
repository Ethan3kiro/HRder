"""
OCR提取模块 V2 - 针对发射机监控界面的专用提取器

专门提取以下数据：
1. COMBINER ISO TEMPERATURES 模块：AZ, BZ, CZ, DZ, AB, CD, ABCD
2. Z-Plane A/B/C/D 模块：Current 列和 ISO Temp 列（每个 Z-Plane 8 行）
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

logger = logging.getLogger("transmitter.ocr_v2")


try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    import warnings
    warnings.warn("opencv-python not available. Using PIL for image preprocessing.")


class OCRExtractorV2:
    """OCR数据提取器 V2 - 专用于发射机监控界面"""
    
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
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理以提高OCR准确率
        
        Args:
            image: 原始图像数组
        
        Returns:
            预处理后的图像数组
        """
        if CV2_AVAILABLE:
            return self._preprocess_with_cv2(image)
        else:
            return self._preprocess_with_pil(image)
    
    def _preprocess_with_cv2(self, image: np.ndarray) -> np.ndarray:
        """
        使用OpenCV进行图像预处理（更高质量）
        
        Args:
            image: 原始图像数组
        
        Returns:
            预处理后的图像数组
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 增加图像尺寸以提高OCR准确率
        scale_factor = 2.0
        width = int(gray.shape[1] * scale_factor)
        height = int(gray.shape[0] * scale_factor)
        gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
        
        # 降噪
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # 自适应阈值二值化
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 形态学操作去除噪点
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        logger.debug("使用OpenCV完成图像预处理")
        return cleaned
    
    def _preprocess_with_pil(self, image: np.ndarray) -> np.ndarray:
        """
        使用PIL进行图像预处理（备用方案）
        
        Args:
            image: 原始图像数组
        
        Returns:
            预处理后的图像数组
        """
        from PIL import ImageEnhance, ImageFilter
        
        # 转换为PIL Image
        if len(image.shape) == 3:
            pil_image = Image.fromarray(image).convert('L')
        else:
            pil_image = Image.fromarray(image)
        
        # 增加图像尺寸
        scale_factor = 2.0
        new_size = (int(pil_image.width * scale_factor), int(pil_image.height * scale_factor))
        pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(2.0)
        
        # 增强锐度
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        # 降噪
        pil_image = pil_image.filter(ImageFilter.MedianFilter(size=3))
        
        # 二值化
        threshold = 128
        pil_image = pil_image.point(lambda x: 255 if x > threshold else 0, mode='1')
        
        logger.debug("使用PIL完成图像预处理")
        return np.array(pil_image)
    
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
            
            # 预处理图像以提高OCR准确率
            processed_image = self._preprocess_image(np.array(image))
            
            # 使用优化的OCR配置提取文本
            # PSM 6: 假设是单个统一的文本块
            # --oem 3: 使用默认OCR引擎模式
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_image, lang='eng', config=custom_config)
            
            logger.debug(f"OCR提取的原始文本:\n{text}")
            
            # 解析数据
            extracted_data = self._parse_transmitter_data(text)
            
            logger.info(f"成功提取 {len(extracted_data)} 条数据")
            
            return extracted_data
        
        except Exception as e:
            logger.error(f"OCR提取失败: {e}")
            raise OCRError(f"OCR识别失败: {str(e)}")
    
    def _parse_transmitter_data(self, text: str) -> pd.DataFrame:
        """
        解析发射机监控文本数据
        
        Args:
            text: OCR提取的完整文本
        
        Returns:
            包含item_name、value、unit的DataFrame
        """
        items = []
        
        # 1. 提取 COMBINER ISO TEMPERATURES 数据
        combiner_data = self._extract_combiner_temperatures(text)
        items.extend(combiner_data)
        
        # 2. 提取 Z-Plane 数据
        for module in self.ZPLANE_MODULES:
            zplane_data = self._extract_zplane_data(text, module)
            items.extend(zplane_data)
        
        # 创建DataFrame
        if not items:
            logger.warning("未提取到任何数据项")
            return pd.DataFrame(columns=["item_name", "value", "unit"])
        
        df = pd.DataFrame(items)
        logger.info(f"提取的数据项: {df['item_name'].tolist()}")
        
        return df
    
    def _extract_combiner_temperatures(self, text: str) -> List[Dict]:
        """
        提取 COMBINER ISO TEMPERATURES 数据
        
        提取项目：AZ, BZ, CZ, DZ, AB, CD, ABCD
        
        Args:
            text: OCR文本
        
        Returns:
            数据项列表
        """
        items = []
        
        # 查找 COMBINER ISO TEMPERATURES 部分
        combiner_pattern = r'COMBINER\s+ISO\s+TEMPERATURES?\s*\n(.*?)(?=Z-Plane|$)'
        match = re.search(combiner_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            logger.warning("未找到 COMBINER ISO TEMPERATURES 部分")
            return items
        
        combiner_text = match.group(1)
        logger.debug(f"COMBINER 部分文本:\n{combiner_text}")
        
        # 提取标题行和数值行
        # 格式通常是：
        # AZ  BZ  CZ  DZ  AB  CD  ABCD
        # 47  44  44  42  29  30  29
        
        lines = combiner_text.strip().split('\n')
        
        # 查找包含标题的行
        header_line = None
        values_line = None
        
        for i, line in enumerate(lines):
            # 检查是否包含所有标题
            if all(item in line.upper() for item in ['AZ', 'BZ', 'CZ', 'DZ']):
                header_line = line
                # 下一行应该是数值
                if i + 1 < len(lines):
                    values_line = lines[i + 1]
                break
        
        if header_line and values_line:
            # 提取标题
            headers = re.findall(r'[A-Z]+', header_line.upper())
            # 提取数值
            values = re.findall(r'\d+\.?\d*', values_line)
            
            logger.debug(f"COMBINER 标题: {headers}")
            logger.debug(f"COMBINER 数值: {values}")
            
            # 匹配标题和数值
            for i, header in enumerate(headers):
                if header in self.COMBINER_ITEMS and i < len(values):
                    value = float(values[i])
                    items.append({
                        'item_name': header,  # 直接使用 AZ, BZ, CZ 等
                        'value': value,
                        'unit': '°C'
                    })
                    logger.debug(f"提取 COMBINER {header}: {value}°C")
        else:
            logger.warning("未能解析 COMBINER 数据的表格结构")
            
            # 备用方案：逐个查找
            for item_name in self.COMBINER_ITEMS:
                pattern = rf'{item_name}\s*:?\s*(\d+\.?\d*)'
                match = re.search(pattern, combiner_text, re.IGNORECASE)
                
                if match:
                    value = float(match.group(1))
                    items.append({
                        'item_name': item_name,  # 直接使用 AZ, BZ, CZ 等
                        'value': value,
                        'unit': '°C'
                    })
                    logger.debug(f"提取 COMBINER {item_name}: {value}°C")
        
        return items
    
    def _extract_zplane_data(self, text: str, module: str) -> List[Dict]:
        """
        提取 Z-Plane 模块的 Current 和 ISO Temp 数据
        
        Args:
            text: OCR文本
            module: 模块名称 (A, B, C, D)
        
        Returns:
            数据项列表
        """
        items = []
        
        # 查找 Z-Plane 模块部分
        # 例如：Z-Plane A ... Z-Plane B
        pattern = rf'Z-Plane\s+{module}\s+(.*?)(?=Z-Plane\s+[A-D]|FAULTS|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            logger.warning(f"未找到 Z-Plane {module} 部分")
            return items
        
        zplane_text = match.group(1)
        logger.debug(f"Z-Plane {module} 部分文本:\n{zplane_text}")
        
        # 提取表格数据
        # 查找 Current 和 ISO Temp 列的数据
        # 表格格式：行号 | Current | Temp | Gate | ISO Temp
        
        # 分行处理
        lines = zplane_text.split('\n')
        
        row_num = 1
        for line in lines:
            if not line.strip():
                continue
            
            # 查找包含数值的行
            # 匹配模式：数字开头，后面跟着多个数值
            numbers = re.findall(r'\d+\.?\d*', line)
            
            if len(numbers) >= 4:  # 至少需要4个数值（行号、Current、Temp、ISO Temp）
                try:
                    # 假设格式：行号 Current Temp Gate ISO_Temp
                    # 我们需要 Current (索引1) 和 ISO_Temp (索引4)
                    if len(numbers) >= 5:
                        current = float(numbers[1])
                        iso_temp = float(numbers[4])
                        
                        # 添加 Current 数据 - 格式：Z-Plane A-Current-1
                        items.append({
                            'item_name': f'Z-Plane {module}-Current-{row_num}',
                            'value': current,
                            'unit': 'A'
                        })
                        
                        # 添加 ISO Temp 数据 - 格式：Z-Plane A-ISO Temp-1
                        items.append({
                            'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                            'value': iso_temp,
                            'unit': '°C'
                        })
                        
                        logger.debug(f"Z-Plane {module} Row {row_num}: Current={current}A, ISO Temp={iso_temp}°C")
                        
                        row_num += 1
                        
                        if row_num > self.ZPLANE_ROWS:
                            break
                
                except (ValueError, IndexError) as e:
                    logger.debug(f"跳过无效行: {line} - {e}")
                    continue
        
        if row_num <= self.ZPLANE_ROWS:
            logger.warning(f"Z-Plane {module} 只提取到 {row_num-1} 行数据，预期 {self.ZPLANE_ROWS} 行")
        
        return items


# 为了向后兼容，创建一个别名
OCRExtractor = OCRExtractorV2
