"""
OCR提取模块 V7 - 进一步优化版 EasyOCR 智能提取

主要改进：
1. 回归简单但有效的容差匹配（DBSCAN 效果不佳）
2. 增大 Y 坐标容差以捕获更多行
3. 动态调整 X 坐标范围（增加重叠）
4. 改进数字分配逻辑
5. 添加置信度过滤
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

import numpy as np
import pandas as pd
from PIL import Image

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

logger = logging.getLogger("transmitter.ocr_v7")


class OCRExtractorV7:
    """OCR数据提取器 V7 - 进一步优化版 EasyOCR 智能提取"""
    
    # 需要提取的 COMBINER ISO TEMPERATURES 数据项
    COMBINER_ITEMS = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    # Z-Plane 模块列表
    ZPLANE_MODULES = ['A', 'B', 'C', 'D']
    
    # 每个 Z-Plane 的行数
    ZPLANE_ROWS = 8
    
    def __init__(self):
        """
        初始化OCR提取器
        
        Raises:
            OCRError: EasyOCR未安装或初始化失败
        """
        if not EASYOCR_AVAILABLE:
            raise OCRError(
                "easyocr模块不可用。\n"
                "请安装 EasyOCR:\n"
                "pip3 install easyocr -i https://mirrors.aliyun.com/pypi/simple/"
            )
        
        try:
            # 初始化 EasyOCR Reader（使用英文模型，CPU模式）
            logger.info("正在初始化 EasyOCR V7...")
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("✓ EasyOCR V7 初始化成功")
        except Exception as e:
            raise OCRError(f"EasyOCR 初始化失败: {e}")
    
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
            # 使用 EasyOCR 识别所有文本
            results = self.reader.readtext(str(image_path))
            
            # 提取所有数字及其位置
            all_numbers = self._extract_numbers(results, image_path)
            
            logger.info(f"EasyOCR 识别到 {len(all_numbers)} 个数字")
            
            if not all_numbers:
                logger.warning("未识别到任何数字")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            items = []
            
            # 提取 COMBINER 数据
            logger.info("匹配 COMBINER ISO TEMPERATURES 数据...")
            combiner_data = self._find_combiner_numbers_v7(all_numbers)
            items.extend(combiner_data)
            
            # 提取 Z-Plane 数据
            for module in self.ZPLANE_MODULES:
                logger.info(f"匹配 Z-Plane {module} 数据...")
                zplane_data = self._find_zplane_numbers_v7(all_numbers, module)
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
    
    def _extract_numbers(self, results: List, image_path: Path) -> List[Dict]:
        """
        从 EasyOCR 结果中提取所有数字
        
        Args:
            results: EasyOCR 识别结果
            image_path: 图像路径（用于获取图像尺寸）
        
        Returns:
            数字列表，每个元素包含 text, value, x, y, x_center, y_center, conf
        """
        # 获取图像尺寸
        image = Image.open(image_path)
        img_width, img_height = image.size
        
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
    
    def _find_combiner_numbers_v7(self, numbers: List[Dict]) -> List[Dict]:
        """
        V7 改进版：使用更大的容差找出 COMBINER 数据
        
        改进：
        1. 增大 Y 坐标容差（0.05 -> 0.06）
        2. 过滤低置信度数字
        """
        # COMBINER 区域大致在 y < 0.4 的位置
        combiner_candidates = [n for n in numbers if n['y_center'] < 0.4 and n['conf'] > 0.3]
        
        if not combiner_candidates:
            logger.warning("未找到 COMBINER 候选数字")
            return []
        
        # 按 Y 坐标分组，找到同一行的数字
        y_tolerance = 0.06  # 增大容差
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
    
    def _find_zplane_numbers_v7(self, numbers: List[Dict], module: str) -> List[Dict]:
        """
        V7 改进版：使用更大的容差和动态 X 范围找出 Z-Plane 数据
        
        改进：
        1. 增大 Y 坐标容差（0.03 -> 0.045）
        2. 动态调整 X 坐标范围（增加重叠）
        3. 过滤低置信度数字
        """
        # Z-Plane 区域大致在 y > 0.4 的位置
        zplane_candidates = [n for n in numbers if n['y_center'] > 0.4 and n['conf'] > 0.25]
        
        if not zplane_candidates:
            logger.warning(f"未找到 Z-Plane {module} 候选数字")
            return []
        
        # 根据模块确定 X 范围（增加重叠以改善边界识别）
        module_index = self.ZPLANE_MODULES.index(module)
        x_start = max(0, module_index * 0.25 - 0.08)  # 向左扩展 8%
        x_end = min(1.0, (module_index + 1) * 0.25 + 0.08)  # 向右扩展 8%
        
        # 筛选该模块的数字
        module_numbers = [n for n in zplane_candidates if x_start <= n['x_center'] < x_end]
        
        if not module_numbers:
            logger.warning(f"未找到 Z-Plane {module} 的数字")
            return []
        
        # 按 Y 坐标排序
        module_numbers.sort(key=lambda x: x['y_center'])
        
        logger.info(f"找到 Z-Plane {module} 的 {len(module_numbers)} 个数字")
        
        # 按行分组（每行应该有2个数字：Current 和 ISO Temp）
        rows = []
        y_tolerance = 0.045  # 增大容差
        
        for num in module_numbers:
            found_row = False
            for row in rows:
                if abs(num['y_center'] - row[0]['y_center']) < y_tolerance:
                    row.append(num)
                    found_row = True
                    break
            if not found_row:
                rows.append([num])
        
        # 为每行的数字排序（按 X 坐标）
        for row in rows:
            row.sort(key=lambda x: x['x_center'])
        
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
    
    def _parse_value_unit(self, text: str) -> Tuple[float, str]:
        """
        解析带单位的数值字符串（保持向后兼容）
        
        Args:
            text: 原始文本（如"12.5V"、"407%"）
        
        Returns:
            (数值, 单位)元组
        
        Raises:
            ValueError: 无法解析为数值
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
OCRExtractor = OCRExtractorV7
