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


class FullscreenDataEntryWindow(QWidget):
    """全屏数据录入窗口"""
    
    # 信号
    closed = pyqtSignal()  # 窗口关闭信号
    
    def __init__(self, ocr_extractor, database, device_manager, settings_manager, 
                 image_path=None, parent=None):
        super().__init__(parent)
        self.ocr_extractor = ocr_extractor
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager
        
        self.current_data = None
        self.ocr_worker = None
        self.current_image_path = image_path
        
        self.init_ui()
        
        # 如果提供了图像路径，自动加载
        if image_path:
            self.load_image_preview(image_path)
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("数据录入 - 全屏模式")
        self.setGeometry(50, 50, 1400, 900)
        
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
        
        return panel
    
    def create_data_panel(self):
        """创建数据面板（仅表格）"""
        panel = QGroupBox("数据填写表格")
        layout = QVBoxLayout(panel)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["数据项名称", "数值", "单位"])
        
        # 设置表格固定高度，确保滚动条始终在可见区域内
        self.data_table.setFixedHeight(650)  # 固定高度，确保滚动条可见
        
        # 强制显示水平滚动条
        self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.data_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 设置列宽 - 使用更小的固定宽度
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 数据项名称固定
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # 数值列固定
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 单位列固定
        
        # 设置具体宽度 - 确保三列都能在可见区域内
        self.data_table.setColumnWidth(0, 180)  # 数据项名称：180px
        self.data_table.setColumnWidth(1, 120)  # 数值：120px（加宽以便输入）
        self.data_table.setColumnWidth(2, 60)   # 单位：60px
        
        # 总宽度：360px，应该能在右侧面板中完整显示
        
        layout.addWidget(self.data_table)
        
        return panel
    
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
            self.current_image_path = image_path
            self.file_path_edit.setText(image_path)
            
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                self.image_label.setText("无法加载图像")
                self.image_label.setStyleSheet(
                    "color: #f44336; padding: 40px; background-color: #ffebee; "
                    "border: 2px solid #f44336; font-size: 16px;"
                )
                return
            
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
            
            # 自动显示数据模板
            self.display_data_with_template(pd.DataFrame())
            self.save_btn.setEnabled(True)
            
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
    
    def start_ocr(self):
        """开始 OCR 识别"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        if not Path(file_path).exists():
            QMessageBox.critical(self, "错误", "文件不存在")
            return
        
        if not self.ocr_extractor:
            QMessageBox.critical(
                self, "错误", 
                "OCR 提取器未初始化"
            )
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # 导入 OCRWorker
        from .data_entry_widget import OCRWorker
        
        # 创建并启动工作线程
        self.ocr_worker = OCRWorker(self.ocr_extractor, file_path)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.progress.connect(lambda msg: self.progress_bar.setFormat(msg))
        self.ocr_worker.start()
    
    def on_ocr_finished(self, data):
        """OCR 完成"""
        self.progress_bar.setVisible(False)
        
        # 显示空白模板
        self.current_data = pd.DataFrame()
        self.display_data_with_template(self.current_data)
        self.save_btn.setEnabled(True)
        
        if data is not None and not data.empty:
            QMessageBox.information(
                self, "识别完成", 
                f"✓ OCR 识别到 {len(data)} 个数字\n\n"
                f"请对照左侧截图手动填写数据"
            )
        else:
            QMessageBox.information(
                self, "提示", 
                "未识别到数据\n\n请对照左侧截图手动填写所有数据"
            )
    
    def on_ocr_error(self, error_msg):
        """OCR 错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", error_msg)
    
    def display_data_with_template(self, ocr_data):
        """显示完整的数据模板"""
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
        
        # 显示到表格
        self.data_table.setRowCount(len(all_items))
        
        for row, item in enumerate(all_items):
            # 数据项名称（只读）
            name_item = QTableWidgetItem(item['item_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 0, name_item)
            
            # 数值（可编辑）
            value_item = QTableWidgetItem(item['value'])
            value_item.setBackground(Qt.GlobalColor.white)
            self.data_table.setItem(row, 1, value_item)
            
            # 单位（只读）
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            unit_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 2, unit_item)
    
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
