#!/usr/bin/env python3
"""
简单测试阿里百炼 API 连接
"""

import requests
import json
import base64

# API 配置
API_KEY = "sk-9f235e80bee840f39da5257ac4f683a9"
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# 测试 1: 纯文本请求（不带图像）
print("测试 1: 纯文本请求")
print("=" * 60)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "qwen-plus",  # 先用文本模型测试
    "messages": [
        {
            "role": "user",
            "content": "你好，请回复'测试成功'"
        }
    ]
}

try:
    print(f"正在连接: {API_URL}")
    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✓ API 连接成功！")
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"✗ API 返回错误")
        print(f"响应: {response.text}")
        
except Exception as e:
    print(f"✗ 连接失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("如果上面的测试成功，说明 API 密钥和端点正确")
print("如果失败，可能需要：")
print("1. 检查 API 密钥是否正确")
print("2. 检查网络连接")
print("3. 检查 API 端点 URL")
print("4. 查看阿里百炼控制台的 API 文档")
