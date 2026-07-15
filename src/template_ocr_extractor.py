"""
基于模板匹配的本地OCR识别器

特点：
- 适用于固定布局的发射机截图
- 不依赖深度学习，纯CPU运算
- 低内存占用，适合老旧硬件
- 使用 OpenCV + Tesseract OCR
"""
import cv2
import numpy as np
import pytesseract
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.exceptions import OCRError

logger = logging.getLogger(__name__)


class TemplateOCRExtractor:
    """模板匹配OCR提取器
    
    工作流程：
    1. 加载固定区域坐标模板
    2. 图像预处理（灰度化、二值化）
    3. 按坐标提取各个数据区域
    4. 使用 Tesseract OCR 识别数字
    5. 后处理和验证
    """
    
    def __init__(self, coords_file: Optional[Path] = None, config: Optional[Dict] = None):
        """
        初始化提取器
        
        Args:
            coords_file: 坐标模板文件路径，默认为 config/template_coordinates.json
            config: 可选配置字典
        """
        self.coords_file = coords_file or Path('config/template_coordinates.json')
        self.config = config or {}
        
        # 设置 Tesseract 路径（Windows 打包版本需要）
        self._setup_tesseract_path()
        
        # Tesseract 配置
        self.tesseract_config = self.config.get(
            'tesseract_config',
            r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.'
        )
        
        # 预处理参数
        self.preprocess_mode = self.config.get('preprocess_mode', 'adaptive')  # 'simple', 'adaptive', 'none'
        self.apply_morphology = self.config.get('apply_morphology', False)
        
        # 验证参数
        self.valid_ranges = {
            'Current': (5.0, 10.0),      # 电流合理范围
            'ISO_Temp': (20.0, 80.0),    # 温度合理范围
            'Temp': (20.0, 80.0),        # 温度合理范围
        }
        
        # 加载坐标模板
        self.coords = self._load_coordinates()
        
        logger.info(f"模板OCR提取器初始化完成")
        logger.info(f"  坐标文件: {self.coords_file}")
        logger.info(f"  预处理模式: {self.preprocess_mode}")
        logger.info(f"  已加载区域: {self._count_regions()} 个")
    
    def _setup_tesseract_path(self):
        """设置 Tesseract 路径，支持 Windows 常见安装位置和打包版本"""
        import sys
        import os
        
        # 如果已经设置了路径，直接返回
        if hasattr(pytesseract, 'tesseract_cmd') and pytesseract.pytesseract.tesseract_cmd:
            current_path = pytesseract.pytesseract.tesseract_cmd
            if current_path != 'tesseract' and Path(current_path).exists():
                logger.info(f"使用已配置的 Tesseract 路径: {current_path}")
                return
        
        # 优先查找打包后的 Tesseract（PyInstaller）
        if getattr(sys, 'frozen', False):
            # 打包后的 EXE 环境
            base_path = Path(sys.executable).parent
            bundled_tesseract = base_path / 'tesseract' / 'tesseract.exe'
            
            if bundled_tesseract.exists():
                pytesseract.pytesseract.tesseract_cmd = str(bundled_tesseract)
                # 设置 tessdata 路径
                os.environ['TESSDATA_PREFIX'] = str(base_path / 'tesseract' / 'tessdata')
                logger.info(f"✓ 使用打包的 Tesseract: {bundled_tesseract}")
                return
        
        # Windows 系统需要设置路径
        if sys.platform == 'win32':
            # 常见的 Tesseract 安装路径
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
            ]
            
            # 从环境变量中查找
            if 'TESSERACT_PATH' in os.environ:
                possible_paths.insert(0, os.environ['TESSERACT_PATH'])
            
            # 尝试找到 Tesseract
            for path in possible_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"✓ 找到 Tesseract: {path}")
                    return
            
            # 如果都找不到，记录警告但继续（可能在PATH中）
            logger.warning("未找到 Tesseract 安装路径，尝试使用系统 PATH")
            logger.warning("如果 OCR 识别失败，请确保 Tesseract 已正确安装")
            logger.warning("推荐安装路径: C:\\Program Files\\Tesseract-OCR")
        else:
            # macOS/Linux 通常在 PATH 中
            logger.info("非 Windows 系统，使用系统 PATH 中的 tesseract")
    
    def _count_regions(self) -> int:
        """统计区域数量"""
        count = 0
        for key, value in self.coords.items():
            if isinstance(value, dict):
                count += len(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        count += len(item)
        return count
    
    def _load_coordinates(self) -> Dict:
        """加载坐标模板"""
        if not self.coords_file.exists():
            logger.warning(f"坐标文件不存在: {self.coords_file}")
            logger.warning("将使用空模板，请先运行坐标标定工具")
            return {}
        
        try:
            with open(self.coords_file, 'r', encoding='utf-8') as f:
                coords = json.load(f)
            
            logger.info(f"✓ 坐标模板加载成功: {self.coords_file}")
            return coords
        
        except Exception as e:
            logger.error(f"加载坐标模板失败: {e}")
            raise OCRError(f"无法加载坐标模板: {e}")
    
    def extract_from_image(self, image_path: Path) -> pd.DataFrame:
        """
        从图像提取数据
        
        Args:
            image_path: 图像路径
            
        Returns:
            包含识别结果的 DataFrame
            
        Raises:
            OCRError: OCR识别失败
        """
        logger.info(f"开始处理图像: {image_path}")
        
        try:
            # 1. 读取图像（使用PIL确保跨平台兼容）
            from PIL import Image as PILImage
            import numpy as np
            
            pil_image = PILImage.open(str(image_path))
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            img_rgb = np.array(pil_image)
            image = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            
            if image is None:
                raise OCRError(f"无法读取图像: {image_path}")
            
            logger.info(f"  图像尺寸: {image.shape[1]} x {image.shape[0]}")
            
            # 2. 提取所有区域并识别（不再统一预处理，改为按字段类型处理）
            results = []
            
            # 遍历所有坐标（支持扁平和嵌套两种格式）
            for item_name, coords in self.coords.items():
                # 判断坐标类型
                if isinstance(coords, list) and len(coords) == 4:
                    # 扁平格式：直接是坐标 [x1, y1, x2, y2]
                    # 判断数据类型
                    if 'Current' in item_name or 'current' in item_name:
                        expected_type = 'current'
                        unit = 'A'
                    elif 'Temp' in item_name or 'temp' in item_name:
                        expected_type = 'temperature'
                        unit = '°C'
                    else:
                        # COMBINER数据默认是温度
                        expected_type = 'temperature'
                        unit = '°C'
                    
                    value = self.extract_and_recognize(
                        image, tuple(coords),
                        expected_type=expected_type
                    )
                    
                    if value is not None:
                        results.append({
                            'item_name': item_name,
                            'value': value,
                            'unit': unit
                        })
                        logger.debug(f"    {item_name}: {value} {unit}")
                
                elif isinstance(coords, dict):
                    # 嵌套格式：COMBINER等
                    for sub_name, sub_coords in coords.items():
                        value = self.extract_and_recognize(
                            image, tuple(sub_coords),
                            expected_type='temperature'
                        )
                        if value is not None:
                            results.append({
                                'item_name': sub_name,
                                'value': value,
                                'unit': '°C'
                            })
                            logger.debug(f"    {sub_name}: {value}°C")
            
            logger.info(f"✓ 识别完成: 共 {len(results)} 个数据项")
            
            return pd.DataFrame(results)
        
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            raise OCRError(f"OCR识别失败: {e}")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像
            
        Returns:
            预处理后的图像
        """
        if self.preprocess_mode == 'none':
            return image
        
        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        if self.preprocess_mode == 'simple':
            # 简单二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        
        elif self.preprocess_mode == 'adaptive':
            # 自适应二值化（更适合光照不均）
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 可选：形态学处理去噪
            if self.apply_morphology:
                kernel = np.ones((2, 2), np.uint8)
                binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return binary
        
        else:
            return gray
    
    def extract_and_recognize(
        self, 
        image: np.ndarray, 
        coords: Tuple[int, int, int, int],
        expected_type: Optional[str] = None
    ) -> Optional[float]:
        """
        提取区域并识别
        
        Args:
            image: 原始图像（未预处理）
            coords: 区域坐标 (x1, y1, x2, y2)
            expected_type: 期望的数据类型 ('current', 'temperature')
            
        Returns:
            识别的数值，失败返回 None
        """
        try:
            x1, y1, x2, y2 = coords
            
            # 边界检查
            h, w = image.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 <= x1 or y2 <= y1:
                logger.warning(f"无效的坐标: {coords}")
                return None
            
            # 提取 ROI
            roi = image[y1:y2, x1:x2]
            
            # 根据数据类型选择最佳预处理方法
            if expected_type == 'current':
                # Current字段：使用灰度或简单Otsu，不用自适应二值化
                processed_roi = self._preprocess_for_current(roi)
            else:
                # Temperature字段：使用自适应二值化
                processed_roi = self._preprocess_for_temperature(roi)
            
            # 可选：ROI增强
            processed_roi = self._enhance_roi(processed_roi)
            
            # OCR识别
            text = pytesseract.image_to_string(processed_roi, config=self.tesseract_config)
            
            # 清理文本（传入expected_type以便智能处理）
            cleaned = self._clean_text(text, expected_type=expected_type)
            
            if not cleaned:
                logger.debug(f"OCR返回空文本: coords={coords}")
                return None
            
            # 转换为浮点数
            try:
                value = float(cleaned)
            except ValueError:
                logger.debug(f"无法转换为数字: '{cleaned}' at {coords}")
                return None
            
            # 验证合理性
            if expected_type and not self._validate_value(value, expected_type):
                logger.debug(f"数值超出合理范围: {value} ({expected_type}) at {coords}")
                return None
            
            return value
        
        except Exception as e:
            logger.debug(f"识别失败: {e} at {coords}")
            return None
    
    def _preprocess_for_current(self, roi: np.ndarray) -> np.ndarray:
        """
        Current字段专用预处理
        
        Current字段通常是白色文字或浅色背景，使用简单二值化效果最好
        """
        # 转灰度
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi.copy()
        
        # 使用简单二值化（Otsu自动阈值）
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _preprocess_for_temperature(self, roi: np.ndarray) -> np.ndarray:
        """
        Temperature字段专用预处理
        
        Temperature字段使用简单二值化效果更稳定
        """
        # 转灰度
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi.copy()
        
        # 使用简单二值化（Otsu自动阈值）- 比自适应二值化更稳定
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _enhance_roi(self, roi: np.ndarray) -> np.ndarray:
        """增强 ROI 质量"""
        # 可选：放大小区域
        if roi.shape[0] < 30 or roi.shape[1] < 50:
            scale = 2
            roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        return roi
    
    def _clean_text(self, text: str, expected_type: Optional[str] = None) -> str:
        """清理OCR识别的文本"""
        # 去除空白
        text = text.strip()
        
        # 去除所有空格和换行符
        text = text.replace(' ', '').replace('\n', '')
        
        # 常见识别错误修正
        replacements = {
            'O': '0',  # 字母O → 数字0
            'o': '0',
            'I': '1',  # 字母I → 数字1
            'l': '1',  # 小写L → 数字1
            'S': '5',  # 字母S → 数字5（如果需要）
            'B': '8',  # 字母B → 数字8（如果需要）
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # 只保留数字和小数点
        cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
        
        # 处理多个小数点
        if cleaned.count('.') > 1:
            # 只保留第一个小数点
            parts = cleaned.split('.')
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        
        # Current字段特殊处理：如果是两位整数，可能是缺少小数点
        # 例如 "73" 应该是 "7.3"，"78" 应该是 "7.8"
        if expected_type == 'current' and cleaned and '.' not in cleaned:
            if len(cleaned) == 2:
                # 两位数字，插入小数点
                cleaned = cleaned[0] + '.' + cleaned[1]
            elif len(cleaned) == 3 and cleaned[0] == '1':
                # 三位数且首位是1，可能是 "100" 之类，插入小数点: "10.0"
                cleaned = cleaned[:2] + '.' + cleaned[2]
        
        return cleaned
    
    def _validate_value(self, value: float, value_type: str) -> bool:
        """验证数值合理性"""
        if value_type == 'current':
            min_val, max_val = self.valid_ranges['Current']
        elif value_type == 'temperature':
            min_val, max_val = self.valid_ranges['ISO_Temp']
        else:
            return True  # 未知类型，不验证
        
        return min_val <= value <= max_val
    
    def test_single_region(
        self, 
        image_path: Path, 
        coords: Tuple[int, int, int, int],
        save_roi: bool = False
    ) -> Optional[float]:
        """
        测试单个区域识别（用于调试）
        
        Args:
            image_path: 图像路径
            coords: 区域坐标
            save_roi: 是否保存 ROI 图像
            
        Returns:
            识别结果
        """
        from PIL import Image as PILImage
        import numpy as np
        
        pil_image = PILImage.open(str(image_path))
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        img_rgb = np.array(pil_image)
        image = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        if image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        processed = self.preprocess(image)
        
        x1, y1, x2, y2 = coords
        roi = processed[y1:y2, x1:x2]
        
        if save_roi:
            output_path = Path(f'debug_roi_{x1}_{y1}.png')
            cv2.imwrite(str(output_path), roi)
            print(f"✓ ROI 已保存: {output_path}")
        
        result = self.extract_and_recognize(processed, coords)
        
        print(f"坐标: {coords}")
        print(f"ROI 尺寸: {roi.shape}")
        print(f"识别结果: {result}")
        
        return result
    
    def batch_test_accuracy(
        self, 
        image_path: Path, 
        ground_truth: Dict[str, float]
    ) -> Dict:
        """
        批量测试识别准确率
        
        Args:
            image_path: 图像路径
            ground_truth: 真实值字典 {item_name: value}
            
        Returns:
            测试结果统计
        """
        results = self.extract_from_image(image_path)
        
        stats = {
            'total': len(ground_truth),
            'recognized': len(results),
            'correct': 0,
            'errors': []
        }
        
        for _, row in results.iterrows():
            item_name = row['item_name']
            recognized_value = row['value']
            
            if item_name in ground_truth:
                true_value = ground_truth[item_name]
                error = abs(recognized_value - true_value)
                
                # 允许小误差（±0.5）
                if error <= 0.5:
                    stats['correct'] += 1
                else:
                    stats['errors'].append({
                        'item': item_name,
                        'recognized': recognized_value,
                        'true': true_value,
                        'error': error
                    })
        
        stats['accuracy'] = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        
        return stats


# 便捷函数
def extract_from_image(image_path: Path, coords_file: Optional[Path] = None) -> pd.DataFrame:
    """
    便捷函数：从图像提取数据
    
    Args:
        image_path: 图像路径
        coords_file: 坐标文件路径
        
    Returns:
        识别结果 DataFrame
    """
    extractor = TemplateOCRExtractor(coords_file)
    return extractor.extract_from_image(image_path)
