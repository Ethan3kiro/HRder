"""
两月对比组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path


class ComparisonWidget(QWidget):
    """两月对比组件"""
    
    def __init__(self, analyzer, database, device_manager, visualizer, exporter, settings_manager):
        super().__init__()
        self.analyzer = analyzer
        self.database = database
        self.device_manager = device_manager
        self.visualizer = visualizer
        self.exporter = exporter
        self.settings_manager = settings_manager
        
        self.comparison_result = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📊 两月对比")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 设备选择区域
        device_group = QGroupBox("1. 选择设备")
        device_layout = QHBoxLayout()
        
        device_layout.addWidget(QLabel("设备："))
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # 月份选择区域
        month_group = QGroupBox("2. 选择对比月份")
        month_layout = QHBoxLayout()
        
        month_layout.addWidget(QLabel("第一个月份："))
        self.month1_combo = QComboBox()
        month_layout.addWidget(self.month1_combo)
        
        month_layout.addWidget(QLabel("第二个月份："))
        self.month2_combo = QComboBox()
        month_layout.addWidget(self.month2_combo)
        
        compare_btn = QPushButton("🔍 开始对比")
        compare_btn.clicked.connect(self.start_comparison)
        month_layout.addWidget(compare_btn)
        
        month_layout.addStretch()
        
        month_group.setLayout(month_layout)
        layout.addWidget(month_group)
        
        # 对比结果表格
        result_group = QGroupBox("3. 对比结果")
        result_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels([
            "数据项", f"{self.month1_combo.currentText()}", 
            f"{self.month2_combo.currentText()}", "单位",
            "绝对变化", "相对变化(%)", "状态"
        ])
        
        # 设置列宽
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        result_layout.addWidget(self.result_table)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.export_excel_btn = QPushButton("📊 导出 Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.export_excel_btn.setEnabled(False)
        button_layout.addWidget(self.export_excel_btn)
        
        self.export_chart_btn = QPushButton("📈 导出图表")
        self.export_chart_btn.clicked.connect(self.export_chart)
        self.export_chart_btn.setEnabled(False)
        button_layout.addWidget(self.export_chart_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 加载设备列表和月份列表
        self.load_devices()
        self.load_months()
    
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
    
    def on_device_changed(self):
        """设备改变时重新加载月份"""
        self.load_months()
    
    def load_months(self):
        """加载月份列表"""
        try:
            # 获取选中的设备 ID
            device_id = self.device_combo.currentData()
            if not device_id:
                self.month1_combo.clear()
                self.month2_combo.clear()
                return
            
            months = self.database.get_available_months(device_id)
            
            self.month1_combo.clear()
            self.month2_combo.clear()
            
            if months:
                self.month1_combo.addItems(months)
                self.month2_combo.addItems(months)
                
                # 默认选择最后两个月
                if len(months) >= 2:
                    self.month1_combo.setCurrentIndex(len(months) - 2)
                    self.month2_combo.setCurrentIndex(len(months) - 1)
        
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"加载月份列表失败：{str(e)}"
            )
    
    def start_comparison(self):
        """开始对比"""
        month1 = self.month1_combo.currentText()
        month2 = self.month2_combo.currentText()
        
        if not month1 or not month2:
            QMessageBox.warning(self, "提示", "请选择两个月份")
            return
        
        if month1 == month2:
            QMessageBox.warning(self, "提示", "请选择不同的月份")
            return
        
        try:
            # 获取选中的设备 ID
            device_id = self.device_combo.currentData()
            if not device_id:
                QMessageBox.warning(self, "提示", "请先选择设备")
                return
            
            # 执行对比
            self.comparison_result = self.analyzer.compare_two_months(
                month1, month2, device_id
            )
            
            if self.comparison_result.empty:
                QMessageBox.warning(
                    self, "提示",
                    "没有可对比的数据\n\n两个月份可能没有共同的数据项"
                )
                return
            
            # 显示结果
            self.display_comparison(self.comparison_result, month1, month2)
            
            # 启用导出按钮
            self.export_excel_btn.setEnabled(True)
            self.export_chart_btn.setEnabled(True)
            
            QMessageBox.information(
                self, "成功",
                f"对比完成！\n\n共对比 {len(self.comparison_result)} 个数据项"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"对比失败：{str(e)}"
            )
    
    def display_comparison(self, result, month1, month2):
        """显示对比结果"""
        # 更新表头
        self.result_table.setHorizontalHeaderLabels([
            "数据项", month1, month2, "单位",
            "绝对变化", "相对变化(%)", "状态"
        ])
        
        self.result_table.setRowCount(len(result))
        
        # 获取灵敏度阈值
        threshold = self.settings_manager.get_sensitivity_threshold()
        
        for row, (_, item) in enumerate(result.iterrows()):
            # 数据项名称
            self.result_table.setItem(
                row, 0, QTableWidgetItem(str(item['item_name']))
            )
            
            # 第一个月数值
            self.result_table.setItem(
                row, 1, QTableWidgetItem(f"{item['value_month1']:.2f}")
            )
            
            # 第二个月数值
            self.result_table.setItem(
                row, 2, QTableWidgetItem(f"{item['value_month2']:.2f}")
            )
            
            # 单位
            self.result_table.setItem(
                row, 3, QTableWidgetItem(str(item['unit']))
            )
            
            # 绝对变化
            abs_change = item['absolute_change']
            abs_item = QTableWidgetItem(f"{abs_change:+.2f}")
            self.result_table.setItem(row, 4, abs_item)
            
            # 相对变化
            rel_change = item['relative_change']
            rel_item = QTableWidgetItem(f"{rel_change:+.2f}")
            self.result_table.setItem(row, 5, rel_item)
            
            # 状态
            status = item['change_status']
            if status == 'increase':
                status_text = "↑ 增长"
                color = QColor(255, 68, 68)  # 红色
            elif status == 'decrease':
                status_text = "↓ 下降"
                color = QColor(68, 255, 68)  # 绿色
            else:
                status_text = "→ 无变化"
                color = QColor(200, 200, 200)  # 灰色
            
            # 检查是否超过阈值
            if abs(rel_change) >= threshold:
                status_text += " ⚠️"
            
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(color)
            self.result_table.setItem(row, 6, status_item)
            
            # 设置行颜色
            if abs(rel_change) >= threshold:
                for col in range(7):
                    item = self.result_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 255, 200, 100))
    
    def export_excel(self):
        """导出 Excel"""
        if self.comparison_result is None or self.comparison_result.empty:
            QMessageBox.warning(self, "提示", "没有可导出的数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 Excel",
            f"对比报告_{self.month1_combo.currentText()}_vs_{self.month2_combo.currentText()}.xlsx",
            "Excel 文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.exporter.export_comparison_report(
                    self.comparison_result,
                    Path(file_path)
                )
                
                QMessageBox.information(
                    self, "成功",
                    f"已导出到：\n{file_path}"
                )
            
            except Exception as e:
                QMessageBox.critical(
                    self, "错误",
                    f"导出失败：{str(e)}"
                )
    
    def export_chart(self):
        """导出图表"""
        if self.comparison_result is None or self.comparison_result.empty:
            QMessageBox.warning(self, "提示", "没有可导出的数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图表",
            f"对比图表_{self.month1_combo.currentText()}_vs_{self.month2_combo.currentText()}.png",
            "PNG 图像 (*.png);;PDF 文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.visualizer.plot_comparison_chart(
                    self.comparison_result,
                    Path(file_path)
                )
                
                QMessageBox.information(
                    self, "成功",
                    f"已导出到：\n{file_path}"
                )
            
            except Exception as e:
                QMessageBox.critical(
                    self, "错误",
                    f"导出失败：{str(e)}"
                )
    
    def refresh(self):
        """刷新数据"""
        self.load_devices()
        self.load_months()
