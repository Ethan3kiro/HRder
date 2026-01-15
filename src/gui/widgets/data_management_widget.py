"""
数据管理组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QFileDialog, QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt
from pathlib import Path
import pandas as pd


class DataManagementWidget(QWidget):
    """数据管理组件"""
    
    def __init__(self, database, device_manager, exporter, settings_manager):
        super().__init__()
        self.database = database
        self.device_manager = device_manager
        self.exporter = exporter
        self.settings_manager = settings_manager
        
        self.current_data = []
        self.show_id_column = False  # 默认隐藏 ID 列
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("💾 数据管理")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 设备选择区域
        from PyQt6.QtWidgets import QGroupBox
        device_group = QGroupBox("1. 选择设备")
        device_layout = QHBoxLayout()
        
        device_layout.addWidget(QLabel("设备："))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # 搜索和筛选栏
        filter_group = QGroupBox("2. 筛选和搜索")
        filter_layout = QHBoxLayout()
        
        # 月份筛选
        filter_layout.addWidget(QLabel("月份："))
        self.month_filter = QComboBox()
        self.month_filter.addItem("全部")
        self.month_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.month_filter)
        
        # 数据项搜索
        filter_layout.addWidget(QLabel("数据项："))
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("输入数据项名称搜索...")
        self.item_search.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.item_search)
        
        # ID 列显示开关
        self.show_id_checkbox = QCheckBox("显示 ID 列")
        self.show_id_checkbox.setChecked(self.show_id_column)
        self.show_id_checkbox.stateChanged.connect(self.toggle_id_column)
        filter_layout.addWidget(self.show_id_checkbox)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(6)
        self.data_table.setHorizontalHeaderLabels([
            "ID", "月份", "数据项", "数值", "单位", "创建时间"
        ])
        
        # 设置表格属性
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.data_table.setAlternatingRowColors(True)
        
        # 默认隐藏 ID 列
        self.data_table.setColumnHidden(0, not self.show_id_column)
        
        layout.addWidget(self.data_table)
        
        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setObjectName("infoText")
        layout.addWidget(self.stats_label)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("🗑️ 删除选中")
        self.delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        self.export_excel_btn = QPushButton("📊 导出 Excel")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        btn_layout.addWidget(self.export_excel_btn)
        
        self.export_csv_btn = QPushButton("📄 导出 CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        btn_layout.addWidget(self.export_csv_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 加载设备列表
        self.load_devices()
        # 初始化数据
        self.refresh()
    
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
        """设备改变时重新加载数据"""
        self.refresh()
    
    def refresh(self):
        """刷新数据"""
        try:
            # 获取选中的设备 ID
            device_id = self.device_combo.currentData()
            if not device_id:
                self.data_table.setRowCount(0)
                self.stats_label.setText("请先选择设备")
                return
            
            device = self.device_manager.get_device_by_id(device_id)
            if not device:
                self.data_table.setRowCount(0)
                self.stats_label.setText("请先选择设备")
                return
            
            # 获取所有月份
            months = self.database.get_available_months(device_id=device_id)
            
            # 更新月份筛选
            current_month = self.month_filter.currentText()
            self.month_filter.clear()
            self.month_filter.addItem("全部")
            self.month_filter.addItems(months)
            
            # 恢复之前的选择
            if current_month in months:
                self.month_filter.setCurrentText(current_month)
            
            # 获取所有数据
            query = """
                SELECT id, month, item_name, value, unit, create_time
                FROM transmitter_data
                WHERE device_id = ?
                ORDER BY month DESC, item_name ASC
            """
            
            cursor = self.database.connection.cursor()
            cursor.execute(query, (device_id,))
            rows = cursor.fetchall()
            
            self.current_data = [dict(row) for row in rows]
            
            # 应用筛选
            self.apply_filters()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新数据失败：{str(e)}")
    
    def apply_filters(self):
        """应用筛选条件"""
        try:
            # 获取筛选条件
            month_filter = self.month_filter.currentText()
            item_search = self.item_search.text().strip().lower()
            
            # 筛选数据
            filtered_data = self.current_data
            
            if month_filter != "全部":
                filtered_data = [d for d in filtered_data if d['month'] == month_filter]
            
            if item_search:
                filtered_data = [d for d in filtered_data 
                               if item_search in d['item_name'].lower()]
            
            # 更新表格
            self.data_table.setRowCount(len(filtered_data))
            
            for row_idx, data in enumerate(filtered_data):
                self.data_table.setItem(row_idx, 0, QTableWidgetItem(str(data['id'])))
                self.data_table.setItem(row_idx, 1, QTableWidgetItem(data['month']))
                self.data_table.setItem(row_idx, 2, QTableWidgetItem(data['item_name']))
                self.data_table.setItem(row_idx, 3, QTableWidgetItem(f"{data['value']:.2f}"))
                self.data_table.setItem(row_idx, 4, QTableWidgetItem(data['unit'] or ''))
                self.data_table.setItem(row_idx, 5, QTableWidgetItem(data['create_time']))
            
            # 更新统计信息
            total_count = len(self.current_data)
            filtered_count = len(filtered_data)
            
            if month_filter != "全部" or item_search:
                self.stats_label.setText(
                    f"显示 {filtered_count} 条记录（共 {total_count} 条）"
                )
            else:
                self.stats_label.setText(f"共 {total_count} 条记录")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用筛选失败：{str(e)}")
    
    def toggle_id_column(self, state):
        """切换 ID 列的显示/隐藏"""
        self.show_id_column = (state == Qt.CheckState.Checked.value)
        self.data_table.setColumnHidden(0, not self.show_id_column)
    
    def delete_selected(self):
        """删除选中的记录"""
        try:
            # 获取选中的行
            selected_rows = set(item.row() for item in self.data_table.selectedItems())
            
            if not selected_rows:
                QMessageBox.warning(self, "提示", "请先选择要删除的记录")
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除选中的 {len(selected_rows)} 条记录吗？\n此操作不可恢复！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # 获取要删除的 ID
            ids_to_delete = []
            for row in selected_rows:
                id_item = self.data_table.item(row, 0)
                if id_item:
                    ids_to_delete.append(int(id_item.text()))
            
            # 删除记录
            cursor = self.database.connection.cursor()
            for record_id in ids_to_delete:
                cursor.execute("DELETE FROM transmitter_data WHERE id = ?", (record_id,))
            
            self.database.connection.commit()
            
            QMessageBox.information(self, "成功", f"已删除 {len(ids_to_delete)} 条记录")
            
            # 刷新数据
            self.refresh()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除记录失败：{str(e)}")
    
    def export_to_excel(self):
        """导出到 Excel"""
        try:
            # 获取当前显示的数据
            if self.data_table.rowCount() == 0:
                QMessageBox.warning(self, "提示", "没有数据可导出")
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出 Excel", "", "Excel 文件 (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # 收集表格数据
            data = []
            for row in range(self.data_table.rowCount()):
                row_data = {
                    'ID': self.data_table.item(row, 0).text(),
                    '月份': self.data_table.item(row, 1).text(),
                    '数据项': self.data_table.item(row, 2).text(),
                    '数值': float(self.data_table.item(row, 3).text()),
                    '单位': self.data_table.item(row, 4).text(),
                    '创建时间': self.data_table.item(row, 5).text(),
                }
                data.append(row_data)
            
            # 创建 DataFrame
            df = pd.DataFrame(data)
            
            # 导出到 Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            QMessageBox.information(self, "成功", f"数据已导出到：\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 Excel 失败：{str(e)}")
    
    def export_to_csv(self):
        """导出到 CSV"""
        try:
            # 获取当前显示的数据
            if self.data_table.rowCount() == 0:
                QMessageBox.warning(self, "提示", "没有数据可导出")
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出 CSV", "", "CSV 文件 (*.csv)"
            )
            
            if not file_path:
                return
            
            # 收集表格数据
            data = []
            for row in range(self.data_table.rowCount()):
                row_data = {
                    'ID': self.data_table.item(row, 0).text(),
                    '月份': self.data_table.item(row, 1).text(),
                    '数据项': self.data_table.item(row, 2).text(),
                    '数值': float(self.data_table.item(row, 3).text()),
                    '单位': self.data_table.item(row, 4).text(),
                    '创建时间': self.data_table.item(row, 5).text(),
                }
                data.append(row_data)
            
            # 创建 DataFrame
            df = pd.DataFrame(data)
            
            # 导出到 CSV
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            QMessageBox.information(self, "成功", f"数据已导出到：\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 CSV 失败：{str(e)}")
