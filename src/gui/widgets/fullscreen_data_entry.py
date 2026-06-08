"""
全屏数据录入窗口
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QGroupBox,
    QHeaderView, QProgressBar, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from pathlib import Path
import pandas as pd


class APIWorker(QThread):
    """API 识别处理工作线程"""
    
    finished = pyqtSignal(object)  # 完成信号，传递 DataFrame
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号
    
    def __init__(self, api_extractor, image_path):
        super().__init__()
        self.api_extractor = api_extractor
        self.image_path = image_path
    
    def run(self):
        """执行 API 识别"""
        try:
            self.progress.emit("正在读取图像...")
            
            if not self.api_extractor:
                self.error.emit("API 提取器未初始化")
                return
            
            self.progress.emit("正在调用 API 识别...")
            result = self.api_extractor.extract_from_image(Path(self.image_path))
            
            self.progress.emit("识别完成！")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"API 识别失败：{str(e)}")


class TemplateWorker(QThread):
    """模板识别处理工作线程"""
    
    finished = pyqtSignal(object)  # 完成信号，传递 DataFrame
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        """执行模板识别"""
        try:
            self.progress.emit("正在加载模板...")
            
            from src.template_ocr_extractor import TemplateOCRExtractor
            
            extractor = TemplateOCRExtractor()
            
            self.progress.emit("正在识别图像...")
            result = extractor.extract_from_image(Path(self.image_path))
            
            self.progress.emit("识别完成！")
            self.finished.emit(result)
            
        except FileNotFoundError as e:
            if 'template_coordinates.json' in str(e):
                self.error.emit(
                    "坐标模板文件不存在\n\n"
                    "请先运行坐标标定工具"
                )
            else:
                self.error.emit(f"模板识别失败：{str(e)}")
        except Exception as e:
            self.error.emit(f"模板识别失败：{str(e)}")


class FullscreenDataEntryWindow(QWidget):
    """全屏数据录入窗口"""
    
    # 信号
    closed = pyqtSignal()  # 窗口关闭信号
    
    def __init__(self, database, device_manager, settings_manager, 
                 image_path=None, api_ocr_extractor=None, recognized_data=None, parent=None):
        super().__init__(parent)
        
        # 初始化所有属性
        self.api_ocr_extractor = api_ocr_extractor
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager
        
        self.current_data = recognized_data  # 接收已识别的数据
        self.api_worker = None
        self.current_image_path = image_path
        
        # 初始化UI组件引用（避免在init_ui之前访问）
        self.file_path_edit = None
        self.image_label = None
        self.assist_result_label = None
        self.assist_result_scroll = None  # 识别结果滚动区域
        self.data_table = None
        self.device_combo = None
        self.month_edit = None
        self.save_btn = None
        self.progress_bar = None
        self.api_btn = None
        self.manual_btn = None
        
        try:
            self.init_ui()
            
            # 如果提供了图像路径，自动加载
            if image_path:
                self.load_image_preview(image_path)
            
            # 如果有已识别的数据，自动显示
            if recognized_data is not None and not recognized_data.empty:
                self.display_data_with_template(recognized_data)
                self.save_btn.setEnabled(True)
                
                # 显示识别结果提示
                self.assist_result_scroll.setVisible(True)
                self.assist_result_label.setText(
                    f"<div style='padding: 10px; background-color: #e8f5e9; border: 1px solid #4caf50; border-radius: 4px;'>"
                    f"<b>✓ 已加载识别结果</b><br>"
                    f"识别到 {len(recognized_data)} 个数据项<br>"
                    f"<span style='color: #666;'>数据来自普通模式的识别结果</span>"
                    f"</div>"
                )
        except Exception as e:
            import traceback
            error_msg = f"初始化全屏窗口失败：{str(e)}\n\n详细信息：\n{traceback.format_exc()}"
            print(error_msg)
            # 显示错误对话框
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "初始化错误", error_msg)
            raise  # 重新抛出异常，让调用者知道初始化失败
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("数据录入 - 全屏模式")
        
        # Windows兼容性：使用普通窗口而不是真正的全屏
        # 设置窗口标志，确保在Windows上正常显示
        from PyQt6.QtCore import Qt
        self.setWindowFlags(
            Qt.WindowType.Window |  # 普通窗口
            Qt.WindowType.WindowMaximizeButtonHint |  # 最大化按钮
            Qt.WindowType.WindowCloseButtonHint  # 关闭按钮
        )
        
        # 设置窗口大小和位置
        self.setGeometry(50, 50, 1400, 900)
        
        # 可选：启动时最大化窗口（而不是全屏）
        # self.showMaximized()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部工具栏
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 主内容区域 - 左右分栏
        content_layout = QHBoxLayout()
        
        # 左侧：原始截图（占 40% 宽度）
        left_panel = self.create_image_panel()
        content_layout.addWidget(left_panel, 2)  # 占 2 份
        
        # 右侧：数据表格（占 60% 宽度）
        right_panel = self.create_data_panel()
        content_layout.addWidget(right_panel, 3)  # 占 3 份
        
        layout.addLayout(content_layout)
        
        # 加载设备列表
        self.load_devices()
    
    def create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 10)
        
        # 返回按钮
        back_btn = QPushButton("← 返回")
        back_btn.clicked.connect(self.close)
        back_btn.setFixedWidth(100)
        toolbar_layout.addWidget(back_btn)
        
        toolbar_layout.addSpacing(20)
        
        # 文件选择
        toolbar_layout.addWidget(QLabel("截图文件："))
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择截图文件...")
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setMinimumWidth(300)
        toolbar_layout.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton("📁 浏览")
        browse_btn.clicked.connect(self.browse_file)
        toolbar_layout.addWidget(browse_btn)
        
        toolbar_layout.addSpacing(20)
        
        # 录入模式按钮
        # 模板识别按钮
        self.template_btn = QPushButton("🖼️ 模板识别")
        self.template_btn.clicked.connect(self.start_template_entry)
        self.template_btn.setToolTip("使用本地模板匹配OCR识别（离线、快速）")
        toolbar_layout.addWidget(self.template_btn)
        
        # API 识别按钮
        self.api_btn = QPushButton("🌐 API 识别")
        self.api_btn.clicked.connect(self.start_api_entry)
        if self.api_ocr_extractor:
            self.api_btn.setEnabled(True)
            provider = self.api_ocr_extractor.config.provider.upper()
            self.api_btn.setToolTip(f"使用 {provider} API 识别")
        else:
            self.api_btn.setEnabled(False)
            self.api_btn.setToolTip("API 识别不可用\n请配置 config/api_config.json")
        toolbar_layout.addWidget(self.api_btn)
        
        self.manual_btn = QPushButton("✍️ 手动录入")
        self.manual_btn.clicked.connect(self.start_manual_entry)
        self.manual_btn.setToolTip("显示空白表格，完全手动填写")
        toolbar_layout.addWidget(self.manual_btn)
        
        toolbar_layout.addSpacing(20)
        
        # 月份和设备
        toolbar_layout.addWidget(QLabel("月份："))
        self.month_edit = QLineEdit()
        self.month_edit.setPlaceholderText("YYYY-MM")
        self.month_edit.setFixedWidth(100)
        toolbar_layout.addWidget(self.month_edit)
        
        toolbar_layout.addSpacing(10)
        
        toolbar_layout.addWidget(QLabel("设备："))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(150)
        toolbar_layout.addWidget(self.device_combo)
        
        toolbar_layout.addStretch()
        
        # 保存按钮
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        self.save_btn.setFixedWidth(100)
        toolbar_layout.addWidget(self.save_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(200)
        toolbar_layout.addWidget(self.progress_bar)
        
        return toolbar
    
    def create_image_panel(self):
        """创建图像显示面板"""
        panel = QGroupBox("原始截图")
        layout = QVBoxLayout(panel)
        
        # 图像显示区域（带滚动）
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_scroll.setMinimumHeight(600)  # 增加最小高度
        
        self.image_label = QLabel("选择图像后将在这里显示")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "color: #999; padding: 40px; background-color: #f5f5f5; "
            "border: 2px dashed #ccc; font-size: 16px;"
        )
        self.image_label.setScaledContents(False)
        
        image_scroll.setWidget(self.image_label)
        layout.addWidget(image_scroll)
        
        # 识别结果提示（仅在 API 识别模式下显示）- 使用滚动区域
        assist_scroll = QScrollArea()
        assist_scroll.setWidgetResizable(True)
        assist_scroll.setMaximumHeight(150)  # 限制最大高度
        assist_scroll.setVisible(False)  # 默认隐藏
        
        self.assist_result_label = QLabel("")
        self.assist_result_label.setWordWrap(True)
        self.assist_result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        assist_scroll.setWidget(self.assist_result_label)
        self.assist_result_scroll = assist_scroll  # 保存引用以便控制显示/隐藏
        layout.addWidget(assist_scroll)
        
        return panel
    
    def create_data_panel(self):
        """创建数据面板（仅表格）"""
        panel = QGroupBox("数据填写表格")
        layout = QVBoxLayout(panel)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["数据项名称", "数值", "单位"])
        
        # Windows兼容性：使用更保守的高度设置
        # 不使用固定高度，让表格自适应
        self.data_table.setMinimumHeight(600)
        
        # 滚动条策略
        self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.data_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 设置列宽
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 数据项名称自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # 数值列固定
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # 单位列固定
        
        # 设置具体宽度
        self.data_table.setColumnWidth(1, 120)  # 数值：120px
        self.data_table.setColumnWidth(2, 60)   # 单位：60px
        
        layout.addWidget(self.data_table)
        
        return panel
    
    def _get_dl_unavailable_reason(self):
        """获取深度学习模型不可用的原因 - 已弃用"""
        return "深度学习模型已移除\n\n请使用 API 识别或手动录入"
    
    def start_assisted_entry(self):
        """开始辅助录入（使用深度学习模型）- 已弃用"""
        QMessageBox.information(
            self, "功能移除",
            "深度学习模型识别功能已移除\n\n请使用：\n• API 识别\n• 手动录入"
        )
    
    def on_assisted_entry_progress(self, message):
        """辅助录入进度更新 - 已弃用"""
        pass
    
    def on_assisted_entry_finished(self, data):
        """辅助录入完成 - 已弃用"""
        pass
    
    def on_assisted_entry_error(self, error_msg):
        """辅助录入错误 - 已弃用"""
        pass
    
    def load_devices(self):
        """加载设备列表"""
        try:
            devices = self.device_manager.get_all_devices()
            self.device_combo.clear()
            
            if devices:
                for device in devices:
                    self.device_combo.addItem(
                        device['device_name'],
                        device['id']
                    )
                
                # 默认选择当前设备
                current_device_id = self.settings_manager.get_current_device_id()
                for i in range(self.device_combo.count()):
                    if self.device_combo.itemData(i) == current_device_id:
                        self.device_combo.setCurrentIndex(i)
                        break
        
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"加载设备列表失败：{str(e)}"
            )
    
    def load_image_preview(self, image_path):
        """加载并显示图像预览"""
        try:
            import cv2
            from PyQt6.QtGui import QImage
            
            self.current_image_path = image_path
            self.file_path_edit.setText(image_path)
            
            # 使用OpenCV加载（支持BMP等更多格式）
            img = cv2.imread(image_path)
            if img is None:
                self.image_label.setText("无法加载图像")
                self.image_label.setStyleSheet(
                    "color: #f44336; padding: 40px; background-color: #ffebee; "
                    "border: 2px solid #f44336; font-size: 16px;"
                )
                return
            
            # 转换BGR到RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            bytes_per_line = ch * w
            
            # 转换为QImage (需要复制数据以保证生命周期)
            q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(q_img)
            
            # 缩放图像以适应显示区域（保持宽高比）
            # 在全屏模式下，可以显示更大的图像
            scaled_pixmap = pixmap.scaled(
                1000, 800,  # 更大的显示尺寸
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet(
                "padding: 10px; background-color: #fff; border: 1px solid #ddd;"
            )
            
        except Exception as e:
            self.image_label.setText(f"加载图像失败：{str(e)}")
            self.image_label.setStyleSheet(
                "color: #f44336; padding: 40px; background-color: #ffebee; "
                "border: 2px solid #f44336; font-size: 16px;"
            )
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择截图文件",
            "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*.*)"
        )
        
        if file_path:
            self.load_image_preview(file_path)
    
    
    def start_template_entry(self):
        """开始模板识别"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        if not Path(file_path).exists():
            QMessageBox.critical(self, "错误", "文件不存在")
            return
        
        # 检查坐标文件
        coords_file = Path('config/template_coordinates.json')
        if not coords_file.exists():
            QMessageBox.warning(
                self, "坐标模板不存在",
                "尚未标定坐标模板\n\n"
                "请先运行坐标标定工具：\n"
                "python tools/coordinate_calibrator.py <图像路径>\n\n"
                "详细说明请查看：docs/TEMPLATE_OCR_GUIDE.md"
            )
            return
        
        # 打开模板OCR对话框
        try:
            from src.gui.widgets.template_ocr_dialog import TemplateOCRDialog
            
            dialog = TemplateOCRDialog(file_path, self)
            dialog.recognition_completed.connect(self.on_template_entry_finished)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"打开识别对话框失败：{str(e)}"
            )
    
    def start_manual_entry(self):
        """开始手动录入（显示空白表格）"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        # 隐藏识别结果提示
        self.assist_result_scroll.setVisible(False)
        
        # 显示空白模板
        self.current_data = pd.DataFrame()
        self.display_data_with_template(self.current_data)
        self.save_btn.setEnabled(True)
        
        QMessageBox.information(
            self, "手动录入", 
            "✓ 已准备好空白表格\n\n请对照左侧截图手动填写所有数据"
        )
    
    def start_api_entry(self):
        """开始 API 识别"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        if not Path(file_path).exists():
            QMessageBox.critical(self, "错误", "文件不存在")
            return
        
        if not self.api_ocr_extractor:
            QMessageBox.critical(
                self, "错误",
                "API 识别不可用\n\n请配置 config/api_config.json"
            )
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("正在调用 API 识别...")
        
        # 创建并启动工作线程
        self.api_worker = APIWorker(self.api_ocr_extractor, file_path)
        self.api_worker.finished.connect(self.on_api_entry_finished)
        self.api_worker.error.connect(self.on_api_entry_error)
        self.api_worker.progress.connect(self.on_api_entry_progress)
        self.api_worker.start()
    
    def on_api_entry_progress(self, message):
        """API 识别进度更新"""
        self.progress_bar.setFormat(message)
    
    def on_api_entry_finished(self, data):
        """API 识别完成"""
        self.progress_bar.setVisible(False)
        
        # 显示模板并填充识别结果
        self.current_data = data if data is not None else pd.DataFrame()
        self.display_data_with_template(self.current_data)
        self.save_btn.setEnabled(True)
        
        # 显示识别结果提示
        self.assist_result_scroll.setVisible(True)
        
        if data is not None and not data.empty:
            provider = self.api_ocr_extractor.config.provider.upper()
            self.assist_result_label.setText(
                f"<div style='padding: 10px; background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 4px;'>"
                f"<b>✓ {provider} API 识别完成</b><br>"
                f"识别到 {len(data)} 个数据项<br>"
                f"<span style='color: #666;'>请仔细核对并修正识别结果</span>"
                f"</div>"
            )
        else:
            self.assist_result_label.setText(
                f"<div style='padding: 10px; background-color: #fff3e0; border: 1px solid #ff9800; border-radius: 4px;'>"
                f"<b>⚠ 未识别到数据</b><br>"
                f"<span style='color: #666;'>请手动填写所有数据</span>"
                f"</div>"
            )
    
    def on_template_entry_finished(self, data):
        """模板识别完成"""
        # 显示模板并填充识别结果
        self.current_data = data if data is not None else pd.DataFrame()
        self.display_data_with_template(self.current_data)
        self.save_btn.setEnabled(True)
        
        # 显示识别结果提示
        self.assist_result_scroll.setVisible(True)
        
        if data is not None and not data.empty:
            self.assist_result_label.setText(
                f"<div style='padding: 10px; background-color: #e8f5e9; border: 1px solid #4caf50; border-radius: 4px;'>"
                f"<b>✓ 模板识别完成</b><br>"
                f"识别到 {len(data)} 个数据项 ({len(data)/71*100:.1f}%)<br>"
                f"<span style='color: #666;'>请核对识别结果并修正错误</span>"
                f"</div>"
            )
        else:
            self.assist_result_label.setText(
                f"<div style='padding: 10px; background-color: #fff3e0; border: 1px solid #ff9800; border-radius: 4px;'>"
                f"<b>⚠ 未识别到数据</b><br>"
                f"<span style='color: #666;'>请手动填写所有数据</span>"
                f"</div>"
            )
    
    def on_api_entry_error(self, error_msg):
        """API 识别错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", f"API 识别失败：{error_msg}")
    
    def display_data_with_template(self, assisted_data):
        """显示完整的数据模板，并填充识别的数据"""
        try:
            # 定义所有 71 个数据项
            all_items = []
            
            # COMBINER ISO TEMPERATURES (7 项)
            combiner_items = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
            for item_name in combiner_items:
                all_items.append({
                    'item_name': item_name,
                    'value': '',
                    'unit': '°C',
                    'category': 'COMBINER'
                })
            
            # Z-Plane 数据 (64 项: 4 模块 × 8 行 × 2 列)
            zplane_modules = ['A', 'B', 'C', 'D']
            for module in zplane_modules:
                for row_num in range(1, 9):
                    # Current
                    all_items.append({
                        'item_name': f'Z-Plane {module}-Current-{row_num}',
                        'value': '',
                        'unit': 'A',
                        'category': f'Z-Plane {module}'
                    })
                    # ISO Temp
                    all_items.append({
                        'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                        'value': '',
                        'unit': '°C',
                        'category': f'Z-Plane {module}'
                    })
            
            # 如果有识别数据，填充到模板中
            if assisted_data is not None and not assisted_data.empty:
                # 创建名称映射字典（处理命名差异）
                api_dict = {}
                for _, row in assisted_data.iterrows():
                    api_name = row.get('item_name', '')
                    value = row.get('value', '')
                    api_dict[api_name] = value
                    
                    # 为模板识别创建名称映射
                    # 模板格式: Z-Plane-A-Current-1, Z-Plane-A-ISOTemp-1
                    # 表格格式: Z-Plane A-Current-1, Z-Plane A-ISO Temp-1
                    if 'Z-Plane-' in api_name:
                        # Z-Plane-A-Current-1 -> Z-Plane A-Current-1
                        normalized = api_name.replace('Z-Plane-', 'Z-Plane ')
                        # Z-Plane A-ISOTemp-1 -> Z-Plane A-ISO Temp-1
                        normalized = normalized.replace('-ISOTemp-', '-ISO Temp-')
                        api_dict[normalized] = value
                
                # 查找匹配的数据项
                for item in all_items:
                    if item['item_name'] in api_dict:
                        value = api_dict[item['item_name']]
                        item['value'] = str(value) if value != '' else ''
            
            # 显示到表格
            self.data_table.setRowCount(len(all_items))
            
            for row, item in enumerate(all_items):
                try:
                    # 数据项名称（只读）
                    name_item = QTableWidgetItem(item['item_name'])
                    name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    name_item.setBackground(Qt.GlobalColor.lightGray)
                    self.data_table.setItem(row, 0, name_item)
                    
                    # 数值（可编辑）
                    value_item = QTableWidgetItem(item['value'])
                    # 如果是识别填充的数据，使用浅黄色背景提示用户核对
                    if item['value']:
                        value_item.setBackground(Qt.GlobalColor.yellow)
                        value_item.setToolTip("识别的数据，请核对")
                    else:
                        value_item.setBackground(Qt.GlobalColor.white)
                    self.data_table.setItem(row, 1, value_item)
                    
                    # 单位（只读）
                    unit_item = QTableWidgetItem(item['unit'])
                    unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    unit_item.setBackground(Qt.GlobalColor.lightGray)
                    self.data_table.setItem(row, 2, unit_item)
                    
                except Exception as e:
                    print(f"设置表格第 {row} 行时出错：{str(e)}")
                    continue
                    
        except Exception as e:
            import traceback
            error_msg = f"显示数据模板失败：{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "错误", f"显示数据模板失败：{str(e)}")
    
    def save_data(self):
        """保存数据"""
        month = self.month_edit.text().strip()
        
        if not month:
            QMessageBox.warning(self, "提示", "请输入月份")
            return
        
        # 验证月份格式
        import re
        if not re.match(r'^\d{4}-\d{2}$', month):
            QMessageBox.warning(
                self, "提示", 
                "月份格式错误\n\n正确格式：YYYY-MM"
            )
            return
        
        # 从表格获取数据
        data_list = []
        empty_count = 0
        
        for row in range(self.data_table.rowCount()):
            item_name = self.data_table.item(row, 0).text()
            value_text = self.data_table.item(row, 1).text().strip()
            unit = self.data_table.item(row, 2).text()
            
            if not value_text:
                empty_count += 1
                continue
            
            try:
                value = float(value_text)
            except ValueError:
                QMessageBox.warning(
                    self, "数据格式错误",
                    f"第 {row + 1} 行数据格式错误：{value_text}"
                )
                return
            
            data_list.append({
                'item_name': item_name,
                'value': value,
                'unit': unit
            })
        
        if not data_list:
            QMessageBox.warning(self, "提示", "没有可保存的数据")
            return
        
        # 提示用户
        if empty_count > 0:
            reply = QMessageBox.question(
                self, "确认保存",
                f"✓ 已填写 {len(data_list)} 条数据\n"
                f"⚠ 还有 {empty_count} 条数据未填写\n\n"
                f"是否继续保存？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        data_df = pd.DataFrame(data_list)
        
        # 获取设备
        device_id = self.device_combo.currentData()
        if not device_id:
            QMessageBox.warning(self, "提示", "请选择设备")
            return
        
        # 保存数据
        try:
            # 检查是否已存在
            existing_data = self.database.query_by_month(month, device_id)
            if not existing_data.empty:
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"{month} 已有数据，是否覆盖？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
                
                self.database.delete_month(month, device_id)
            
            self.database.insert_monthly_data(month, data_df, overwrite=False, device_id=device_id)
            
            QMessageBox.information(
                self, "保存成功", 
                f"✓ 成功保存 {len(data_df)} 条数据到 {month}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", 
                f"保存数据失败：{str(e)}"
            )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.closed.emit()
        event.accept()
