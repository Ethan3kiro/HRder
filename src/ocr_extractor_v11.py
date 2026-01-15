"""
OCR提取模块 V11 - 多引擎融合版

主要改进：
1. 同时使用 Tesseract 和 EasyOCR 两个引擎
2. 合并两个引擎的识别结果
3. 去重和冲突解决（使用置信度投票）
4. 保留 V8 的智能过滤校准因子功能
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

import numpy as np
import pandas as pd
from PIL import Image
import shutil

# Handle Tesseract import
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError as e:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

# Handle EasyOCR import
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError as e:
    EASYOCR_AVAILABLE = False
    easyocr = None

from src.exceptions import OCRError, FileError
from src.config import Config

logger = logging.getLogger("transmitter.ocr_v11")


class OCRExtractorV11:
    """OCR数据提取器 V11 - 多引擎融合版"""
    
    # 需要提取的 COMBINER ISO TEMPERATURES 数据项
    COMBINER_ITEMS = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
    
    # Z-Plane 模块列表
    ZPLANE_MODULES = ['A', 'B', 'C', 'D']
    
    # 每个 Z-Plane 的行数
    ZPLANE_ROWS = 8
    
    def __init__(self, use_tesseract: bool = True, use_easyocr: bool = True):
        """
        初始化OCR提取器
        
        Args:
            use_tesseract: 是否使用 Tesseract
            use_easyocr: 是否使用 EasyOCR
        
        Raises:
            OCRError: 两个引擎都不可用
        """
        self.use_tesseract = use_tesseract and PYTESSERACT_AVAILABLE
        self.use_easyocr = use_easyocr and EASYOCR_AVAILABLE
        
        if not self.use_tesseract and not self.use_easyocr:
            raise OCRError(
                "至少需要一个 OCR 引擎可用。\n"
                "请安装 Tesseract 或 EasyOCR。"
            )
        
        logger.info(f"正在初始化 OCR V11 (Tesseract: {self.use_tesseract}, EasyOCR: {self.use_easyocr})...")
        
        # 初始化 Tesseract
        if self.use_tesseract:
            try:
                self._init_tesseract()
                logger.info("✓ Tesseract 初始化成功")
            except Exception as e:
                logger.warning(f"Tesseract 初始化失败: {e}")
                self.use_tesseract = False
        
        # 初始化 EasyOCR
        if self.use_easyocr:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                logger.info("✓ EasyOCR 初始化成功")
            except Exception as e:
                logger.warning(f"EasyOCR 初始化失败: {e}")
                self.use_easyocr = False
        
        if not self.use_tesseract and not self.use_easyocr:
            raise OCRError("所有 OCR 引擎初始化失败")
        
        logger.info(f"✓ OCR V11 初始化完成 (活跃引擎: {self._get_active_engines()})")
    
    def _init_tesseract(self):
        """初始化 Tesseract"""
        # 检测 Tesseract 路径
        tesseract_path = self._detect_tesseract()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # 验证 Tesseract 可用
        try:
            version = pytesseract.get_tesseract_version()
            logger.debug(f"Tesseract 版本: {version}")
        except Exception as e:
            raise OCRError(f"Tesseract 不可用: {e}")
    
    def _detect_tesseract(self) -> Optional[str]:
        """检测 Tesseract 路径"""
        # 尝试 Config 默认路径
        default_path = Config.get_tesseract_path()
        if default_path:
            return default_path
        
        # 尝试系统 PATH
        tesseract_cmd = shutil.which("tesseract")
        if tesseract_cmd:
            return tesseract_cmd
        
        return None
    
    def _get_active_engines(self) -> str:
        """获取活跃引擎列表"""
        engines = []
        if self.use_tesseract:
            engines.append("Tesseract")
        if self.use_easyocr:
            engines.append("EasyOCR")
        return " + ".join(engines)
    
    def extract_from_image(self, image_path: Path) -> pd.DataFrame:
        """
        从图像中提取指定的数据项（使用多引擎融合）
        
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
        logger.info(f"使用引擎: {self._get_active_engines()}")
        
        try:
            # 收集所有引擎的识别结果
            all_numbers = []
            
            # Tesseract 识别
            if self.use_tesseract:
                logger.info("运行 Tesseract 识别...")
                tesseract_numbers = self._extract_with_tesseract(image_path)
                logger.info(f"Tesseract 识别到 {len(tesseract_numbers)} 个数字")
                all_numbers.extend(tesseract_numbers)
            
            # EasyOCR 识别
            if self.use_easyocr:
                logger.info("运行 EasyOCR 识别...")
                easyocr_numbers = self._extract_with_easyocr(image_path)
                logger.info(f"EasyOCR 识别到 {len(easyocr_numbers)} 个数字")
                all_numbers.extend(easyocr_numbers)
            
            if not all_numbers:
                logger.warning("所有引擎都未识别到数字")
                return pd.DataFrame(columns=["item_name", "value", "unit"])
            
            # 合并和去重
            logger.info(f"合并前共 {len(all_numbers)} 个数字")
            merged_numbers = self._merge_and_deduplicate(all_numbers)
            logger.info(f"合并后共 {len(merged_numbers)} 个数字")
            
            items = []
            
            # 提取 COMBINER 数据
            logger.info("匹配 COMBINER ISO TEMPERATURES 数据...")
            combiner_data = self._find_combiner_numbers(merged_numbers)
            items.extend(combiner_data)
            
            # 提取 Z-Plane 数据
            for module in self.ZPLANE_MODULES:
                logger.info(f"匹配 Z-Plane {module} 数据...")
                zplane_data = self._find_zplane_numbers(merged_numbers, module)
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
    
    def _extract_with_tesseract(self, image_path: Path) -> List[Dict]:
        """使用 Tesseract 提取数字"""
        # 加载图像
        image = Image.open(image_path)
        img_width, img_height = image.size
        
        # 使用 Tesseract 提取
        data = pytesseract.image_to_data(
            image, 
            output_type=pytesseract.Output.DICT,
            lang='eng',
            config='--oem 3 --psm 6'
        )
        
        numbers = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            
            if not text or conf < 30:
                continue
            
            # 尝试解析为数字
            try:
                cleaned = text.replace(',', '.').replace('O', '0').replace('o', '0').replace(' ', '')
                value = float(cleaned)
                
                # 计算中心点
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                x_center = (x + w / 2) / img_width
                y_center = (y + h / 2) / img_height
                
                numbers.append({
                    'text': text,
                    'value': value,
                    'x_center': x_center,
                    'y_center': y_center,
                    'conf': conf / 100.0,  # 归一化到 0-1
                    'source': 'tesseract'
                })
                
                logger.debug(f"Tesseract: {value} at ({x_center:.3f}, {y_center:.3f}), conf={conf/100:.2f}")
            
            except ValueError:
                pass
        
        return numbers
    
    def _extract_with_easyocr(self, image_path: Path) -> List[Dict]:
        """使用 EasyOCR 提取数字"""
        # 获取图像尺寸
        image = Image.open(image_path)
        img_width, img_height = image.size
        
        # 使用 EasyOCR 识别
        results = self.easyocr_reader.readtext(str(image_path))
        
        numbers = []
        
        for bbox, text, conf in results:
            # 计算边界框中心点
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x_center = sum(x_coords) / len(x_coords) / img_width
            y_center = sum(y_coords) / len(y_coords) / img_height
            
            # 尝试解析为数字
            try:
                cleaned = text.replace(',', '.').replace('O', '0').replace('o', '0').replace(' ', '')
                value = float(cleaned)
                
                numbers.append({
                    'text': text,
                    'value': value,
                    'x_center': x_center,
                    'y_center': y_center,
                    'conf': conf,
                    'source': 'easyocr'
                })
                
                logger.debug(f"EasyOCR: {value} at ({x_center:.3f}, {y_center:.3f}), conf={conf:.2f}")
            
            except ValueError:
                pass
        
        return numbers
    
    def _merge_and_deduplicate(self, numbers: List[Dict]) -> List[Dict]:
        """
        合并和去重数字
        
        策略：
        1. 如果两个数字位置接近（距离 < 0.05）且数值相同，认为是同一个数字
        2. 保留置信度更高的那个
        3. 如果数值不同但位置接近，保留置信度更高的那个
        """
        if not numbers:
            return []
        
        merged = []
        used = set()
        
        for i, num1 in enumerate(numbers):
            if i in used:
                continue
            
            # 查找与 num1 位置接近的其他数字
            duplicates = [num1]
            
            for j, num2 in enumerate(numbers):
                if j <= i or j in used:
                    continue
                
                # 计算距离
                dist = ((num1['x_center'] - num2['x_center']) ** 2 + 
                       (num1['y_center'] - num2['y_center']) ** 2) ** 0.5
                
                if dist < 0.05:  # 位置接近
                    duplicates.append(num2)
                    used.add(j)
            
            # 从重复项中选择最佳的
            if len(duplicates) == 1:
                merged.append(num1)
            else:
                # 选择置信度最高的
                best = max(duplicates, key=lambda x: x['conf'])
                
                # 如果有多个引擎识别到相同数值，提升置信度
                same_value = [d for d in duplicates if abs(d['value'] - best['value']) < 0.01]
                if len(same_value) > 1:
                    best = best.copy()
                    best['conf'] = min(1.0, best['conf'] * 1.2)  # 提升 20%
                    best['source'] = 'merged'
                    logger.debug(f"合并: {best['value']} (置信度提升到 {best['conf']:.2f})")
                
                merged.append(best)
        
        return merged
    
    def _find_combiner_numbers(self, numbers: List[Dict]) -> List[Dict]:
        """找出 COMBINER 数据（继承 V8 逻辑）"""
        # COMBINER 区域大致在 y < 0.4 的位置
        combiner_candidates = [n for n in numbers if n['y_center'] < 0.4 and n['conf'] > 0.3]
        
        if not combiner_candidates:
            logger.warning("未找到 COMBINER 候选数字")
            return []
        
        # 按 Y 坐标分组
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
        
        if not rows:
            return []
        
        # 找到数字最多的行
        combiner_row = max(rows, key=len)
        combiner_row.sort(key=lambda x: x['x_center'])
        
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
                logger.debug(f"COMBINER {self.COMBINER_ITEMS[i]}: {num['value']}°C (来源: {num['source']})")
        
        return items
    
    def _find_zplane_numbers(self, numbers: List[Dict], module: str) -> List[Dict]:
        """找出 Z-Plane 数据（继承 V8 逻辑）"""
        # Z-Plane 区域大致在 y > 0.4 的位置
        zplane_candidates = [n for n in numbers if n['y_center'] > 0.4 and n['conf'] > 0.25]
        
        if not zplane_candidates:
            logger.warning(f"未找到 Z-Plane {module} 候选数字")
            return []
        
        # 过滤校准因子
        calibration_values = {15.15, 332.0, 412.0}
        filtered_candidates = [
            n for n in zplane_candidates 
            if abs(n['value']) >= 0.01
            and n['value'] not in calibration_values
            and n['y_center'] <= 0.85
        ]
        
        logger.info(f"过滤前: {len(zplane_candidates)} 个候选，过滤后: {len(filtered_candidates)} 个")
        
        # 根据模块确定 X 范围
        module_index = self.ZPLANE_MODULES.index(module)
        
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
        
        # 行分组
        rows = self._group_numbers_into_rows(module_numbers)
        
        logger.info(f"Z-Plane {module} 分组为 {len(rows)} 行")
        
        # 匹配到数据项
        items = []
        for row_num, row in enumerate(rows, 1):
            if row_num > self.ZPLANE_ROWS:
                break
            
            if len(row) >= 1:
                items.append({
                    'item_name': f'Z-Plane {module}-Current-{row_num}',
                    'value': row[0]['value'],
                    'unit': 'A'
                })
                logger.debug(f"Z-Plane {module} Row {row_num} Current: {row[0]['value']}A (来源: {row[0]['source']})")
            
            if len(row) >= 2:
                items.append({
                    'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                    'value': row[1]['value'],
                    'unit': '°C'
                })
                logger.debug(f"Z-Plane {module} Row {row_num} ISO Temp: {row[1]['value']}°C (来源: {row[1]['source']})")
        
        return items
    
    def _group_numbers_into_rows(self, numbers: List[Dict]) -> List[List[Dict]]:
        """行分组逻辑（继承 V8）"""
        if not numbers:
            return []
        
        rows = []
        y_tolerance = 0.045
        
        for num in numbers:
            found_row = False
            for row in rows:
                if abs(num['y_center'] - row[0]['y_center']) < y_tolerance:
                    row.append(num)
                    found_row = True
                    break
            
            if not found_row:
                rows.append([num])
        
        # 为每行排序
        for row in rows:
            row.sort(key=lambda x: x['x_center'])
        
        # 按行的平均 Y 坐标排序
        rows.sort(key=lambda row: sum(n['y_center'] for n in row) / len(row))
        
        return rows


# 为了向后兼容，创建一个别名
OCRExtractor = OCRExtractorV11
