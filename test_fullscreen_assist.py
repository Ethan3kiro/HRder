#!/usr/bin/env python3
"""
测试全屏模式辅助录入功能修复
"""

import sys
from pathlib import Path

def test_imports():
    """测试导入是否正常"""
    print("测试 1: 检查导入...")
    try:
        from src.gui.widgets.fullscreen_data_entry import FullscreenDataEntryWindow, OCRWorker
        print("✓ 成功导入 FullscreenDataEntryWindow 和 OCRWorker")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_ocr_worker_class():
    """测试 OCRWorker 类是否正确定义"""
    print("\n测试 2: 检查 OCRWorker 类...")
    try:
        from src.gui.widgets.fullscreen_data_entry import OCRWorker
        from PyQt6.QtCore import QThread
        
        # 检查是否是 QThread 的子类
        if issubclass(OCRWorker, QThread):
            print("✓ OCRWorker 正确继承自 QThread")
        else:
            print("✗ OCRWorker 未正确继承 QThread")
            return False
        
        # 检查必要的信号
        required_signals = ['finished', 'error', 'progress']
        for signal_name in required_signals:
            if hasattr(OCRWorker, signal_name):
                print(f"✓ OCRWorker 有 {signal_name} 信号")
            else:
                print(f"✗ OCRWorker 缺少 {signal_name} 信号")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def test_fullscreen_methods():
    """测试全屏窗口的关键方法"""
    print("\n测试 3: 检查全屏窗口方法...")
    try:
        from src.gui.widgets.fullscreen_data_entry import FullscreenDataEntryWindow
        
        # 检查必要的方法
        required_methods = [
            'start_assisted_entry',
            'on_assisted_entry_finished',
            'on_assisted_entry_error',
            'on_assisted_entry_progress'
        ]
        
        for method_name in required_methods:
            if hasattr(FullscreenDataEntryWindow, method_name):
                print(f"✓ FullscreenDataEntryWindow 有 {method_name} 方法")
            else:
                print(f"✗ FullscreenDataEntryWindow 缺少 {method_name} 方法")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def test_code_consistency():
    """测试代码一致性"""
    print("\n测试 4: 检查代码一致性...")
    try:
        # 读取文件内容
        with open('src/gui/widgets/fullscreen_data_entry.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否还有错误的导入
        if 'from .data_entry_widget import DLOCRWorker' in content:
            print("✗ 仍然存在错误的 DLOCRWorker 导入")
            return False
        else:
            print("✓ 没有错误的 DLOCRWorker 导入")
        
        # 检查是否定义了 OCRWorker
        if 'class OCRWorker(QThread):' in content:
            print("✓ 正确定义了 OCRWorker 类")
        else:
            print("✗ 未找到 OCRWorker 类定义")
            return False
        
        # 检查是否使用了正确的类
        if 'self.ocr_worker = OCRWorker(self.dl_ocr_extractor, file_path)' in content:
            print("✓ 正确使用 OCRWorker 类")
        else:
            print("✗ 未正确使用 OCRWorker 类")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("全屏模式辅助录入功能修复测试")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_ocr_worker_class,
        test_fullscreen_methods,
        test_code_consistency
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if all(results):
        print("\n✓ 所有测试通过！全屏模式辅助录入功能已修复。")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查上述错误。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
