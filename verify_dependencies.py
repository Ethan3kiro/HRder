#!/usr/bin/env python3
"""
依赖验证脚本
检查所有必需的依赖是否正确安装
"""

import sys
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    print("检查 Python 版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (需要 3.9+)")
        return False


def check_package(package_name, import_name=None):
    """检查 Python 包是否安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"  ✓ {package_name}")
        return True
    except ImportError:
        print(f"  ✗ {package_name} (未安装)")
        return False


def check_tesseract():
    """检查 Tesseract OCR"""
    print("检查 Tesseract OCR...")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"  ✓ Tesseract {version}")
        return True
    except Exception as e:
        print(f"  ✗ Tesseract (未安装或配置错误)")
        print(f"     错误: {e}")
        return False


def check_pytorch():
    """检查 PyTorch"""
    print("检查 PyTorch (可选)...")
    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
        
        # 检查可用设备
        if torch.cuda.is_available():
            print(f"     GPU (CUDA) 可用")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print(f"     GPU (MPS) 可用")
        else:
            print(f"     仅 CPU 可用")
        
        return True
    except ImportError:
        print(f"  ⚠ PyTorch (未安装，深度学习功能不可用)")
        return False


def check_model_files():
    """检查模型文件"""
    print("检查模型文件...")
    model_path = Path("models/digit_ocr_model.pth")
    coord_path = Path("models/coordinates.json")
    
    model_exists = model_path.exists()
    coord_exists = coord_path.exists()
    
    if model_exists:
        print(f"  ✓ 模型文件存在")
    else:
        print(f"  ⚠ 模型文件不存在 (深度学习功能不可用)")
    
    if coord_exists:
        print(f"  ✓ 坐标文件存在")
    else:
        print(f"  ⚠ 坐标文件不存在 (深度学习功能不可用)")
    
    return model_exists and coord_exists


def main():
    """主函数"""
    print("=" * 60)
    print("依赖验证")
    print("=" * 60)
    print()
    
    results = []
    
    # 检查 Python 版本
    results.append(("Python 版本", check_python_version()))
    print()
    
    # 检查核心依赖
    print("检查核心依赖...")
    results.append(("pandas", check_package("pandas")))
    results.append(("numpy", check_package("numpy")))
    results.append(("Pillow", check_package("Pillow", "PIL")))
    results.append(("opencv-python", check_package("opencv-python", "cv2")))
    results.append(("pytesseract", check_package("pytesseract")))
    print()
    
    # 检查 GUI 依赖
    print("检查 GUI 依赖...")
    results.append(("PyQt6", check_package("PyQt6")))
    results.append(("matplotlib", check_package("matplotlib")))
    print()
    
    # 检查 Tesseract
    results.append(("Tesseract OCR", check_tesseract()))
    print()
    
    # 检查 PyTorch (可选)
    pytorch_ok = check_pytorch()
    print()
    
    # 检查模型文件 (可选)
    model_ok = check_model_files()
    print()
    
    # 总结
    print("=" * 60)
    print("总结")
    print("=" * 60)
    
    required_ok = all(ok for name, ok in results)
    
    if required_ok:
        print("✓ 所有必需依赖已安装")
    else:
        print("✗ 部分必需依赖未安装")
        print()
        print("未安装的依赖:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
        print()
        print("请运行以下命令安装:")
        print("  pip install -r requirements.txt -r requirements-gui.txt")
    
    print()
    
    # 可选功能
    if not pytorch_ok:
        print("⚠ PyTorch 未安装 (深度学习功能不可用)")
        print("  如需使用深度学习模型，请运行:")
        print("  pip install -r requirements-training.txt")
        print()
    
    if not model_ok:
        print("⚠ 模型文件不存在 (深度学习功能不可用)")
        print("  如需使用深度学习模型，请参考 TRAINING.md 训练模型")
        print()
    
    # 返回状态
    if required_ok:
        print("✓ 系统可以正常运行")
        return 0
    else:
        print("✗ 请先安装缺失的依赖")
        return 1


if __name__ == "__main__":
    sys.exit(main())
