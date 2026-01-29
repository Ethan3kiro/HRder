#!/usr/bin/env python3
"""
测试阿里百炼 API 图像识别
"""

import requests
import json
import base64
from pathlib import Path
from PIL import Image
import io

# API 配置
API_KEY = "sk-9f235e80bee840f39da5257ac4f683a9"
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

def compress_image(image_path, max_size_kb=200):
    """压缩图像到指定大小以下"""
    img = Image.open(image_path)
    
    # 如果是 RGBA，转换为 RGB
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # 计算缩放比例
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
        print(f"图像已缩放: {width}x{height} -> {new_width}x{new_height}")
    
    # 保存为 JPEG 并压缩
    buffer = io.BytesIO()
    quality = 85
    
    while quality > 20:
        buffer.seek(0)
        buffer.truncate()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        size_kb = len(buffer.getvalue()) / 1024
        
        if size_kb <= max_size_kb:
            break
        
        quality -= 5
    
    print(f"图像已压缩: {size_kb:.1f} KB (质量: {quality})")
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# 测试图像识别
print("测试: 图像识别")
print("=" * 60)

# 查找测试图像
test_image = Path('911-20251016.jpg')
if not test_image.exists():
    print("✗ 测试图像不存在")
    exit(1)

print(f"✓ 使用测试图像: {test_image}")

# 压缩并编码图像
print("正在压缩图像...")
image_base64 = compress_image(test_image, max_size_kb=150)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "qwen-vl-max",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请识别这张图片中的所有数字和文字，以 JSON 格式返回。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
}

try:
    print(f"正在调用 API...")
    print(f"请求大小: {len(json.dumps(payload)) / 1024:.1f} KB")
    
    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✓ API 调用成功！")
        
        # 提取内容
        content = result['choices'][0]['message']['content']
        print(f"\n识别结果:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
        # 保存结果
        with open('test_api_response.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n完整响应已保存到: test_api_response.json")
        
    else:
        print(f"✗ API 返回错误")
        print(f"响应: {response.text}")
        
except Exception as e:
    print(f"✗ 调用失败: {str(e)}")
    import traceback
    traceback.print_exc()
