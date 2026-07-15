#!/usr/bin/env python3
"""
Harris Reader GUI - 图形界面启动文件
"""
import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from src.database import TransmitterDatabase
from src.device_manager import DeviceManager
from src.settings_manager import SettingsManager
from src.analyzer import DataAnalyzer
from src.visualizer import DataVisualizer
from src.exporter import DataExporter
from src.gui.main_window import MainWindow
from src.gui.styles import get_theme
from src.config import Config
from src.logging_config import setup_logging


def get_base_path():
    """获取程序基础路径，兼容PyInstaller打包"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe，使用exe所在目录
        return Path(sys.executable).parent
    else:
        # 如果是源码运行，使用当前文件所在目录
        return Path(__file__).parent


def main():
    """主函数"""
    try:
        # 设置工作目录为程序所在目录
        base_path = get_base_path()
        os.chdir(base_path)
        
        # 设置日志
        setup_logging(log_level="INFO")
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("Harris Reader")
        app.setApplicationVersion(Config.VERSION)
        
        # PyQt6 默认启用高DPI支持，无需手动设置
        
        # 初始化数据库
        db_path = Config.get_default_db_path()
        database = TransmitterDatabase(db_path)
        database.initialize_database()
        
        # 初始化管理器
        device_manager = DeviceManager(database)
        settings_manager = SettingsManager(database)
        
        # 初始化分析和可视化
        analyzer = DataAnalyzer(database)
        visualizer = DataVisualizer(database)
        exporter = DataExporter()  # DataExporter 不需要参数
        
        # 创建主窗口（不再需要OCR和DL提取器）
        window = MainWindow(
            database=database,
            device_manager=device_manager,
            settings_manager=settings_manager,
            analyzer=analyzer,
            visualizer=visualizer,
            exporter=exporter
        )
        
        # 应用样式
        app.setStyleSheet(get_theme("light"))
        
        # 显示窗口
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        # 显示错误对话框
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        QMessageBox.critical(
            None,
            "启动错误",
            f"程序启动失败：\n\n{str(e)}\n\n"
            f"请检查日志文件获取详细信息。"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
