"""
数据标注工具 - 用于标注发射机截图中的数字
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor


class DataLabelingTool(QMainWindow):
    """数据标注工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.labels = {}  # {cell_id: value}
        self.output_dir = Path("training_data")
        self.output_dir.mkdir(exist_ok=True)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("发射机数据标注工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # 左侧：图像显示
        left_panel = self.create_image_panel()
        layout.addWidget(left_panel, 3)
        
        # 右侧：标注表格
        right_panel = self.create_labeling_panel()
        layout.addWidget(right_panel, 2)
    
    def create_image_panel(self):
        """创建图像显示面板"""
        panel = QGroupBox("原始截图")
        layout = QVBoxLayout(panel)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        load_btn = QPushButton("📁 加载图像")
        load_btn.clicked.connect(self.load_image)
        toolbar.addWidget(load_btn)
        
        auto_detect_btn = QPushButton("🔍 自动检测单元格")
        auto_detect_btn.clicked.connect(self.auto_detect_cells)
        toolbar.addWidget(auto_detect_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 图像显示
        self.image_label = QLabel("点击 '加载图像' 开始标注")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #f5f5f5; border: 2px dashed #ccc; "
            "padding: 40px; font-size: 16px; color: #999;"
        )
        self.image_label.setMinimumSize(800, 600)
        layout.addWidget(self.image_label)
        
        return panel
    
    def create_labeling_panel(self):
        """创建标注面板"""
        panel = QGroupBox("数据标注")
        layout = QVBoxLayout(panel)
        
        # 说明
        info = QLabel(
            "📝 标注说明：\n"
            "1. 加载发射机截图\n"
            "2. 点击 '自动检测单元格'\n"
            "3. 在表格中输入每个单元格的数值\n"
            "4. 点击 '保存标注' 完成"
        )
        info.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info)
        
        # 进度
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("标注进度："))
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(71)  # 71 个数据项
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 标注表格
        self.label_table = QTableWidget()
        self.label_table.setColumnCount(3)
        self.label_table.setHorizontalHeaderLabels(["单元格 ID", "数值", "状态"])
        self.label_table.setColumnWidth(0, 200)  # 增加宽度以显示完整 ID
        self.label_table.setColumnWidth(1, 120)
        self.label_table.setColumnWidth(2, 100)
        self.label_table.itemChanged.connect(self.on_label_changed)
        layout.addWidget(self.label_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 保存标注")
        save_btn.clicked.connect(self.save_labels)
        button_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_labels)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # 统计信息
        self.stats_label = QLabel("已标注：0 / 71")
        self.stats_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(self.stats_label)
        
        return panel
    
    def load_image(self):
        """加载图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择发射机截图",
            "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        self.current_image_path = Path(file_path)
        
        # 加载图像
        pixmap = QPixmap(str(file_path))
        if pixmap.isNull():
            QMessageBox.critical(self, "错误", "无法加载图像")
            return
        
        # 缩放显示
        scaled_pixmap = pixmap.scaled(
            800, 600,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setStyleSheet("background-color: #fff; border: 1px solid #ddd;")
        
        QMessageBox.information(
            self, "提示",
            "图像加载成功！\n\n下一步：点击 '自动检测单元格' 按钮"
        )
    
    def auto_detect_cells(self):
        """自动检测单元格位置"""
        if self.current_image_path is None:
            QMessageBox.warning(self, "提示", "请先加载图像")
            return
        
        # 定义 71 个数据项
        cell_ids = []
        
        # COMBINER (7 项)
        combiner_items = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
        cell_ids.extend(combiner_items)
        
        # Z-Plane (64 项)
        for module in ['A', 'B', 'C', 'D']:
            for row in range(1, 9):
                cell_ids.append(f'Z-Plane {module}-Current-{row}')
                cell_ids.append(f'Z-Plane {module}-ISO Temp-{row}')
        
        # 暂时断开信号以避免频繁更新
        self.label_table.itemChanged.disconnect(self.on_label_changed)
        
        # 填充表格
        self.label_table.setRowCount(len(cell_ids))
        
        for row, cell_id in enumerate(cell_ids):
            # 单元格 ID
            id_item = QTableWidgetItem(cell_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            id_item.setBackground(QColor("#e8e8e8"))  # 更深的灰色背景
            id_item.setForeground(QColor("#000000"))  # 黑色文字
            self.label_table.setItem(row, 0, id_item)
            
            # 数值（可编辑）
            value_item = QTableWidgetItem("")
            value_item.setForeground(QColor("#000000"))  # 黑色文字
            self.label_table.setItem(row, 1, value_item)
            
            # 状态
            status_item = QTableWidgetItem("待标注")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setBackground(QColor("#ffecb3"))  # 更深的橙色背景
            status_item.setForeground(QColor("#000000"))  # 黑色文字
            self.label_table.setItem(row, 2, status_item)
        
        # 重新连接信号
        self.label_table.itemChanged.connect(self.on_label_changed)
        
        # 滚动到顶部
        self.label_table.scrollToTop()
        
        QMessageBox.information(
            self, "提示",
            f"✓ 已创建 {len(cell_ids)} 个标注项\n\n"
            "请在表格中输入每个单元格的数值\n\n"
            "提示：可以使用 Tab 键快速切换到下一个单元格"
        )
    
    def on_label_changed(self, item):
        """标注值改变时更新状态"""
        if item.column() != 1:  # 只处理数值列
            return
        
        row = item.row()
        value = item.text().strip()
        
        # 更新状态
        status_item = self.label_table.item(row, 2)
        if value:
            status_item.setText("已标注")
            status_item.setBackground(QColor("#a5d6a7"))  # 更深的绿色背景
            status_item.setForeground(QColor("#000000"))  # 黑色文字
        else:
            status_item.setText("待标注")
            status_item.setBackground(QColor("#ffecb3"))  # 更深的橙色背景
            status_item.setForeground(QColor("#000000"))  # 黑色文字
        
        # 更新进度
        self.update_progress()
    
    def update_progress(self):
        """更新标注进度"""
        total = self.label_table.rowCount()
        labeled = 0
        
        for row in range(total):
            value_item = self.label_table.item(row, 1)
            if value_item and value_item.text().strip():
                labeled += 1
        
        self.progress_bar.setValue(labeled)
        self.stats_label.setText(f"已标注：{labeled} / {total}")
    
    def save_labels(self):
        """保存标注数据"""
        if self.current_image_path is None:
            QMessageBox.warning(self, "提示", "请先加载图像")
            return
        
        # 收集标注数据
        labels = {}
        for row in range(self.label_table.rowCount()):
            cell_id = self.label_table.item(row, 0).text()
            value_item = self.label_table.item(row, 1)
            
            if value_item and value_item.text().strip():
                try:
                    value = float(value_item.text().strip())
                    labels[cell_id] = value
                except ValueError:
                    QMessageBox.warning(
                        self, "数据格式错误",
                        f"第 {row + 1} 行数据格式错误：{value_item.text()}"
                    )
                    return
        
        if not labels:
            QMessageBox.warning(self, "提示", "没有标注数据")
            return
        
        # 保存到文件
        output_file = self.output_dir / f"{self.current_image_path.stem}_labels.json"
        
        # ⚠️ 检查文件名是否已存在
        if output_file.exists():
            # 检查是否是同一个图像路径
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_path = existing_data.get("image_path", "")
                
                # 如果是不同的图像路径，说明文件名重复了
                if existing_path != str(self.current_image_path):
                    reply = QMessageBox.warning(
                        self, "⚠️ 文件名重复警告",
                        f"检测到文件名重复！\n\n"
                        f"当前图像：\n{self.current_image_path}\n\n"
                        f"已存在的标注文件对应图像：\n{existing_path}\n\n"
                        f"这两个不同的图像会生成相同的标注文件名：\n{output_file.name}\n\n"
                        f"⚠️ 如果继续保存，将会覆盖之前的标注数据！\n\n"
                        f"建议：\n"
                        f"1. 取消保存，重命名其中一个图像文件\n"
                        f"2. 或者确认要覆盖旧的标注数据",
                        QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel
                    )
                    
                    if reply == QMessageBox.StandardButton.Cancel:
                        return
                else:
                    # 同一个图像，只是重新标注
                    reply = QMessageBox.question(
                        self, "确认覆盖",
                        f"标注文件已存在，是否覆盖？\n\n"
                        f"文件：{output_file.name}\n"
                        f"图像：{self.current_image_path.name}",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return
            except Exception as e:
                QMessageBox.warning(
                    self, "警告",
                    f"无法读取现有标注文件：{e}\n\n是否继续保存？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
        
        data = {
            "image_path": str(self.current_image_path),
            "labels": labels,
            "total_cells": self.label_table.rowCount(),
            "labeled_cells": len(labels)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        QMessageBox.information(
            self, "保存成功",
            f"✓ 标注数据已保存\n\n"
            f"文件：{output_file}\n"
            f"已标注：{len(labels)} / {self.label_table.rowCount()}"
        )
    
    def clear_labels(self):
        """清空标注"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空所有标注吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.label_table.setRowCount(0)
            self.labels = {}
            self.progress_bar.setValue(0)
            self.stats_label.setText("已标注：0 / 71")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    window = DataLabelingTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
