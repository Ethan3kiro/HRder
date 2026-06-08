"""
数据录入组件（支持API识别、模板识别和手动输入）
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QGroupBox, QFormLayout,
    QHeaderView, QProgressBar, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from pathlib import Path
import pandas as pd


class APIWorker(QThread):
    """API 识别工作线程"""
    
    finished = pyqtSignal(object)  # 完成信号
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


class DataEntryWidget(QWidget):
    """数据录入组件"""
    
    def __init__(self, database, device_manager, settings_manager):
        super().__init__()
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager
        self.api_extractor = None
        
        self.current_data = None
        self.api_worker = None
        self.current_image_path = None
        
        # 加载 API 配置
        self._load_api_config()
        
        self.init_ui()
    
    def _load_api_config(self):
        """加载 API 配置"""
        try:
            from src.api_ocr_extractor import load_api_config_from_file, APIOCRExtractor
            
            config_path = Path('config/api_config.json')
            api_config = load_api_config_from_file(config_path)
            
            if api_config:
                self.api_extractor = APIOCRExtractor(api_config)
                print(f"✓ 已加载 API 配置: {api_config.provider}")
            else:
                self.api_extractor = None
                print("ℹ API 配置文件不存在")
                
        except Exception as e:
            self.api_extractor = None
            print(f"⚠ 加载 API 配置失败: {str(e)}")
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📥 数据录入")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 文件选择区域
        file_group = QGroupBox("1. 选择截图文件")
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("请选择发射机截图文件...")
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton("📁 浏览")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 识别按钮区域
        mode_group = QGroupBox("2. 选择录入方式")
        mode_layout = QHBoxLayout()
        
        # 模板识别按钮
        self.template_btn = QPushButton("🖼️ 模板识别")
        self.template_btn.clicked.connect(self.start_template_recognition)
        self.template_btn.setToolTip(
            "使用本地模板匹配OCR识别\n"
            "• 完全离线，无需网络\n"
            "• 速度快，适合老旧硬件\n"
            "• 需要先标定坐标"
        )
        mode_layout.addWidget(self.template_btn)
        
        # API 识别按钮
        self.api_btn = QPushButton("🌐 API 识别")
        self.api_btn.clicked.connect(self.start_api_recognition)
        if self.api_extractor:
            self.api_btn.setEnabled(True)
            provider = self.api_extractor.config.provider.upper()
            self.api_btn.setToolTip(f"使用 {provider} API 进行图像识别")
        else:
            self.api_btn.setEnabled(False)
            self.api_btn.setToolTip(
                "API 识别不可用\n\n"
                "请在'系统设置'中配置 API"
            )
        mode_layout.addWidget(self.api_btn)
        
        # 手动录入按钮
        manual_btn = QPushButton("✍️ 手动录入")
        manual_btn.clicked.connect(self.start_manual_entry)
        manual_btn.setToolTip("显示空白表格，完全手动填写所有数据")
        mode_layout.addWidget(manual_btn)
        
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 月份和设备选择
        info_group = QGroupBox("3. 输入月份和选择设备")
        info_layout = QHBoxLayout()
        
        info_layout.addWidget(QLabel("月份："))
        self.month_edit = QLineEdit()
        self.month_edit.setPlaceholderText("YYYY-MM")
        self.month_edit.setMaximumWidth(120)
        info_layout.addWidget(self.month_edit)
        
        info_layout.addSpacing(20)
        
        info_layout.addWidget(QLabel("保存到设备："))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(150)
        info_layout.addWidget(self.device_combo)
        
        info_layout.addStretch()
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 截图预览
        preview_group = QGroupBox("4. 原始截图预览")
        preview_layout = QVBoxLayout()
        
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_scroll.setMaximumHeight(200)
        
        self.image_label = QLabel("选择图像后将在这里显示")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #999; padding: 20px; background-color: #f5f5f5; border: 1px dashed #ccc;")
        
        image_scroll.setWidget(self.image_label)
        preview_layout.addWidget(image_scroll)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 数据表格
        data_group = QGroupBox("5. 数据填写表格")
        data_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["数据项名称", "数值", "单位"])
        self.data_table.setMinimumHeight(400)
        
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        data_layout.addWidget(self.data_table)
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存到数据库")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(clear_btn)
        
        # 大屏模式按钮
        fullscreen_btn = QPushButton("🖥️ 大屏模式")
        fullscreen_btn.clicked.connect(self.open_fullscreen_mode)
        fullscreen_btn.setToolTip("打开大屏模式，方便同时查看图片和数据")
        button_layout.addWidget(fullscreen_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 加载设备列表
        self.load_devices()
    
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
                
                current_device_id = self.settings_manager.get_current_device_id()
                for i in range(self.device_combo.count()):
                    if self.device_combo.itemData(i) == current_device_id:
                        self.device_combo.setCurrentIndex(i)
                        break
            else:
                QMessageBox.warning(
                    self, "提示",
                    "还没有设备\n\n请先在 '设备管理' 页面添加设备"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"加载设备列表失败：{str(e)}"
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
            self.file_path_edit.setText(file_path)
            self.load_image_preview(file_path)
    
    def load_image_preview(self, image_path):
        """加载并显示图像预览"""
        try:
            import cv2
            from PyQt6.QtGui import QImage
            
            self.current_image_path = image_path
            
            # 使用OpenCV加载（支持BMP等更多格式）
            img = cv2.imread(image_path)
            if img is None:
                self.image_label.setText("无法加载图像")
                return
            
            # 转换BGR到RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            bytes_per_line = ch * w
            
            # 转换为QImage
            q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # 缩放显示
            scaled_pixmap = pixmap.scaled(
                400, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("padding: 5px; background-color: #fff; border: 1px solid #ddd;")
            
        except Exception as e:
            self.image_label.setText(f"加载图像失败：{str(e)}")
    
    def start_api_recognition(self):
        """开始 API 识别"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        if not Path(file_path).exists():
            QMessageBox.critical(self, "错误", "文件不存在")
            return
        
        if not self.api_extractor:
            QMessageBox.critical(
                self, "错误",
                "API 识别不可用\n\n请在'系统设置'中配置 API"
            )
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # 创建并启动工作线程
        self.api_worker = APIWorker(self.api_extractor, file_path)
        self.api_worker.finished.connect(self.on_api_finished)
        self.api_worker.error.connect(self.on_api_error)
        self.api_worker.progress.connect(self.on_api_progress)
        self.api_worker.start()
    
    
    def start_template_recognition(self):
        """开始模板识别"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        if not Path(file_path).exists():
            QMessageBox.critical(self, "错误", "文件不存在")
            return
        
        # 检查坐标文件是否存在
        coords_file = Path('config/template_coordinates.json')
        if not coords_file.exists():
            reply = QMessageBox.question(
                self, "坐标模板不存在",
                "尚未标定坐标模板\n\n"
                "是否打开标定工具进行标定？\n\n"
                "（标定工具使用说明请查看文档）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(
                    self, "启动标定工具",
                    "请在终端运行以下命令进行坐标标定：\n\n"
                    f"python tools/coordinate_calibrator.py {file_path}\n\n"
                    "详细说明请查看：docs/TEMPLATE_OCR_GUIDE.md"
                )
            return
        
        # 打开模板OCR对话框
        try:
            from src.gui.widgets.template_ocr_dialog import TemplateOCRDialog
            
            dialog = TemplateOCRDialog(file_path, self)
            dialog.recognition_completed.connect(self.on_template_finished)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"打开识别对话框失败：{str(e)}"
            )
    
    def on_template_finished(self, data):
        """模板识别完成（从对话框返回）"""
        if data is not None and not data.empty:
            self.current_data = data
            self.display_data_with_api_results(data)  # 复用API结果显示方法
            self.save_btn.setEnabled(True)
            
            QMessageBox.information(
                self, "识别完成",
                f"✓ 识别到 {len(data)} 个数据项 ({len(data)/71*100:.1f}%)\n\n"
                f"• 黄色背景：模板识别的数据\n"
                f"• 请仔细核对后保存"
            )
        else:
            QMessageBox.warning(
                self, "提示",
                "未识别到数据\n\n请检查：\n"
                "1. 坐标是否正确标定\n"
                "2. 图像质量是否清晰\n"
                "3. 图像布局是否一致"
            )
    
    def start_manual_entry(self):
        """开始手动录入"""
        file_path = self.file_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        # 显示空白模板
        self.current_data = pd.DataFrame()
        self.display_data_template()
        self.save_btn.setEnabled(True)
        
        QMessageBox.information(
            self, "手动录入",
            "✓ 已显示完整的数据项模板\n\n请参考截图，手动填写所有数据"
        )
    
    def on_api_finished(self, data):
        """API 识别完成"""
        self.progress_bar.setVisible(False)
        
        if data is not None and not data.empty:
            self.current_data = data
            self.display_data_with_api_results(data)
            self.save_btn.setEnabled(True)
            
            QMessageBox.information(
                self, "识别完成",
                f"✓ 识别到 {len(data)} 个数据项\n\n请核对数据后保存"
            )
        else:
            QMessageBox.warning(
                self, "提示",
                "未识别到数据\n\n请使用手动录入"
            )
    
    def on_api_error(self, error_msg):
        """API 识别错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", error_msg)
    
    def on_api_progress(self, message):
        """API 识别进度"""
        self.progress_bar.setFormat(message)
    
    def display_data_template(self):
        """显示空白数据模板"""
        all_items = self._get_all_data_items()
        
        self.data_table.setRowCount(len(all_items))
        
        for row, item in enumerate(all_items):
            # 数据项名称（只读）
            name_item = QTableWidgetItem(item['item_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 0, name_item)
            
            # 数值（可编辑）
            value_item = QTableWidgetItem("")
            self.data_table.setItem(row, 1, value_item)
            
            # 单位（只读）
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            unit_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 2, unit_item)
    
    def display_data_with_api_results(self, api_data):
        """显示API识别结果"""
        all_items = self._get_all_data_items()
        
        # 创建API数据的查找字典（包含名称变体映射）
        api_dict = {}
        for _, row in api_data.iterrows():
            api_name = row['item_name']
            api_dict[api_name] = row['value']
            
            # 为模板识别创建名称映射（处理命名差异）
            # 模板格式: Z-Plane-A-Current-1, Z-Plane-A-ISOTemp-1
            # 表格格式: Z-Plane A-Current-1, Z-Plane A-ISO Temp-1
            if 'Z-Plane-' in api_name:
                # Z-Plane-A-Current-1 -> Z-Plane A-Current-1
                normalized = api_name.replace('Z-Plane-', 'Z-Plane ')
                # Z-Plane A-ISOTemp-1 -> Z-Plane A-ISO Temp-1
                normalized = normalized.replace('-ISOTemp-', '-ISO Temp-')
                api_dict[normalized] = row['value']
        
        self.data_table.setRowCount(len(all_items))
        
        for row, item in enumerate(all_items):
            # 数据项名称（只读）
            name_item = QTableWidgetItem(item['item_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 0, name_item)
            
            # 数值（填充API结果或留空）
            value = api_dict.get(item['item_name'], "")
            value_item = QTableWidgetItem(str(value) if value else "")
            if value:
                value_item.setBackground(Qt.GlobalColor.yellow)  # 标记API识别的数据
            self.data_table.setItem(row, 1, value_item)
            
            # 单位（只读）
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            unit_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 2, unit_item)
    
    def _get_all_data_items(self):
        """获取所有71个数据项定义"""
        all_items = []
        
        # COMBINER ISO TEMPERATURES (7 项)
        combiner_items = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
        for item_name in combiner_items:
            all_items.append({
                'item_name': item_name,
                'unit': '°C'
            })
        
        # Z-Plane 数据 (64 项: 4 模块 × 8 行 × 2 列)
        zplane_modules = ['A', 'B', 'C', 'D']
        for module in zplane_modules:
            for row_num in range(1, 9):
                # Current
                all_items.append({
                    'item_name': f'Z-Plane {module}-Current-{row_num}',
                    'unit': 'A'
                })
                # ISO Temp
                all_items.append({
                    'item_name': f'Z-Plane {module}-ISO Temp-{row_num}',
                    'unit': '°C'
                })
        
        return all_items
    
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
                "月份格式错误\n\n正确格式：YYYY-MM，例如：2026-01"
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
                    f"第 {row + 1} 行 ({item_name}) 的数值格式错误：{value_text}"
                )
                return
            
            data_list.append({
                'item_name': item_name,
                'value': value,
                'unit': unit
            })
        
        if not data_list:
            QMessageBox.warning(
                self, "提示",
                "没有可保存的数据\n\n请至少填写一个数据项"
            )
            return
        
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
        
        # 获取选中的设备
        device_id = self.device_combo.currentData()
        if not device_id:
            QMessageBox.warning(self, "提示", "请选择要保存到的设备")
            return
        
        # 保存数据
        try:
            # 检查是否已存在数据
            existing_data = self.database.query_by_month(month, device_id)
            if not existing_data.empty:
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"设备在 {month} 已有数据\n\n是否覆盖？",
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
            
            self.clear_data()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"保存数据失败：{str(e)}"
            )
    
    def clear_data(self):
        """清空数据"""
        self.file_path_edit.clear()
        self.month_edit.clear()
        self.data_table.setRowCount(0)
        self.current_data = None
        self.current_image_path = None
        self.save_btn.setEnabled(False)
        
        self.image_label.clear()
        self.image_label.setText("选择图像后将在这里显示")
        self.image_label.setStyleSheet("color: #999; padding: 20px; background-color: #f5f5f5; border: 1px dashed #ccc;")
    
    def refresh(self):
        """刷新数据"""
        self.load_devices()
        self._load_api_config()
    
    def open_fullscreen_mode(self):
        """打开大屏模式"""
        if not self.current_image_path:
            QMessageBox.warning(self, "提示", "请先选择截图文件")
            return
        
        try:
            from src.gui.widgets.fullscreen_data_entry import FullscreenDataEntryWindow
            
            # 创建全屏窗口，传递当前数据
            self.fullscreen_window = FullscreenDataEntryWindow(
                database=self.database,
                device_manager=self.device_manager,
                settings_manager=self.settings_manager,
                image_path=self.current_image_path,
                api_ocr_extractor=self.api_extractor,
                recognized_data=self.current_data,
                parent=self
            )
            
            # 显示窗口
            self.fullscreen_window.show()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"打开大屏模式失败：{str(e)}"
            )
