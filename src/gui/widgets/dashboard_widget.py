"""
仪表板组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout
)
from PyQt6.QtCore import Qt


class DashboardWidget(QWidget):
    """仪表板组件"""
    
    def __init__(self, database, device_manager, settings_manager):
        super().__init__()
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📊 仪表板")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 统计卡片
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        # 设备总数
        devices_count = len(self.device_manager.get_all_devices())
        cards_layout.addWidget(
            self.create_stat_card("设备总数", str(devices_count), "#4CAF50"),
            0, 0
        )
        
        # 数据记录数
        try:
            device_id = self.settings_manager.get_current_device_id()
            months = self.database.get_available_months(device_id)
            records_count = len(months)
        except:
            records_count = 0
        
        cards_layout.addWidget(
            self.create_stat_card("月度记录", str(records_count), "#2196F3"),
            0, 1
        )
        
        # 灵敏度阈值
        threshold = self.settings_manager.get_sensitivity_threshold()
        cards_layout.addWidget(
            self.create_stat_card("灵敏度阈值", f"{threshold}%", "#FF9800"),
            0, 2
        )
        
        layout.addLayout(cards_layout)
        
        # 说明信息
        info = QLabel(
            "欢迎使用发射机数据分析器！\n\n"
            "✓ 支持多设备管理\n"
            "✓ OCR 自动识别\n"
            "✓ 数据对比分析\n"
            "✓ 趋势可视化\n\n"
            "点击左侧菜单开始使用"
        )
        info.setObjectName("infoText")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
    
    def create_stat_card(self, title, value, color):
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 20px;
                min-height: 100px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return card
    
    def refresh(self):
        """刷新数据"""
        # 清除旧的组件
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        # 重新初始化 UI
        self.init_ui()
