"""
测试智谱AI GLM-4V-Flash API
"""

import requests
import json
import base64
from pathlib import Path

# API 配置
API_KEY = "请填入您的智谱AI API密钥"  # 从 https://open.bigmodel.cn/ 获取
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4v-flash"  # 完全免费的视觉模型

def encode_image(image_path):
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_zhipu_api(image_path):
    """测试智谱AI API"""
    
    # 读取并编码图片
    base64_image = encode_image(image_path)
    
    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张发射机监控截图中的所有数字数据。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    print(f"正在测试智谱AI GLM-4V-Flash...")
    print(f"模型: {MODEL}")
    print(f"图片: {image_path}")
    print(f"API URL: {API_URL}")
    print("-" * 50)
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ API 调用成功！")
            print("\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 提取识别结果
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print("\n识别结果:")
                print(content)
                
                # 显示 token 使用情况
                if 'usage' in result:
                    usage = result['usage']
                    print(f"\nToken 使用情况:")
                    print(f"  输入: {usage.get('prompt_tokens', 0)}")
                    print(f"  输出: {usage.get('completion_tokens', 0)}")
                    print(f"  总计: {usage.get('total_tokens', 0)}")
                    print(f"\n💰 费用: 免费！GLM-4V-Flash 完全免费使用")
        else:
            print(f"\n❌ API 调用失败")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    # 使用示例图片测试
    test_image = "911-20251016.jpg"
    
    if not Path(test_image).exists():
        print(f"❌ 图片文件不存在: {test_image}")
        print("请将测试图片放在当前目录，或修改 test_image 变量")
    else:
        test_zhipu_api(test_image)
