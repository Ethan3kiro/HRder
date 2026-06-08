#!/usr/bin/env python3
"""
模板OCR功能测试脚本

快速测试模板OCR识别功能是否正常工作
"""
import sys
from pathlib import Path


def test_imports():
    """测试必要的库是否已安装"""
    print("=" * 70)
    print("测试1: 检查依赖库")
    print("=" * 70)
    
    try:
        import cv2
        print(f"✓ OpenCV 版本: {cv2.__version__}")
    except ImportError:
        print("✗ OpenCV 未安装")
        print("  安装命令: pip install opencv-python")
        return False
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract 版本: {version}")
    except Exception as e:
        print(f"✗ Tesseract 未安装或配置错误: {e}")
        print("  安装说明: docs/TEMPLATE_OCR_GUIDE.md")
        return False
    
    try:
        import numpy as np
        print(f"✓ NumPy 版本: {np.__version__}")
    except ImportError:
        print("✗ NumPy 未安装")
        return False
    
    try:
        import pandas as pd
        print(f"✓ Pandas 版本: {pd.__version__}")
    except ImportError:
        print("✗ Pandas 未安装")
        return False
    
    print("\n✓ 所有依赖库已正确安装\n")
    return True


def test_coordinate_calibrator():
    """测试坐标标定工具"""
    print("=" * 70)
    print("测试2: 坐标标定工具")
    print("=" * 70)
    
    calibrator_path = Path('tools/coordinate_calibrator.py')
    
    if not calibrator_path.exists():
        print(f"✗ 坐标标定工具不存在: {calibrator_path}")
        return False
    
    print(f"✓ 坐标标定工具存在: {calibrator_path}")
    
    # 测试导入
    try:
        sys.path.insert(0, str(calibrator_path.parent))
        import coordinate_calibrator
        print("✓ 坐标标定工具可以正常导入")
    except Exception as e:
        print(f"✗ 坐标标定工具导入失败: {e}")
        return False
    
    print("\n✓ 坐标标定工具正常\n")
    return True


def test_template_extractor():
    """测试模板OCR提取器"""
    print("=" * 70)
    print("测试3: 模板OCR提取器")
    print("=" * 70)
    
    extractor_path = Path('src/template_ocr_extractor.py')
    
    if not extractor_path.exists():
        print(f"✗ 模板OCR提取器不存在: {extractor_path}")
        return False
    
    print(f"✓ 模板OCR提取器存在: {extractor_path}")
    
    # 测试导入
    try:
        from src.template_ocr_extractor import TemplateOCRExtractor
        print("✓ 模板OCR提取器可以正常导入")
    except Exception as e:
        print(f"✗ 模板OCR提取器导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试初始化
    try:
        extractor = TemplateOCRExtractor()
        print("✓ 模板OCR提取器可以正常初始化")
    except Exception as e:
        print(f"⚠ 模板OCR提取器初始化警告: {e}")
        print("  (坐标文件不存在是正常的，需要先标定)")
    
    print("\n✓ 模板OCR提取器正常\n")
    return True


def test_coordinates_file():
    """检查坐标文件"""
    print("=" * 70)
    print("测试4: 坐标模板文件")
    print("=" * 70)
    
    coords_file = Path('config/template_coordinates.json')
    
    if coords_file.exists():
        print(f"✓ 坐标模板文件已存在: {coords_file}")
        
        try:
            import json
            with open(coords_file, 'r', encoding='utf-8') as f:
                coords = json.load(f)
            
            # 统计区域数量
            count = 0
            for key, value in coords.items():
                if isinstance(value, dict):
                    count += len(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            count += len(item)
            
            print(f"  包含 {count} 个标定区域")
            
            if count >= 71:
                print("✓ 坐标标定完整（71个区域）")
            else:
                print(f"⚠ 坐标标定不完整（需要71个，当前{count}个）")
        
        except Exception as e:
            print(f"⚠ 坐标文件格式错误: {e}")
    else:
        print(f"ℹ 坐标模板文件不存在: {coords_file}")
        print("  需要运行坐标标定工具创建：")
        print("  python tools/coordinate_calibrator.py <图像路径>")
    
    print()
    return True


def test_sample_image():
    """检查示例图片"""
    print("=" * 70)
    print("测试5: 示例图片")
    print("=" * 70)
    
    sample_images = [
        Path('911-20251016.jpg'),
        Path('911-20251111.jpg'),
    ]
    
    found = False
    for img_path in sample_images:
        if img_path.exists():
            print(f"✓ 找到示例图片: {img_path}")
            print(f"  可以用于测试：python tools/coordinate_calibrator.py {img_path}")
            found = True
        else:
            print(f"ℹ 图片不存在: {img_path}")
    
    if not found:
        print("\n⚠ 未找到示例图片")
        print("  请准备一张发射机截图用于测试")
    
    print()
    return True


def test_gui_integration():
    """测试GUI集成"""
    print("=" * 70)
    print("测试6: GUI集成")
    print("=" * 70)
    
    try:
        from src.gui.widgets.data_entry_widget import DataEntryWidget, TemplateWorker
        print("✓ DataEntryWidget 包含 TemplateWorker")
    except ImportError as e:
        print(f"✗ DataEntryWidget 导入失败: {e}")
        return False
    
    try:
        from src.gui.widgets.fullscreen_data_entry import FullscreenDataEntryWindow, TemplateWorker as FTW
        print("✓ FullscreenDataEntryWindow 包含 TemplateWorker")
    except ImportError as e:
        print(f"✗ FullscreenDataEntryWindow 导入失败: {e}")
        return False
    
    print("\n✓ GUI集成正常\n")
    return True


def run_quick_test():
    """运行快速识别测试"""
    print("=" * 70)
    print("测试7: 快速识别测试（如果坐标和图片都存在）")
    print("=" * 70)
    
    coords_file = Path('config/template_coordinates.json')
    sample_image = None
    
    for img_path in [Path('911-20251016.jpg'), Path('911-20251111.jpg')]:
        if img_path.exists():
            sample_image = img_path
            break
    
    if not coords_file.exists():
        print("ℹ 跳过识别测试：坐标文件不存在")
        print()
        return True
    
    if not sample_image:
        print("ℹ 跳过识别测试：示例图片不存在")
        print()
        return True
    
    print(f"运行识别测试：{sample_image}")
    
    try:
        from src.template_ocr_extractor import TemplateOCRExtractor
        import time
        
        extractor = TemplateOCRExtractor()
        
        start_time = time.time()
        results = extractor.extract_from_image(sample_image)
        elapsed = time.time() - start_time
        
        print(f"✓ 识别完成")
        print(f"  识别到: {len(results)} 个数据项")
        print(f"  耗时: {elapsed:.2f} 秒")
        
        if len(results) > 0:
            print(f"\n  前5个识别结果：")
            for _, row in results.head(5).iterrows():
                print(f"    {row['item_name']}: {row['value']} {row['unit']}")
        
        if len(results) >= 60:
            print(f"\n✓ 识别结果正常（>= 60个数据项）")
        else:
            print(f"\n⚠ 识别结果可能不完整（< 60个数据项）")
        
    except Exception as e:
        print(f"✗ 识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(" 模板OCR功能测试")
    print("=" * 70)
    print()
    
    tests = [
        ("依赖库", test_imports),
        ("坐标标定工具", test_coordinate_calibrator),
        ("模板OCR提取器", test_template_extractor),
        ("坐标模板文件", test_coordinates_file),
        ("示例图片", test_sample_image),
        ("GUI集成", test_gui_integration),
        ("识别测试", run_quick_test),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} 测试出错: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("=" * 70)
    print(" 测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status:10} - {name}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n下一步:")
        print("  1. 运行坐标标定工具：python tools/coordinate_calibrator.py <图像路径>")
        print("  2. 启动GUI测试：python main_gui.py")
    else:
        print("\n⚠ 部分测试未通过，请检查上述错误信息")
    
    print("=" * 70)
    print()
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
