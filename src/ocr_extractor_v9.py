"""
OCR提取模块 V9 - PaddleOCR 版本

主要特性：
1. 使用 PaddleOCR 替代 EasyOCR
2. 继承 V8 的智能过滤校准因子逻辑
3. PaddleOCR 对中英文混合识别更好
4. 可能识别更多数字
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

import numpy as np
import pandas as pd
from PIL import Image

# Handle PaddleOCR import
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError as e:
    PADDLEOCR_AVAILABLE = False
    PaddleOCR = None
    import warnings
    warnings.warn(f"paddleocr import failed: {e}. OCR functionality will be limited.")

from src.exceptions import OCRError, FileError
from src.config import Config

logger = logging.getLogger("transmitter.ocr_v9")


class OCRExtractorV9:
    """OCR数据提取器 V9 - PaddleOCR 版本"""
    
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
            OCRError: PaddleOCR未安装或初始化失败
        """
        if not PADDLEOCR_AVAILABLE:
            raise OCRError(
                "paddleocr模块不可用。\n"
                "请安装 PaddleOCR:\n"
                "pip3 install paddlepaddle paddleocr -i https://mirrors.aliyun.com/pypi/simple/"
            )
        
        try:
            # 初始化 PaddleOCR（使用英文模型，CPU模式）
            logger.info("正在初始化 PaddleOCR V9...")
            self.reader = PaddleOCR(
                use_angle_cls=True,  # 使用方向分类器
                lang='en'  # 英文模型
            )
            logger.info("✓ PaddleOCR V9 初始化成功")
        except Exception as e:
            raise OCRError(f"PaddleOCR 初始化失败: {e}")
    
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
            # 使用 PaddleOCR 识别所有文本
            results = self.reader.ocr(str(image_path), cls=True)
            
            # PaddleOCR 返回格式: [[[bbox], (text, conf)], ...]
            # 需要转换为统一格式
            if not results or not results[0]:
                logger.warning("PaddleOCR 未识别到任何内容")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            # 提取所有数字及其位置
            all_numbers = self._extract_numbers(results[0], image_path)
            
            logger.info(f"PaddleOCR 识别到 {len(all_numbers)} 个数字")
            
            if not all_numbers:
                logger.warning("未识别到任何数字")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            items = []
            
            # 提取 COMBINER 数据（使用所有数字）
            logger.info("匹配 COMBINER ISO TEMPERATURES 数据...")
            combiner_data = self._find_combiner_numbers_v9(all_numbers)
            items.extend(combiner_data)
            
            # 提取 Z-Plane 数据（过滤掉底部校准因子区域）
            for module in self.ZPLANE_MODULES:
                logger.info(f"匹配 Z-Plane {module} 数据...")
                zplane_data = self._find_zplane_numbers_v9(all_numbers, module)
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
        从 PaddleOCR 结果中提取所有数字
        
        Args:
            results: PaddleOCR 识别结果
            image_path: 图像路径（用于获取图像尺寸）
        
        Returns:
            数字列表，每个元素包含 text, value, x, y, x_center, y_center, conf
        """
        # 获取图像尺寸
        image = Image.open(image_path)
        img_width, img_height = image.size
        
        numbers = []
        
        for item in results:
            # PaddleOCR 格式: [bbox, (text, conf)]
            bbox = item[0]
            text = item[1][0]
            conf = item[1][1]
            
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
    
    def _find_combiner_numbers_v9(self, numbers: List[Dict]) -> List[Dict]:
        """
        V9 版本：找出 COMBINER 数据
        
        继承 V7/V8 的逻辑
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
    
    def _find_zplane_numbers_v9(self, numbers: List[Dict], module: str) -> List[Dict]:
        """
        V9 版本：智能过滤校准因子，找出 Z-Plane 数据
        
        继承 V8 的智能过滤逻辑
        """
        # Z-Plane 区域大致在 y > 0.4 的位置
        zplane_candidates = [n for n in numbers if n['y_center'] > 0.4 and n['conf'] > 0.25]
        
        if not zplane_candidates:
            logger.warning(f"未找到 Z-Plane {module} 候选数字")
            return []
        
        # 过滤校准因子：
        # 1. 极小值（<0.01）- 如 0.015355, 0.000619
        # 2. 特定校准值 - 如 15.15, 332, 412
        # 3. 底部区域（y > 0.85）
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
            x_start = max(0, module_index * 0.25 - 0.12)  # 向左扩展 12%
            x_end = min(1.0, (module_index + 1) * 0.25 + 0.12)  # 向右扩展 12%
        else:
            x_start = max(0, module_index * 0.25 - 0.08)  # 向左扩展 8%
            x_end = min(1.0, (module_index + 1) * 0.25 + 0.08)  # 向右扩展 8%
        
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
        改进的行分组逻辑
        
        Args:
            numbers: 已按 Y 坐标排序的数字列表（已过滤校准因子）
        
        Returns:
            行列表，每行包含该行的数字（按 X 坐标排序）
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
OCRExtractor = OCRExtractorV9
