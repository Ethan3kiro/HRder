#!/usr/bin/env python3
"""
测试阿里百炼 API 识别功能
"""

import sys
from pathlib import Path
import json

def test_api_config():
    """测试 API 配置加载"""
    print("=" * 60)
    print("测试 1: 加载 API 配置")
    print("=" * 60)
    
    try:
        from src.api_ocr_extractor import load_api_config_from_file, APIOCRExtractor
        
        config_path = Path('config/api_config.json')
        if not config_path.exists():
            print(f"✗ 配置文件不存在: {config_path}")
            return False
        
        api_config = load_api_config_from_file(config_path)
        if not api_config:
            print("✗ 加载配置失败")
            return False
        
        print(f"✓ 成功加载配置")
        print(f"  提供商: {api_config.provider}")
        print(f"  API URL: {api_config.api_url}")
        print(f"  API Key: {api_config.api_key[:20]}...")
        
        # 创建提取器
        extractor = APIOCRExtractor(api_config)
        print(f"✓ 成功创建 API OCR 提取器")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_call():
    """测试 API 调用"""
    print("\n" + "=" * 60)
    print("测试 2: 调用阿里百炼 API")
    print("=" * 60)
    
    try:
        from src.api_ocr_extractor import load_api_config_from_file, APIOCRExtractor
        
        # 加载配置
        config_path = Path('config/api_config.json')
        api_config = load_api_config_from_file(config_path)
        extractor = APIOCRExtractor(api_config)
        
        # 查找测试图像
        test_images = [
            Path('911-20251016.jpg'),
            Path('911-20251111.jpg'),
            Path('examples/sample_images/sample_transmitter_1.png'),
            Path('examples/sample_images/sample_transmitter_2.png'),
        ]
        
        test_image = None
        for img in test_images:
            if img.exists():
                test_image = img
                break
        
        if not test_image:
            print("✗ 未找到测试图像")
            print("  请确保以下任一图像存在：")
            for img in test_images:
                print(f"    - {img}")
            return False
        
        print(f"✓ 使用测试图像: {test_image}")
        print(f"⏳ 正在调用 API（这可能需要 10-30 秒）...")
        
        # 调用 API
        result = extractor.extract_from_image(test_image)
        
        print(f"✓ API 调用成功！")
        print(f"\n识别结果：")
        print(f"  识别到 {len(result)} 个数据项")
        
        if len(result) > 0:
            print(f"\n前 5 个数据项：")
            for i, row in result.head(5).iterrows():
                print(f"  {i+1}. {row['item_name']}: {row['value']} {row['unit']}")
        
        # 保存完整结果
        output_file = Path('test_api_result.json')
        result.to_json(output_file, orient='records', indent=2, force_ascii=False)
        print(f"\n✓ 完整结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ API 调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("阿里百炼 API 测试")
    print("=" * 60)
    
    # 测试 1: 配置加载
    if not test_api_config():
        print("\n❌ 配置加载失败，无法继续测试")
        return 1
    
    # 测试 2: API 调用
    if not test_api_call():
        print("\n❌ API 调用失败")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 查看识别结果: cat test_api_result.json")
    print("2. 在 GUI 中使用: 启动程序，点击 '🌐 API 识别' 按钮")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
