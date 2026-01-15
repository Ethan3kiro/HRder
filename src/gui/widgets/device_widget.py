"""
设备管理组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog, QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class DeviceWidget(QWidget):
    """设备管理组件"""
    
    # 信号
    device_changed = pyqtSignal()
    
    def __init__(self, device_manager, database):
        super().__init__()
        self.device_manager = device_manager
        self.database = database
        self.show_id_column = False  # 默认隐藏 ID 列
        
        self.init_ui()
        self.load_devices()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📱 设备管理")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # 设备列表表格
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels([
            "ID", "设备名称", "描述", "数据记录数"
        ])
        
        # 设置列宽
        header = self.device_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置选择模式
        self.device_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.device_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        
        # 默认隐藏 ID 列
        self.device_table.setColumnHidden(0, not self.show_id_column)
        
        layout.addWidget(self.device_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        # ID 列显示开关
        self.show_id_checkbox = QCheckBox("显示 ID 列")
        self.show_id_checkbox.setChecked(self.show_id_column)
        self.show_id_checkbox.stateChanged.connect(self.toggle_id_column)
        button_layout.addWidget(self.show_id_checkbox)
        
        button_layout.addStretch()
        
        self.add_btn = QPushButton("➕ 添加设备")
        self.add_btn.clicked.connect(self.add_device)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self.edit_device)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.clicked.connect(self.delete_device)
        button_layout.addWidget(self.delete_btn)
        
        self.switch_btn = QPushButton("🔄 切换")
        self.switch_btn.clicked.connect(self.switch_device)
        button_layout.addWidget(self.switch_btn)
        
        layout.addLayout(button_layout)
    
    def toggle_id_column(self, state):
        """切换 ID 列的显示/隐藏"""
        self.show_id_column = (state == Qt.CheckState.Checked.value)
        self.device_table.setColumnHidden(0, not self.show_id_column)
    
    def load_devices(self):
        """加载设备列表"""
        try:
            devices = self.device_manager.get_all_devices()
            
            self.device_table.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                # ID
                self.device_table.setItem(
                    row, 0, QTableWidgetItem(str(device['id']))
                )
                
                # 设备名称
                self.device_table.setItem(
                    row, 1, QTableWidgetItem(device['device_name'])
                )
                
                # 描述
                desc = device.get('description', '') or ''
                self.device_table.setItem(
                    row, 2, QTableWidgetItem(desc)
                )
                
                # 数据记录数
                try:
                    months = self.database.get_available_months(device['id'])
                    count = len(months)
                except:
                    count = 0
                
                self.device_table.setItem(
                    row, 3, QTableWidgetItem(str(count))
                )
            
            print(f"✓ 已加载 {len(devices)} 个设备")
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"加载设备列表失败：\n{str(e)}"
            )
    
    def add_device(self):
        """添加设备"""
        # 输入设备名称
        name, ok = QInputDialog.getText(
            self, "添加设备", "请输入设备名称："
        )
        
        if not ok or not name.strip():
            return
        
        # 输入设备描述
        description, ok = QInputDialog.getText(
            self, "添加设备", "请输入设备描述（可选）："
        )
        
        if not ok:
            return
        
        try:
            device_id = self.device_manager.add_device(
                name.strip(), description.strip() if description else None
            )
            
            QMessageBox.information(
                self, "成功", f"设备 '{name}' 添加成功！\nID: {device_id}"
            )
            
            self.load_devices()
            self.device_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"添加设备失败：\n{str(e)}"
            )
    
    def edit_device(self):
        """编辑设备"""
        selected_rows = self.device_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要编辑的设备")
            return
        
        row = self.device_table.currentRow()
        device_id = int(self.device_table.item(row, 0).text())
        current_name = self.device_table.item(row, 1).text()
        current_desc = self.device_table.item(row, 2).text()
        
        # 输入新名称
        name, ok = QInputDialog.getText(
            self, "编辑设备", "请输入新的设备名称：",
            text=current_name
        )
        
        if not ok or not name.strip():
            return
        
        # 输入新描述
        description, ok = QInputDialog.getText(
            self, "编辑设备", "请输入新的设备描述：",
            text=current_desc
        )
        
        if not ok:
            return
        
        try:
            self.device_manager.update_device(
                device_id, name.strip(), description.strip() if description else None
            )
            
            QMessageBox.information(
                self, "成功", f"设备 '{name}' 更新成功！"
            )
            
            self.load_devices()
            self.device_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"更新设备失败：\n{str(e)}"
            )
    
    def delete_device(self):
        """删除设备"""
        selected_rows = self.device_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的设备")
            return
        
        row = self.device_table.currentRow()
        device_id = int(self.device_table.item(row, 0).text())
        device_name = self.device_table.item(row, 1).text()
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除设备 '{device_name}' 吗？\n\n"
            "注意：该设备的所有数据也将被删除！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.device_manager.delete_device(device_id, confirm=True)
            
            QMessageBox.information(
                self, "成功", f"设备 '{device_name}' 已删除"
            )
            
            self.load_devices()
            self.device_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"删除设备失败：\n{str(e)}"
            )
    
    def switch_device(self):
        """切换当前设备"""
        selected_rows = self.device_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要切换的设备")
            return
        
        row = self.device_table.currentRow()
        device_id = int(self.device_table.item(row, 0).text())
        device_name = self.device_table.item(row, 1).text()
        
        try:
            from src.settings_manager import SettingsManager
            settings_manager = SettingsManager(self.database)
            settings_manager.set_current_device_id(device_id)
            
            QMessageBox.information(
                self, "成功", f"已切换到设备：{device_name}"
            )
            
            self.device_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"切换设备失败：\n{str(e)}"
            )
    
    def refresh(self):
        """刷新数据"""
        self.load_devices()
