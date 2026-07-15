#!/usr/bin/env python3
"""
测试模板OCR对话框的新布局
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication


def test_template_dialog():
    """测试模板OCR对话框"""
    print("=" * 70)
    print("测试模板OCR对话框 - 新左右布局")
    print("=" * 70)
    print()
    
    # 检查测试图片
    test_image = '911-20251016.jpg'
    if not Path(test_image).exists():
        print(f"❌ 测试图片不存在: {test_image}")
        return False
    
    # 创建应用
    app = QApplication(sys.argv)
    
    try:
        from src.gui.widgets.template_ocr_dialog import TemplateOCRDialog
        
        print("✓ 成功导入 TemplateOCRDialog")
        
        # 创建对话框
        dialog = TemplateOCRDialog(test_image)
        
        print("✓ 对话框创建成功")
        print()
        print("布局说明:")
        print("  - 顶部：标题 + 状态标签 + 进度条")
        print("  - 左侧：图片预览（70%宽度）")
        print("  - 右侧：控制面板（30%宽度）")
        print("    • 位置调整显示")
        print("    • 缩放滑块")
        print("    • 所有操作按钮")
        print("  - 无滚动区域，所有按钮可见")
        print()
        print("请检查:")
        print("  1. 窗口是否正常显示")
        print("  2. 左右布局是否清晰")
        print("  3. 所有按钮是否可见且不被遮挡")
        print("  4. 方向键是否可以调整图片位置")
        print()
        
        # 显示对话框
        dialog.exec()
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    test_template_dialog()
