#!/usr/bin/env python3
"""
测试全屏数据录入窗口的新布局
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication


def test_fullscreen_window():
    """测试全屏窗口"""
    print("=" * 70)
    print("测试全屏数据录入窗口 - 新左右布局")
    print("=" * 70)
    print()
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 模拟必要的依赖
    class MockDatabase:
        def query_by_month(self, month, device_id):
            import pandas as pd
            return pd.DataFrame()
        
        def delete_month(self, month, device_id):
            pass
        
        def insert_monthly_data(self, month, data, overwrite, device_id):
            pass
    
    class MockDeviceManager:
        def get_all_devices(self):
            return [
                {'id': 1, 'device_name': '测试设备1'},
                {'id': 2, 'device_name': '测试设备2'}
            ]
    
    class MockSettingsManager:
        def get_current_device_id(self):
            return 1
    
    # 导入窗口
    try:
        from src.gui.widgets.fullscreen_data_entry import FullscreenDataEntryWindow
        
        print("✓ 成功导入 FullscreenDataEntryWindow")
        
        # 创建窗口
        window = FullscreenDataEntryWindow(
            database=MockDatabase(),
            device_manager=MockDeviceManager(),
            settings_manager=MockSettingsManager(),
            image_path='911-20251016.jpg' if Path('911-20251016.jpg').exists() else None
        )
        
        print("✓ 窗口创建成功")
        print()
        print("布局说明:")
        print("  - 顶部：简化的标题栏和返回按钮")
        print("  - 左侧：图片预览 + 操作按钮（45%宽度）")
        print("  - 右侧：数据表格 + 保存按钮（55%宽度）")
        print("  - 无滚动区域，避免兼容性问题")
        print()
        print("请检查:")
        print("  1. 窗口是否正常显示")
        print("  2. 左右布局是否清晰")
        print("  3. 所有按钮是否在正确位置")
        print("  4. 表格是否使用内置滚动条")
        print()
        
        # 显示窗口
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_fullscreen_window()
