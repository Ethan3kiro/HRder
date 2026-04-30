"""
API OCR 提取器 - 调用第三方 API 进行图像识别
支持多种 API 提供商
"""

import json
import base64
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from PIL import Image
import io


class APIConfig:
    """API 配置类"""
    
    def __init__(self, provider: str, api_key: str, api_url: str = None, **kwargs):
        """
        初始化 API 配置
        
        Args:
            provider: API 提供商 ('openai', 'baidu', 'aliyun', 'custom')
            api_key: API 密钥
            api_url: API 地址（可选，某些提供商需要）
            **kwargs: 其他配置参数
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_url = api_url
        self.extra_params = kwargs


class APIOCRExtractor:
    """API OCR 提取器"""
    
    def __init__(self, config: APIConfig):
        """
        初始化 API OCR 提取器
        
        Args:
            config: API 配置对象
        """
        self.config = config
        
        # 根据提供商设置默认 URL
        if not self.config.api_url:
            self.config.api_url = self._get_default_url()
    
    def _get_default_url(self) -> str:
        """获取默认 API URL"""
        default_urls = {
            'openai': 'https://api.openai.com/v1/chat/completions',
            'baidu': 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic',
            'aliyun': 'https://ocrapi-advanced.cn-shanghai.aliyuncs.com',
            'custom': ''
        }
        return default_urls.get(self.config.provider, '')
    
    def extract_from_image(self, image_path: Path) -> pd.DataFrame:
        """
        从图像中提取数据
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            包含提取数据的 DataFrame
        """
        # 读取并编码图像
        image_base64 = self._encode_image(image_path)
        
        # 根据提供商调用相应的 API
        if self.config.provider == 'openai':
            result = self._call_openai_api(image_base64)
        elif self.config.provider == 'baidu':
            result = self._call_baidu_api(image_base64)
        elif self.config.provider == 'aliyun':
            result = self._call_aliyun_api(image_base64)
        elif self.config.provider == 'custom':
            result = self._call_custom_api(image_base64)
        else:
            raise ValueError(f"不支持的 API 提供商: {self.config.provider}")
        
        # 解析结果为 DataFrame
        return self._parse_result(result)
    
    def _encode_image(self, image_path: Path) -> str:
        """
        将图像编码为 base64，并进行压缩优化
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            base64 编码的图像字符串
        """
        try:
            from PIL import Image
            import io
            
            # 打开图像
            img = Image.open(image_path)
            
            # 如果是 RGBA，转换为 RGB
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # 计算缩放比例（限制最大边长）
            width, height = img.size
            max_dimension = 1024  # 最大边长
            
            if max(width, height) > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 压缩图像
            buffer = io.BytesIO()
            quality = 85
            max_size_kb = 200  # 最大文件大小
            
            while quality > 20:
                buffer.seek(0)
                buffer.truncate()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                size_kb = len(buffer.getvalue()) / 1024
                
                if size_kb <= max_size_kb:
                    break
                
                quality -= 5
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except ImportError:
            # 如果 PIL 不可用，直接读取文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    
    def _call_openai_api(self, image_base64: str) -> Dict[str, Any]:
        """
        调用 OpenAI GPT-4 Vision API
        
        Args:
            image_base64: base64 编码的图像
            
        Returns:
            API 响应结果
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        }
        
        # 构建提示词
        prompt = """请识别这张发射机截图中的所有数据。

图像包含以下数据项：
1. COMBINER ISO TEMPERATURES (7项): AZ, BZ, CZ, DZ, AB, CD, ABCD
2. Z-Plane 数据 (64项): 4个模块(A,B,C,D) × 8行 × 2列(Current和ISO Temp)

请以 JSON 格式返回识别结果，格式如下：
{
  "data": [
    {"item_name": "AZ", "value": 30.0, "unit": "°C"},
    {"item_name": "Z-Plane A-Current-1", "value": 7.2, "unit": "A"},
    {"item_name": "Z-Plane A-ISO Temp-1", "value": 48.0, "unit": "°C"},
    ...
  ]
}

注意：
- 只返回 JSON 数据，不要其他说明
- value 必须是数字
- item_name 必须严格按照上述格式
- 如果某个数据无法识别，可以省略该项"""
        
        payload = {
            'model': self.config.extra_params.get('model', 'gpt-4-vision-preview'),
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_base64}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': self.config.extra_params.get('max_tokens', 2000)
        }
        
        response = requests.post(
            self.config.api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        return response.json()
    
    def _call_baidu_api(self, image_base64: str) -> Dict[str, Any]:
        """
        调用百度 OCR API
        
        Args:
            image_base64: base64 编码的图像
            
        Returns:
            API 响应结果
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        params = {
            'access_token': self.config.api_key
        }
        
        data = {
            'image': image_base64
        }
        
        response = requests.post(
            self.config.api_url,
            headers=headers,
            params=params,
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def _call_aliyun_api(self, image_base64: str) -> Dict[str, Any]:
        """
        调用阿里云 OCR API
        
        Args:
            image_base64: base64 编码的图像
            
        Returns:
            API 响应结果
        """
        # 阿里云 API 实现（需要根据实际 API 文档调整）
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'APPCODE {self.config.api_key}'
        }
        
        payload = {
            'image': image_base64
        }
        
        response = requests.post(
            self.config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def _call_custom_api(self, image_base64: str) -> Dict[str, Any]:
        """
        调用自定义 API
        
        Args:
            image_base64: base64 编码的图像
            
        Returns:
            API 响应结果
        """
        headers = self.config.extra_params.get('headers', {
            'Content-Type': 'application/json'
        })
        
        # 如果配置中有 API key，添加到 headers
        if self.config.api_key:
            auth_header = self.config.extra_params.get('auth_header', 'Authorization')
            auth_prefix = self.config.extra_params.get('auth_prefix', 'Bearer')
            headers[auth_header] = f'{auth_prefix} {self.config.api_key}'
        
        # 构建请求体
        payload = self.config.extra_params.get('payload_template', {
            'image': image_base64
        })
        
        # 替换占位符
        payload_str = json.dumps(payload).replace('{{image}}', image_base64)
        payload = json.loads(payload_str)
        
        response = requests.post(
            self.config.api_url,
            headers=headers,
            json=payload,
            timeout=self.config.extra_params.get('timeout', 30)
        )
        
        response.raise_for_status()
        return response.json()
    
    def _parse_result(self, result: Dict[str, Any]) -> pd.DataFrame:
        """
        解析 API 返回结果为 DataFrame
        
        Args:
            result: API 返回的原始结果
            
        Returns:
            包含提取数据的 DataFrame
        """
        if self.config.provider == 'openai':
            return self._parse_openai_result(result)
        elif self.config.provider == 'baidu':
            return self._parse_baidu_result(result)
        elif self.config.provider == 'aliyun':
            return self._parse_aliyun_result(result)
        elif self.config.provider == 'custom':
            return self._parse_custom_result(result)
        else:
            raise ValueError(f"不支持的 API 提供商: {self.config.provider}")
    
    def _parse_openai_result(self, result: Dict[str, Any]) -> pd.DataFrame:
        """解析 OpenAI API 结果"""
        try:
            # 提取响应内容
            content = result['choices'][0]['message']['content']
            
            # 尝试提取 JSON（可能包含在 markdown 代码块中）
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            
            # 解析 JSON
            data = json.loads(content)
            
            # 转换为 DataFrame
            if 'data' in data:
                return pd.DataFrame(data['data'])
            else:
                return pd.DataFrame(data)
                
        except Exception as e:
            raise ValueError(f"解析 OpenAI 结果失败: {str(e)}\n原始内容: {result}")
    
    def _parse_baidu_result(self, result: Dict[str, Any]) -> pd.DataFrame:
        """解析百度 OCR 结果"""
        # 百度 OCR 返回的是文字识别结果，需要进一步处理
        # 这里提供一个基础实现，实际使用时可能需要根据具体格式调整
        try:
            words_result = result.get('words_result', [])
            
            # 简单的文本解析逻辑（需要根据实际情况调整）
            data_list = []
            for item in words_result:
                text = item.get('words', '')
                # 这里需要实现具体的解析逻辑
                # 例如：识别 "AZ: 30.0°C" 这样的格式
                # 这只是示例，实际需要更复杂的解析
                pass
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            raise ValueError(f"解析百度 OCR 结果失败: {str(e)}")
    
    def _parse_aliyun_result(self, result: Dict[str, Any]) -> pd.DataFrame:
        """解析阿里云 OCR 结果"""
        # 类似百度 OCR，需要根据实际 API 返回格式实现
        try:
            # 示例实现
            data_list = []
            # 实现具体的解析逻辑
            return pd.DataFrame(data_list)
            
        except Exception as e:
            raise ValueError(f"解析阿里云 OCR 结果失败: {str(e)}")
    
    def _parse_custom_result(self, result: Dict[str, Any]) -> pd.DataFrame:
        """解析自定义 API 结果"""
        try:
            # 从配置中获取数据路径
            data_path = self.config.extra_params.get('data_path', 'data')
            
            # 支持嵌套路径，如 'choices.0.message.content'
            data = result
            for key in data_path.split('.'):
                if key.isdigit():
                    # 处理数组索引
                    data = data[int(key)]
                else:
                    data = data[key]
            
            # 如果数据是字符串，尝试解析为 JSON
            if isinstance(data, str):
                # 尝试提取 JSON（可能包含在 markdown 代码块中）
                if '```json' in data:
                    json_start = data.find('```json') + 7
                    json_end = data.find('```', json_start)
                    data = data[json_start:json_end].strip()
                elif '```' in data:
                    json_start = data.find('```') + 3
                    json_end = data.find('```', json_start)
                    data = data[json_start:json_end].strip()
                
                # 解析 JSON 字符串
                data = json.loads(data)
            
            # 如果数据是字典且包含 'data' 键，提取 data
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            
            # 转换为 DataFrame
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                raise ValueError(f"不支持的数据格式: {type(data)}")
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            raise ValueError(
                f"解析自定义 API 结果失败: {str(e)}\n\n"
                f"详细错误:\n{error_detail}\n\n"
                f"原始结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
            )


def load_api_config_from_file(config_path: Path = Path('config/api_config.json')) -> Optional[APIConfig]:
    """
    从配置文件加载 API 配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        APIConfig 对象，如果文件不存在则返回 None
    """
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return APIConfig(
            provider=config_data['provider'],
            api_key=config_data['api_key'],
            api_url=config_data.get('api_url'),
            **config_data.get('extra_params', {})
        )
    except Exception as e:
        print(f"加载 API 配置失败: {str(e)}")
        return None


def create_default_config_file(config_path: Path = Path('config/api_config.json')):
    """
    创建默认配置文件模板
    
    Args:
        config_path: 配置文件路径
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "_comment": "API OCR 配置文件",
        "provider": "openai",
        "api_key": "your-api-key-here",
        "api_url": "",
        "extra_params": {
            "model": "gpt-4-vision-preview",
            "max_tokens": 2000
        },
        "_examples": {
            "openai": {
                "provider": "openai",
                "api_key": "sk-...",
                "extra_params": {
                    "model": "gpt-4-vision-preview",
                    "max_tokens": 2000
                }
            },
            "custom": {
                "provider": "custom",
                "api_key": "your-api-key",
                "api_url": "https://your-api.com/ocr",
                "extra_params": {
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "auth_header": "Authorization",
                    "auth_prefix": "Bearer",
                    "payload_template": {
                        "image": "{{image}}",
                        "options": {
                            "format": "json"
                        }
                    },
                    "data_path": "result.data",
                    "timeout": 30
                }
            }
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"已创建默认配置文件: {config_path}")
    print("请编辑此文件，填入您的 API 密钥和配置")
