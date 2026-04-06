"""
PyInstaller 打包配置脚本
用于生成 .spec 文件
"""

import PyInstaller.__main__
import sys
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 打包配置
PyInstaller.__main__.run([
    'main_gui.py',
    '--name=HarrisReader',
    '--windowed',  # 不显示控制台窗口
    '--onefile',   # 打包成单个文件
    '--icon=assets/icon.ico' if (ROOT_DIR / 'assets' / 'icon.ico').exists() else '',
    
    # 添加数据文件
    '--add-data=config;config',
    '--add-data=models;models' if (ROOT_DIR / 'models').exists() else '',
    
    # 隐藏导入
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=PyQt6.QtCharts',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--hidden-import=matplotlib',
    '--hidden-import=PIL',
    '--hidden-import=pytesseract',
    '--hidden-import=openpyxl',
    '--hidden-import=xlsxwriter',
    '--hidden-import=requests',
    '--hidden-import=cv2',
    
    # 收集所有相关包
    '--collect-all=PyQt6',
    '--collect-all=matplotlib',
    
    # 排除不需要的模块（减小体积）
    '--exclude-module=pytest',
    '--exclude-module=hypothesis',
    '--exclude-module=tkinter',
    
    # 优化
    '--clean',
    '--noconfirm',
])
