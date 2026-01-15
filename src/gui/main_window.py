"""
主窗口
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel, QPushButton, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .styles import get_theme
from .widgets.dashboard_widget import DashboardWidget
from .widgets.device_widget import DeviceWidget
from .widgets.data_entry_widget import DataEntryWidget
from .widgets.comparison_widget import ComparisonWidget
from .widgets.trend_widget import TrendWidget
from .widgets.data_management_widget import DataManagementWidget
from .widgets.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号
    theme_changed = pyqtSignal(str)
    
    def __init__(self, database, device_manager, settings_manager, 
                 ocr_extractor, analyzer, visualizer, exporter, dl_ocr_extractor=None):
        super().__init__()
        
        # 保存模块引用
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager
        self.ocr_extractor = ocr_extractor
        self.dl_ocr_extractor = dl_ocr_extractor
        self.analyzer = analyzer
        self.visualizer = visualizer
        self.exporter = exporter
        
        # 当前主题
        self.current_theme = "light"
        
        # 初始化 UI
        self.init_ui()
        
        # 应用样式
        self.apply_theme(self.current_theme)
        
        print("✓ GUI 主窗口初始化完成")
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("发射机数据分析器 v0.1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建侧边栏
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 创建内容区域
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # 添加页面
        self.add_pages()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 默认显示仪表板
        self.switch_page(0)
    
    def create_sidebar(self):
        """创建侧边栏"""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题
        title = QLabel("功能菜单")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sidebarTitle")
        title.setFixedHeight(60)
        layout.addWidget(title)
        
        # 菜单项
        menu_items = [
            ("📊", "仪表板"),
            ("📱", "设备管理"),
            ("📥", "数据录入"),
            ("📊", "两月对比"),
            ("📈", "趋势分析"),
            ("💾", "数据管理"),
            ("⚙️", "系统设置"),
        ]
        
        self.menu_buttons = []
        for icon, text in menu_items:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("menuButton")
            btn.setFixedHeight(50)
            btn.clicked.connect(
                lambda checked, idx=len(self.menu_buttons): self.switch_page(idx)
            )
            layout.addWidget(btn)
            self.menu_buttons.append(btn)
        
        layout.addStretch()
        
        # 底部信息
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 10, 10, 10)
        
        # 当前设备
        self.current_device_label = QLabel()
        self.current_device_label.setObjectName("sidebarInfo")
        self.current_device_label.setWordWrap(True)
        info_layout.addWidget(self.current_device_label)
        
        # 主题切换按钮
        theme_btn = QPushButton("🌓 切换主题")
        theme_btn.setObjectName("menuButton")
        theme_btn.setFixedHeight(40)
        theme_btn.clicked.connect(self.toggle_theme)
        info_layout.addWidget(theme_btn)
        
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        layout.addWidget(info_widget)
        
        return sidebar
    
    def add_pages(self):
        """添加页面"""
        # 仪表板
        self.dashboard_widget = DashboardWidget(
            self.database, self.device_manager, self.settings_manager
        )
        self.content_stack.addWidget(self.dashboard_widget)
        
        # 设备管理
        self.device_widget = DeviceWidget(
            self.device_manager, self.database
        )
        self.content_stack.addWidget(self.device_widget)
        
        # 数据录入
        self.data_entry_widget = DataEntryWidget(
            self.ocr_extractor, self.database, self.device_manager, self.settings_manager,
            dl_ocr_extractor=self.dl_ocr_extractor
        )
        self.content_stack.addWidget(self.data_entry_widget)
        
        # 两月对比
        self.comparison_widget = ComparisonWidget(
            self.analyzer, self.database, self.device_manager,
            self.visualizer, self.exporter, self.settings_manager
        )
        self.content_stack.addWidget(self.comparison_widget)
        
        # 趋势分析
        self.trend_widget = TrendWidget(
            self.database, self.device_manager, self.visualizer, self.settings_manager
        )
        self.content_stack.addWidget(self.trend_widget)
        
        # 数据管理
        self.data_management_widget = DataManagementWidget(
            self.database, self.device_manager, self.exporter, self.settings_manager
        )
        self.content_stack.addWidget(self.data_management_widget)
        
        # 系统设置
        self.settings_widget = SettingsWidget(
            self.settings_manager, self.database
        )
        self.content_stack.addWidget(self.settings_widget)
        
        # 连接信号
        self.settings_widget.theme_changed.connect(self.apply_theme)
        self.device_widget.device_changed.connect(self.update_current_device)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 数据库状态
        self.db_status_label = QLabel("数据库：已连接")
        self.db_status_label.setObjectName("statusLabel")
        status_bar.addWidget(self.db_status_label)
        
        status_bar.addWidget(QLabel("|"))
        
        # 当前设备
        self.device_status_label = QLabel()
        self.device_status_label.setObjectName("statusLabel")
        status_bar.addWidget(self.device_status_label)
        
        status_bar.addWidget(QLabel("|"))
        
        # 就绪状态
        self.ready_label = QLabel("就绪")
        self.ready_label.setObjectName("statusLabel")
        status_bar.addPermanentWidget(self.ready_label)
        
        # 更新设备信息
        self.update_current_device()
    
    def switch_page(self, index):
        """切换页面"""
        self.content_stack.setCurrentIndex(index)
        
        # 更新按钮状态
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.setProperty("active", True)
            else:
                btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # 刷新当前页面
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
    
    def update_current_device(self):
        """更新当前设备显示"""
        try:
            device_id = self.settings_manager.get_current_device_id()
            device = self.device_manager.get_device_by_id(device_id)
            
            if device:
                device_text = f"当前设备：\n{device['device_name']}"
                status_text = f"当前设备：{device['device_name']} (ID: {device_id})"
            else:
                device_text = "当前设备：\n未选择"
                status_text = "当前设备：未选择"
            
            self.current_device_label.setText(device_text)
            self.device_status_label.setText(status_text)
            
        except Exception as e:
            print(f"更新设备信息失败: {e}")
            self.current_device_label.setText("当前设备：\n错误")
            self.device_status_label.setText("当前设备：错误")
    
    def toggle_theme(self):
        """切换主题"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)
    
    def apply_theme(self, theme_name):
        """应用主题"""
        self.current_theme = theme_name
        self.setStyleSheet(get_theme(theme_name))
        self.theme_changed.emit(theme_name)
        print(f"✓ 已切换到 {theme_name} 主题")
    
    def set_status(self, message, timeout=3000):
        """设置状态栏消息"""
        self.statusBar().showMessage(message, timeout)
