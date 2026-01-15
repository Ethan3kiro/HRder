"""
深度学习 OCR 提取器
使用训练好的深度学习模型进行数字识别
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

import cv2
import numpy as np
import pandas as pd

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

from src.exceptions import OCRError

logger = logging.getLogger("transmitter.dl_ocr")


class DigitCNN(nn.Module):
    """数字识别 CNN 模型"""
    
    def __init__(self):
        super(DigitCNN, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        # 池化层
        self.pool = nn.MaxPool2d(2, 2)
        
        # Dropout
        self.dropout = nn.Dropout(0.5)
        
        # 全连接层
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 1)
        
        # 激活函数
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # 卷积块
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        
        x = self.relu(self.conv3(x))
        x = self.pool(x)
        
        # 展平
        x = x.view(-1, 128 * 3 * 3)
        
        # 全连接层
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x


class DLOCRExtractor:
    """深度学习 OCR 提取器"""
    
    def __init__(
        self,
        model_path: str = "models/digit_ocr_model.pth",
        coordinates_path: str = "models/coordinates.json"
    ):
        """
        初始化深度学习 OCR 提取器
        
        Args:
            model_path: 模型文件路径
            coordinates_path: 坐标定义文件路径
        
        Raises:
            OCRError: 模型加载失败
        """
        if not TORCH_AVAILABLE:
            raise OCRError(
                "PyTorch 未安装。深度学习 OCR 功能不可用。\n"
                "请运行: pip install torch torchvision"
            )
        
        self.model_path = Path(model_path)
        self.coordinates_path = Path(coordinates_path)
        
        # 检查文件是否存在
        if not self.model_path.exists():
            raise OCRError(f"模型文件不存在: {self.model_path}")
        
        if not self.coordinates_path.exists():
            raise OCRError(f"坐标文件不存在: {self.coordinates_path}")
        
        # 加载坐标定义
        self.coordinates = self._load_coordinates()
        
        # 检测设备
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        # 加载模型
        self.model = self._load_model()
        
        logger.info(f"深度学习 OCR 提取器初始化成功 (设备: {self.device})")
    
    def _load_coordinates(self) -> Dict:
        """加载坐标定义"""
        with open(self.coordinates_path, 'r', encoding='utf-8') as f:
            coords = json.load(f)
        
        # 转换格式
        formatted_coords = {}
        for key, value in coords.items():
            if isinstance(value, list):
                # [x, y, w, h] 格式
                formatted_coords[key] = {
                    "x": value[0],
                    "y": value[1],
                    "width": value[2],
                    "height": value[3]
                }
            else:
                # 已经是字典格式
                formatted_coords[key] = value
        
        logger.info(f"加载了 {len(formatted_coords)} 个坐标定义")
        return formatted_coords
    
    def _load_model(self):
        """加载训练好的模型"""
        model = DigitCNN()
        checkpoint = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        
        logger.info(f"模型加载成功: {self.model_path}")
        return model
    
    def _preprocess_digit(self, image: np.ndarray, x: int, y: int, w: int, h: int, padding: int = 5) -> Optional[torch.Tensor]:
        """
        预处理数字图像区域
        
        Args:
            image: 原始图像
            x, y, w, h: 区域坐标
            padding: 边距
        
        Returns:
            预处理后的 tensor
        """
        # 添加 padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.shape[1], x + w + padding)
        y2 = min(image.shape[0], y + h + padding)
        
        # 裁剪
        digit_img = image[y1:y2, x1:x2]
        
        if digit_img.size == 0:
            return None
        
        # 转换为灰度图
        if len(digit_img.shape) == 3:
            digit_img = cv2.cvtColor(digit_img, cv2.COLOR_BGR2GRAY)
        
        # 调整大小到 28x28
        digit_img = cv2.resize(digit_img, (28, 28), interpolation=cv2.INTER_AREA)
        
        # 二值化
        _, digit_img = cv2.threshold(digit_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 归一化
        digit_img = digit_img.astype(np.float32) / 255.0
        
        # 转换为 tensor
        digit_tensor = torch.from_numpy(digit_img).unsqueeze(0).unsqueeze(0)
        
        return digit_tensor
    
    def _predict(self, image_tensor: torch.Tensor) -> float:
        """
        预测数值
        
        Args:
            image_tensor: 预处理后的图像 tensor
        
        Returns:
            预测的数值
        """
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            output = self.model(image_tensor)
            value = output.item()
        
        return value
    
    def extract_from_image(self, image_path: Path) -> pd.DataFrame:
        """
        从图像中提取数据
        
        Args:
            image_path: 图像文件路径
        
        Returns:
            包含 item_name、value、unit 的 DataFrame
        
        Raises:
            FileNotFoundError: 图像文件不存在
            OCRError: 提取失败
        """
        if not image_path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        logger.info(f"开始提取图像: {image_path}")
        
        try:
            # 加载图像
            image = cv2.imread(str(image_path))
            if image is None:
                raise OCRError(f"无法加载图像: {image_path}")
            
            # 提取每个单元格的数据
            results = []
            
            for cell_id, coord in self.coordinates.items():
                x = coord['x']
                y = coord['y']
                w = coord['width']
                h = coord['height']
                
                # 预处理
                image_tensor = self._preprocess_digit(image, x, y, w, h)
                if image_tensor is None:
                    logger.warning(f"无法预处理单元格: {cell_id}")
                    continue
                
                # 预测
                pred_value = self._predict(image_tensor)
                
                # 确定单位
                if 'Current' in cell_id:
                    unit = 'A'
                    # Current 列保留一位小数
                    pred_value = round(pred_value, 1)
                else:
                    unit = '°C'
                    # 温度值取整
                    pred_value = round(pred_value)
                
                results.append({
                    'item_name': cell_id,
                    'value': pred_value,
                    'unit': unit
                })
            
            df = pd.DataFrame(results)
            logger.info(f"成功提取 {len(df)} 条数据")
            
            return df
        
        except Exception as e:
            logger.error(f"深度学习 OCR 提取失败: {e}")
            raise OCRError(f"提取失败: {str(e)}")
    
    @staticmethod
    def is_available() -> bool:
        """检查深度学习 OCR 是否可用"""
        if not TORCH_AVAILABLE:
            return False
        
        model_path = Path("models/digit_ocr_model.pth")
        coordinates_path = Path("models/coordinates.json")
        
        return model_path.exists() and coordinates_path.exists()
