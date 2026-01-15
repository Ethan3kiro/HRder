"""
OCR提取模块 V10 - 图像预处理增强

主要改进：
1. 添加 CLAHE 对比度增强
2. 添加锐化处理
3. 添加去噪算法
4. 添加自适应二值化
5. 保留 V8 的智能过滤校准因子功能
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
import cv2

# Handle EasyOCR import
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError as e:
    EASYOCR_AVAILABLE = False
    easyocr = None
    import warnings
    warnings.warn(f"easyocr import failed: {e}. OCR functionality will be limited.")

from src.exceptions import OCRError, FileError
from src.config import Config

logger = logging.getLogger("transmitter.ocr_v10")


class OCRExtractorV10:
    """OCR数据提取器 V10 - 图像预处理增强版"""
    
    # 需要提取的 COMBINER ISO TEMPERATURES 数据项
    COMBINER_ITEMS = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    # Z-Plane 模块列表
    ZPLANE_MODULES = ['A', 'B', 'C', 'D']
    
    # 每个 Z-Plane 的行数
    ZPLANE_ROWS = 8
    
    def __init__(self, preprocessing_level: str = 'medium'):
        """
        初始化OCR提取器
        
        Args:
            preprocessing_level: 预处理级别 ('light', 'medium', 'heavy')
        
        Raises:
            OCRError: EasyOCR未安装或初始化失败
        """
        if not EASYOCR_AVAILABLE:
            raise OCRError(
                "easyocr模块不可用。\n"
                "请安装 EasyOCR:\n"
                "pip3 install easyocr -i https://mirrors.aliyun.com/pypi/simple/"
            )
        
        self.preprocessing_level = preprocessing_level
        
        try:
            # 初始化 EasyOCR Reader（使用英文模型，CPU模式）
            logger.info(f"正在初始化 EasyOCR V10 (预处理级别: {preprocessing_level})...")
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("✓ EasyOCR V10 初始化成功")
        except Exception as e:
            raise OCRError(f"EasyOCR 初始化失败: {e}")
    
    def _preprocess_image(self, image_path: Path) -> np.ndarray:
        """
        图像预处理增强
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            预处理后的图像数组
        """
        logger.info(f"开始图像预处理 (级别: {self.preprocessing_level})...")
        
        # 读取图像
        img = cv2.imread(str(image_path))
        if img is None:
            raise OCRError(f"无法读取图像: {image_path}")
        
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        logger.debug("✓ 转换为灰度图")
        
        # 根据预处理级别应用不同的增强
        if self.preprocessing_level == 'light':
            processed = self._light_preprocessing(gray)
        elif self.preprocessing_level == 'heavy':
            processed = self._heavy_preprocessing(gray)
        else:  # medium (default)
            processed = self._medium_preprocessing(gray)
        
        logger.info("✓ 图像预处理完成")
        return processed
    
    def _light_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """
        轻度预处理：基础增强
        
        Args:
            gray: 灰度图像
        
        Returns:
            处理后的图像
        """
        # 1. 轻度去噪
        denoised = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=7, searchWindowSize=21)
        logger.debug("✓ 轻度去噪")
        
        # 2. 对比度增强（CLAHE）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        logger.debug("✓ CLAHE 对比度增强")
        
        return enhanced
    
    def _medium_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """
        中度预处理：平衡增强
        
        Args:
            gray: 灰度图像
        
        Returns:
            处理后的图像
        """
        # 1. 去噪
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        logger.debug("✓ 去噪")
        
        # 2. 对比度增强（CLAHE）
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        logger.debug("✓ CLAHE 对比度增强")
        
        # 3. 锐化
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        logger.debug("✓ 锐化处理")
        
        # 4. 自适应二值化（可选，根据效果决定是否使用）
        # binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #                                cv2.THRESH_BINARY, 11, 2)
        
        return sharpened
    
    def _heavy_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """
        重度预处理：最大增强
        
        Args:
            gray: 灰度图像
        
        Returns:
            处理后的图像
        """
        # 1. 强力去噪
        denoised = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)
        logger.debug("✓ 强力去噪")
        
        # 2. 对比度增强（CLAHE）
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        logger.debug("✓ CLAHE 对比度增强")
        
        # 3. 双边滤波（保边去噪）
        bilateral = cv2.bilateralFilter(enhanced, 9, 75, 75)
        logger.debug("✓ 双边滤波")
        
        # 4. 锐化
        kernel = np.array([[-1, -1, -1],
                          [-1, 10, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(bilateral, -1, kernel)
        logger.debug("✓ 锐化处理")
        
        # 5. 自适应二值化
        binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        logger.debug("✓ 自适应二值化")
        
        return binary
    
    def extract_from_image(self, image_path: Path, save_preprocessed: bool = False) -> pd.DataFrame:
        """
        从图像中提取指定的数据项
        
        Args:
            image_path: 图像文件路径
            save_preprocessed: 是否保存预处理后的图像
        
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
            # 图像预处理
            preprocessed = self._preprocess_image(image_path)
            
            # 保存预处理后的图像（如果需要）
            if save_preprocessed:
                output_path = image_path.parent / f"{image_path.stem}_preprocessed_v10_{self.preprocessing_level}.png"
                cv2.imwrite(str(output_path), preprocessed)
                logger.info(f"✓ 预处理图像已保存: {output_path}")
            
            # 使用 EasyOCR 识别所有文本
            results = self.reader.readtext(preprocessed)
            
            # 提取所有数字及其位置
            all_numbers = self._extract_numbers(results, preprocessed.shape)
            
            logger.info(f"EasyOCR 识别到 {len(all_numbers)} 个数字")
            
            if not all_numbers:
                logger.warning("未识别到任何数字")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            items = []
            
            # 提取 COMBINER 数据
            logger.info("匹配 COMBINER ISO TEMPERATURES 数据...")
            combiner_data = self._find_combiner_numbers_v10(all_numbers)
            items.extend(combiner_data)
            
            # 提取 Z-Plane 数据
            for module in self.ZPLANE_MODULES:
                logger.info(f"匹配 Z-Plane {module} 数据...")
                zplane_data = self._find_zplane_numbers_v10(all_numbers, module)
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
    
    def _extract_numbers(self, results: List, image_shape: Tuple) -> List[Dict]:
        """
        从 EasyOCR 结果中提取所有数字
        
        Args:
            results: EasyOCR 识别结果
            image_shape: 图像形状 (height, width)
        
        Returns:
            数字列表，每个元素包含 text, value, x, y, x_center, y_center, conf
        """
        img_height, img_width = image_shape[:2]
        
        numbers = []
        
        for bbox, text, conf in results:
            # 计算边界框中心点
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            
            # 尝试解析为数字
            try:
                # 清理文本
                cleaned = text.replace(',', '.').replace('O', '0').replace('o', '0').replace(' ', '')
                value = float(cleaned)
                
                numbers.append({
                    'text': text,
                    'value': value,
                    'x': x_min,
                    'y': y_min,
                    'x_center': x_center / img_width,
                    'y_center': y_center / img_height,
                    'conf': conf
                })
                
                logger.debug(f"识别到数字: {value} at ({x_center/img_width:.3f}, {y_center/img_height:.3f}), conf={conf:.2f}")
            
            except ValueError:
                # 不是数字，跳过
                pass
        
        return numbers
    
    def _find_combiner_numbers_v10(self, numbers: List[Dict]) -> List[Dict]:
        """
        V10 版本：找出 COMBINER 数据（继承 V8 逻辑）
        """
        # COMBINER 区域大致在 y < 0.4 的位置
        combiner_candidates = [n for n in numbers if n['y_center'] < 0.4 and n['conf'] > 0.3]
        
        if not combiner_candidates:
            logger.warning("未找到 COMBINER 候选数字")
            return []
        
        # 按 Y 坐标分组，找到同一行的数字
        y_tolerance = 0.06
        rows = []
        
        for num in combiner_candidates:
            found_row = False
            for row in rows:
                if abs(num['y_center'] - row[0]['y_center']) < y_tolerance:
                    row.append(num)
                    found_row = True
                    break
            if not found_row:
                rows.append([num])
        
        # 找到数字最多的行（应该是 COMBINER 行）
        if not rows:
            return []
        
        combiner_row = max(rows, key=len)
        combiner_row.sort(key=lambda x: x['x_center'])  # 按 X 坐标排序
        
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
                logger.debug(f"COMBINER {self.COMBINER_ITEMS[i]}: {num['value']}°C")
        
        return items
    
    def _find_zplane_numbers_v10(self, numbers: List[Dict], module: str) -> List[Dict]:
        """
        V10 版本：智能过滤校准因子（继承 V8 逻辑）
        """
        # Z-Plane 区域大致在 y > 0.4 的位置
        zplane_candidates = [n for n in numbers if n['y_center'] > 0.4 and n['conf'] > 0.25]
        
        if not zplane_candidates:
            logger.warning(f"未找到 Z-Plane {module} 候选数字")
            return []
        
        # 过滤校准因子
        calibration_values = {15.15, 332.0, 412.0}
        filtered_candidates = [
            n for n in zplane_candidates 
            if abs(n['value']) >= 0.01  # 过滤极小值
            and n['value'] not in calibration_values  # 过滤特定校准值
            and n['y_center'] <= 0.85  # 过滤底部区域
        ]
        
        logger.info(f"过滤前: {len(zplane_candidates)} 个候选，过滤后: {len(filtered_candidates)} 个")
        
        # 根据模块确定 X 范围
        module_index = self.ZPLANE_MODULES.index(module)
        
        # 对 Z-Plane D 使用更宽松的范围
        if module == 'D':
            x_start = max(0, module_index * 0.25 - 0.12)
            x_end = min(1.0, (module_index + 1) * 0.25 + 0.12)
        else:
            x_start = max(0, module_index * 0.25 - 0.08)
            x_end = min(1.0, (module_index + 1) * 0.25 + 0.08)
        
        # 筛选该模块的数字
        module_numbers = [n for n in filtered_candidates if x_start <= n['x_center'] < x_end]
        
        if not module_numbers:
            logger.warning(f"未找到 Z-Plane {module} 的数字")
            return []
        
        # 按 Y 坐标排序
        module_numbers.sort(key=lambda x: x['y_center'])
        
        logger.info(f"找到 Z-Plane {module} 的 {len(module_numbers)} 个数字")
        
        # 改进的行分组逻辑
        rows = self._group_numbers_into_rows(module_numbers)
        
        logger.info(f"Z-Plane {module} 分组为 {len(rows)} 行")
        
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
                logger.debug(f"Z-Plane {module} Row {row_num} Current: {row[0]['value']}A")
            
            if len(row) >= 2:
                items.append({
                    'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                    'value': row[1]['value'],
                    'unit': '°C'
                })
                logger.debug(f"Z-Plane {module} Row {row_num} ISO Temp: {row[1]['value']}°C")
        
        return items
    
    def _group_numbers_into_rows(self, numbers: List[Dict]) -> List[List[Dict]]:
        """
        改进的行分组逻辑（继承 V8）
        """
        if not numbers:
            return []
        
        rows = []
        y_tolerance = 0.045  # Y 坐标容差
        
        for num in numbers:
            found_row = False
            for row in rows:
                # 检查是否属于同一行
                if abs(num['y_center'] - row[0]['y_center']) < y_tolerance:
                    row.append(num)
                    found_row = True
                    break
            
            if not found_row:
                rows.append([num])
        
        # 为每行的数字排序（按 X 坐标）
        for row in rows:
            row.sort(key=lambda x: x['x_center'])
        
        # 按行的平均 Y 坐标排序
        rows.sort(key=lambda row: sum(n['y_center'] for n in row) / len(row))
        
        return rows
    
    def _parse_value_unit(self, text: str) -> Tuple[float, str]:
        """
        解析带单位的数值字符串（保持向后兼容）
        """
        text = text.strip()
        
        # 支持的单位模式
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


# 为了向后兼容，创建一个别名
OCRExtractor = OCRExtractorV10
