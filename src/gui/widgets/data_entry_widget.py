"""
数据录入组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QGroupBox, QFormLayout,
    QHeaderView, QProgressBar, QComboBox, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from pathlib import Path
import pandas as pd


class OCRWorker(QThread):
    """OCR 处理工作线程"""
    
    finished = pyqtSignal(object)  # 完成信号，传递 DataFrame
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号
    
    def __init__(self, ocr_extractor, image_path):
        super().__init__()
        self.ocr_extractor = ocr_extractor
        self.image_path = image_path
    
    def run(self):
        """执行 OCR 识别"""
        try:
            self.progress.emit("正在读取图像...")
            
            if not self.ocr_extractor:
                self.error.emit("OCR 提取器未初始化")
                return
            
            self.progress.emit("正在进行 OCR 识别...")
            result = self.ocr_extractor.extract_from_image(Path(self.image_path))
            
            self.progress.emit("识别完成！")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"OCR 识别失败：{str(e)}")


class DataEntryWidget(QWidget):
    """数据录入组件"""
    
    def __init__(self, ocr_extractor, database, device_manager, settings_manager, dl_ocr_extractor=None):
        super().__init__()
        self.ocr_extractor = ocr_extractor
        self.dl_ocr_extractor = dl_ocr_extractor
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager
        
        self.current_data = None
        self.ocr_worker = None
        self.current_image_path = None  # 保存当前图像路径
        
        self.init_ui()
    
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
        
        ocr_btn = QPushButton("🔍 OCR 识别")
        ocr_btn.clicked.connect(self.start_ocr)
        file_layout.addWidget(ocr_btn)
        
        # 添加"使用辅助模型"开关
        self.use_dl_model_checkbox = QCheckBox("🤖 使用辅助模型")
        self.use_dl_model_checkbox.setToolTip(
            "使用深度学习模型辅助识别数字\n"
            "注意：模型准确率约 12%，仅供参考"
        )
        # 只有在深度学习模型可用时才启用
        if self.dl_ocr_extractor:
            self.use_dl_model_checkbox.setEnabled(True)
            self.use_dl_model_checkbox.setChecked(False)  # 默认不使用
        else:
            self.use_dl_model_checkbox.setEnabled(False)
            self.use_dl_model_checkbox.setToolTip("深度学习模型不可用")
        file_layout.addWidget(self.use_dl_model_checkbox)
        
        # 添加全屏模式按钮
        fullscreen_btn = QPushButton("🖥️ 全屏模式")
        fullscreen_btn.clicked.connect(self.enter_fullscreen_mode)
        fullscreen_btn.setToolTip("进入全屏数据录入模式，查看更大的截图")
        file_layout.addWidget(fullscreen_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 月份输入区域 - 使用紧凑的横向布局
        month_group = QGroupBox("2. 输入月份和选择设备")
        month_layout = QHBoxLayout()
        
        # 月份输入
        month_layout.addWidget(QLabel("月份："))
        self.month_edit = QLineEdit()
        self.month_edit.setPlaceholderText("YYYY-MM")
        self.month_edit.setMaximumWidth(120)
        month_layout.addWidget(self.month_edit)
        
        # 添加间距
        month_layout.addSpacing(20)
        
        # 设备选择
        month_layout.addWidget(QLabel("保存到设备："))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(150)
        month_layout.addWidget(self.device_combo)
        
        # 添加弹性空间，让控件靠左对齐
        month_layout.addStretch()
        
        month_group.setLayout(month_layout)
        layout.addWidget(month_group)
        
        # OCR 识别结果显示区域 - 左右分栏布局
        ocr_result_group = QGroupBox("3. 原始截图 & OCR 识别结果（参考）")
        ocr_result_main_layout = QHBoxLayout()
        
        # 左侧：原始截图显示
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        image_title = QLabel("原始截图")
        image_title.setStyleSheet("font-weight: bold; color: #333;")
        image_layout.addWidget(image_title)
        
        # 图像显示标签（带滚动）
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_scroll.setMaximumHeight(200)
        image_scroll.setMinimumHeight(100)
        image_scroll.setMinimumWidth(300)
        
        self.image_label = QLabel("选择图像后将在这里显示")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #999; padding: 20px; background-color: #f5f5f5; border: 1px dashed #ccc;")
        self.image_label.setScaledContents(False)  # 不自动缩放，保持原始比例
        
        image_scroll.setWidget(self.image_label)
        image_layout.addWidget(image_scroll)
        
        ocr_result_main_layout.addWidget(image_container, 1)  # 占 1 份空间
        
        # 右侧：OCR 识别结果
        ocr_text_container = QWidget()
        ocr_text_layout = QVBoxLayout(ocr_text_container)
        ocr_text_layout.setContentsMargins(0, 0, 0, 0)
        
        ocr_text_title = QLabel("OCR 识别结果")
        ocr_text_title.setStyleSheet("font-weight: bold; color: #333;")
        ocr_text_layout.addWidget(ocr_text_title)
        
        # 使用 QScrollArea 包装 OCR 结果，限制高度
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)  # 限制最大高度为 200 像素
        scroll_area.setMinimumHeight(100)  # 最小高度 100 像素
        
        self.ocr_result_label = QLabel("OCR 识别到的所有数字将显示在这里，供您参考填写")
        self.ocr_result_label.setWordWrap(True)
        self.ocr_result_label.setStyleSheet("color: #666; padding: 10px;")
        
        scroll_area.setWidget(self.ocr_result_label)
        ocr_text_layout.addWidget(scroll_area)
        
        ocr_result_main_layout.addWidget(ocr_text_container, 1)  # 占 1 份空间
        
        ocr_result_group.setLayout(ocr_result_main_layout)
        layout.addWidget(ocr_result_group)
        
        # 数据预览区域
        preview_group = QGroupBox("4. 数据填写表格")
        preview_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setHorizontalHeaderLabels(["数据项名称", "数值", "单位"])
        self.data_table.setMinimumHeight(400)  # 设置最小高度，确保有足够空间显示数据
        
        # 设置列宽
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        preview_layout.addWidget(self.data_table)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存到数据库")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(clear_btn)
        
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
                
                # 默认选择当前设备
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
    
    def load_image_preview(self, image_path):
        """加载并显示图像预览"""
        try:
            self.current_image_path = image_path
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                self.image_label.setText("无法加载图像")
                self.image_label.setStyleSheet("color: #f44336; padding: 20px; background-color: #ffebee; border: 1px solid #f44336;")
                return
            
            # 缩放图像以适应显示区域（保持宽高比）
            scaled_pixmap = pixmap.scaled(
                400, 180,  # 最大宽度和高度
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("padding: 5px; background-color: #fff; border: 1px solid #ddd;")
            
        except Exception as e:
            self.image_label.setText(f"加载图像失败：{str(e)}")
            self.image_label.setStyleSheet("color: #f44336; padding: 20px; background-color: #ffebee; border: 1px solid #f44336;")
    
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
            # 加载并显示图像预览
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
        
        # 检查是否使用深度学习模型
        use_dl_model = self.use_dl_model_checkbox.isChecked()
        
        if use_dl_model:
            if not self.dl_ocr_extractor:
                QMessageBox.critical(
                    self, "错误",
                    "深度学习模型不可用\n\n请确保模型文件存在:\n"
                    "- models/digit_ocr_model.pth\n"
                    "- models/coordinates.json"
                )
                return
            extractor = self.dl_ocr_extractor
        else:
            if not self.ocr_extractor:
                QMessageBox.critical(
                    self, "错误", 
                    "OCR 提取器未初始化\n\n请确保已安装 Tesseract-OCR"
                )
                return
            extractor = self.ocr_extractor
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 创建并启动工作线程
        self.ocr_worker = OCRWorker(extractor, file_path)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.progress.connect(self.on_ocr_progress)
        self.ocr_worker.start()
    
    def on_ocr_progress(self, message):
        """OCR 进度更新"""
        self.progress_bar.setFormat(message)
    
    def on_ocr_finished(self, data):
        """OCR 完成"""
        self.progress_bar.setVisible(False)
        
        # 显示 OCR 识别的原始结果
        if data is not None and not data.empty:
            ocr_summary = "OCR 识别到以下数字（请参考这些数字填写到正确的位置）：\n\n"
            
            # 按分类显示
            combiner_data = data[data['item_name'].isin(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD'])]
            if not combiner_data.empty:
                ocr_summary += "【COMBINER】\n"
                for _, row in combiner_data.iterrows():
                    ocr_summary += f"  • {row['item_name']}: {row['value']} {row['unit']}\n"
                ocr_summary += "\n"
            
            # Z-Plane 数据
            for module in ['A', 'B', 'C', 'D']:
                module_data = data[data['item_name'].str.contains(f'Z-Plane {module}')]
                if not module_data.empty:
                    ocr_summary += f"【Z-Plane {module}】\n"
                    for _, row in module_data.iterrows():
                        ocr_summary += f"  • {row['item_name']}: {row['value']} {row['unit']}\n"
                    ocr_summary += "\n"
            
            self.ocr_result_label.setText(ocr_summary)
            self.ocr_result_label.setStyleSheet("color: #000; padding: 10px; background-color: #e8f5e9; border: 1px solid #4caf50; border-radius: 4px; font-family: monospace;")
        else:
            self.ocr_result_label.setText("未识别到任何数据，请手动填写所有数据")
            self.ocr_result_label.setStyleSheet("color: #666; padding: 10px; background-color: #fff3e0; border: 1px solid #ff9800; border-radius: 4px;")
        
        # 显示空白模板供用户填写
        self.current_data = pd.DataFrame()  # 不自动填充，让用户参考 OCR 结果手动填写
        self.display_data_with_template(self.current_data)
        self.save_btn.setEnabled(True)
        
        if data is None or data.empty:
            QMessageBox.information(
                self, "提示", 
                f"未能识别到数据\n\n已显示完整的数据项模板，请手动填写所有数据"
            )
        else:
            recognized_count = len(data)
            total_count = 71  # 7 COMBINER + 64 Z-Plane
            
            QMessageBox.information(
                self, "识别完成", 
                f"✓ OCR 识别到 {recognized_count} 个数字\n\n"
                f"这些数字显示在上方的参考区域\n"
                f"请参考这些数字，手动填写到下方表格的正确位置\n\n"
                f"提示：OCR 可能会把数字放错位置，请仔细核对原始截图"
            )
    
    def on_ocr_error(self, error_msg):
        """OCR 错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", error_msg)
    
    def display_data(self, data):
        """显示数据"""
        self.data_table.setRowCount(len(data))
        
        for row, (_, item) in enumerate(data.iterrows()):
            # 数据项名称
            name_item = QTableWidgetItem(str(item['item_name']))
            self.data_table.setItem(row, 0, name_item)
            
            # 数值
            value_item = QTableWidgetItem(str(item['value']))
            self.data_table.setItem(row, 1, value_item)
            
            # 单位
            unit_item = QTableWidgetItem(str(item['unit']))
            self.data_table.setItem(row, 2, unit_item)
    
    def display_data_with_template(self, ocr_data):
        """显示完整的数据模板（空白），OCR 结果仅作为参考显示"""
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
            for row_num in range(1, 9):  # 8 行
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
        
        # 显示到表格（全部留空，让用户参考 OCR 结果手动填写）
        self.data_table.setRowCount(len(all_items))
        
        for row, item in enumerate(all_items):
            # 数据项名称（只读）
            name_item = QTableWidgetItem(item['item_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setBackground(Qt.GlobalColor.lightGray)
            self.data_table.setItem(row, 0, name_item)
            
            # 数值（可编辑，全部留空）
            value_item = QTableWidgetItem(item['value'])
            value_item.setBackground(Qt.GlobalColor.white)  # 白色背景表示待填写
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
                "月份格式错误\n\n正确格式：YYYY-MM，例如：2026-01"
            )
            return
        
        # 从表格获取数据
        data_list = []
        empty_count = 0
        invalid_rows = []
        
        for row in range(self.data_table.rowCount()):
            item_name = self.data_table.item(row, 0).text()
            value_text = self.data_table.item(row, 1).text().strip()
            unit = self.data_table.item(row, 2).text()
            
            # 跳过空值
            if not value_text:
                empty_count += 1
                continue
            
            # 验证数值格式
            try:
                value = float(value_text)
            except ValueError:
                invalid_rows.append(f"第 {row + 1} 行 ({item_name}): {value_text}")
                continue
            
            data_list.append({
                'item_name': item_name,
                'value': value,
                'unit': unit
            })
        
        # 检查是否有无效数据
        if invalid_rows:
            QMessageBox.warning(
                self, "数据格式错误", 
                f"以下数据格式错误，请修正：\n\n" + "\n".join(invalid_rows[:5]) +
                (f"\n\n...还有 {len(invalid_rows) - 5} 个错误" if len(invalid_rows) > 5 else "")
            )
            return
        
        # 检查是否有数据
        if not data_list:
            QMessageBox.warning(
                self, "提示", 
                "没有可保存的数据\n\n请至少填写一个数据项"
            )
            return
        
        # 提示用户有多少数据未填写
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
        
        # 检查是否已存在数据
        try:
            existing_data = self.database.query_by_month(month, device_id)
            if not existing_data.empty:
                # 获取设备名称用于显示
                device = self.device_manager.get_device_by_id(device_id)
                device_name = device['device_name'] if device else device_id
                
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"设备 '{device_name}' 在 {month} 已有数据\n\n是否覆盖？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
                
                # 删除旧数据
                self.database.delete_month(month, device_id)
        except:
            pass
        
        # 保存数据
        try:
            self.database.insert_monthly_data(month, data_df, overwrite=False, device_id=device_id)
            
            QMessageBox.information(
                self, "保存成功", 
                f"✓ 成功保存 {len(data_df)} 条数据到 {month}\n"
                f"⚠ {empty_count} 条数据未填写（已跳过）"
            )
            
            # 清空表单
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
        
        # 清空图像显示
        self.image_label.clear()
        self.image_label.setText("选择图像后将在这里显示")
        self.image_label.setStyleSheet("color: #999; padding: 20px; background-color: #f5f5f5; border: 1px dashed #ccc;")
        
        # 清空 OCR 结果显示
        self.ocr_result_label.setText("OCR 识别到的所有数字将显示在这里，供您参考填写")
        self.ocr_result_label.setStyleSheet("color: #666; padding: 10px;")
    
    def enter_fullscreen_mode(self):
        """进入全屏数据录入模式"""
        from .fullscreen_data_entry import FullscreenDataEntryWindow
        
        # 创建全屏窗口
        self.fullscreen_window = FullscreenDataEntryWindow(
            ocr_extractor=self.ocr_extractor,
            database=self.database,
            device_manager=self.device_manager,
            settings_manager=self.settings_manager,
            image_path=self.current_image_path,  # 传递当前图像路径
            dl_ocr_extractor=self.dl_ocr_extractor,  # 传递深度学习提取器
            parent=self
        )
        
        # 连接关闭信号，在全屏窗口关闭后刷新主窗口
        self.fullscreen_window.closed.connect(self.on_fullscreen_closed)
        
        # 显示全屏窗口
        self.fullscreen_window.show()
    
    def on_fullscreen_closed(self):
        """全屏窗口关闭后的处理"""
        # 刷新设备列表（可能在全屏模式下有变化）
        self.load_devices()
        
        # 清理全屏窗口引用
        if hasattr(self, 'fullscreen_window'):
            self.fullscreen_window.deleteLater()
            self.fullscreen_window = None
    
    def refresh(self):
        """刷新数据"""
        self.load_devices()
