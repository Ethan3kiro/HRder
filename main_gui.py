#!/usr/bin/env python3
"""
发射机数据分析器 - GUI 主程序
图形用户界面入口
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.database import TransmitterDatabase
from src.device_manager import DeviceManager
from src.settings_manager import SettingsManager
from src.ocr_extractor_v8 import OCRExtractorV8 as OCRExtractor
from src.analyzer import DataAnalyzer
from src.visualizer import DataVisualizer
from src.exporter import DataExporter
from src.logging_config import setup_logging
from src.config import Config


def main():
    """主函数"""
    # 初始化日志
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("发射机数据分析器 GUI v0.1.0 启动")
    logger.info("=" * 60)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("发射机数据分析器")
    app.setOrganizationName("TransmitterAnalyzer")
    
    try:
        # 初始化数据库
        db_path = Config.get_default_db_path()
        logger.info(f"数据库路径: {db_path}")
        database = TransmitterDatabase(db_path)
        database.initialize_database()
        
        # 初始化管理器
        device_manager = DeviceManager(database)
        settings_manager = SettingsManager(database)
        
        # 确保有默认设备
        devices = device_manager.get_all_devices()
        if not devices:
            logger.info("创建默认设备...")
            device_manager.add_device("默认设备", "系统自动创建的默认设备")
            devices = device_manager.get_all_devices()
        
        # 设置当前设备
        current_device_id = settings_manager.get_current_device_id()
        if not current_device_id and devices:
            settings_manager.set_current_device_id(devices[0]['id'])
            logger.info(f"设置默认设备: {devices[0]['name']}")
        
        # 初始化其他模块
        try:
            ocr_extractor = OCRExtractor()
            logger.info("✓ OCR 提取器初始化成功")
        except Exception as e:
            logger.warning(f"OCR 提取器初始化失败: {e}")
            ocr_extractor = None
        
        # 初始化深度学习 OCR 提取器
        try:
            from src.dl_ocr_extractor import DLOCRExtractor
            if DLOCRExtractor.is_available():
                dl_ocr_extractor = DLOCRExtractor()
                logger.info("✓ 深度学习 OCR 提取器初始化成功")
            else:
                dl_ocr_extractor = None
                logger.info("深度学习 OCR 模型不可用（模型文件不存在）")
        except Exception as e:
            logger.warning(f"深度学习 OCR 提取器初始化失败: {e}")
            dl_ocr_extractor = None
        
        analyzer = DataAnalyzer(database)
        visualizer = DataVisualizer(database)
        exporter = DataExporter()
        
        logger.info("✓ 所有模块初始化完成")
        
        # 导入并创建主窗口（延迟导入以加快启动速度）
        from src.gui.main_window import MainWindow
        
        window = MainWindow(
            database=database,
            device_manager=device_manager,
            settings_manager=settings_manager,
            ocr_extractor=ocr_extractor,
            analyzer=analyzer,
            visualizer=visualizer,
            exporter=exporter,
            dl_ocr_extractor=dl_ocr_extractor
        )
        
        window.show()
        logger.info("✓ GUI 窗口已显示")
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.exception(f"启动失败: {e}")
        
        # 显示错误对话框
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("启动失败")
        error_box.setText(f"应用启动失败：\n\n{str(e)}")
        error_box.setDetailedText(str(e))
        error_box.exec()
        
        sys.exit(1)


if __name__ == "__main__":
    main()
