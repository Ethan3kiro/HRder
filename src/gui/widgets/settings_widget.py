"""
系统设置组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QSpinBox, QMessageBox, QGroupBox,
    QFormLayout
)
from PyQt6.QtCore import pyqtSignal


class SettingsWidget(QWidget):
    """系统设置组件"""
    
    # 信号
    theme_changed = pyqtSignal(str)
    
    def __init__(self, settings_manager, database):
        super().__init__()
        self.settings_manager = settings_manager
        self.database = database
        self.current_theme = "light"
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("⚙️ 系统设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 灵敏度设置
        sensitivity_group = QGroupBox("灵敏度阈值设置")
        sensitivity_layout = QFormLayout()
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setSuffix(" %")
        self.threshold_spin.setValue(
            int(self.settings_manager.get_sensitivity_threshold())
        )
        
        sensitivity_layout.addRow("变化阈值：", self.threshold_spin)
        
        save_btn = QPushButton("💾 保存设置")
        save_btn.clicked.connect(self.save_settings)
        sensitivity_layout.addRow("", save_btn)
        
        sensitivity_group.setLayout(sensitivity_layout)
        layout.addWidget(sensitivity_group)
        
        # 主题设置
        theme_group = QGroupBox("界面主题")
        theme_layout = QHBoxLayout()
        
        light_btn = QPushButton("☀️ 浅色主题")
        light_btn.clicked.connect(lambda: self.change_theme("light"))
        theme_layout.addWidget(light_btn)
        
        dark_btn = QPushButton("🌙 深色主题")
        dark_btn.clicked.connect(lambda: self.change_theme("dark"))
        theme_layout.addWidget(dark_btn)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 数据库信息
        db_group = QGroupBox("数据库信息")
        db_layout = QFormLayout()
        
        db_path = str(self.database.db_path)
        db_path_label = QLabel(db_path)
        db_path_label.setWordWrap(True)
        db_layout.addRow("数据库路径：", db_path_label)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        layout.addStretch()
    
    def save_settings(self):
        """保存设置"""
        try:
            threshold = self.threshold_spin.value()
            self.settings_manager.set_sensitivity_threshold(threshold)
            
            QMessageBox.information(
                self, "成功", f"灵敏度阈值已设置为 {threshold}%"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"保存设置失败：\n{str(e)}"
            )
    
    def change_theme(self, theme_name):
        """切换主题"""
        self.current_theme = theme_name
        self.theme_changed.emit(theme_name)
        
        QMessageBox.information(
            self, "提示", f"已切换到{theme_name}主题"
        )
    
    def refresh(self):
        """刷新数据"""
        self.threshold_spin.setValue(
            int(self.settings_manager.get_sensitivity_threshold())
        )
