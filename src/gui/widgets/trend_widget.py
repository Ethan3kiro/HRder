"""
趋势分析组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QComboBox, QDoubleSpinBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class TrendWidget(QWidget):
    """趋势分析组件"""
    
    def __init__(self, database, device_manager, visualizer, settings_manager):
        super().__init__()
        self.database = database
        self.device_manager = device_manager
        self.visualizer = visualizer
        self.settings_manager = settings_manager
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📈 趋势分析")
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
        
        # 控制面板
        control_group = QGroupBox("2. 选择数据项和时间范围")
        control_layout = QHBoxLayout()
        
        # 左侧：数据项选择
        left_panel = QVBoxLayout()
        
        item_label = QLabel("选择数据项（可多选）：")
        left_panel.addWidget(item_label)
        
        self.item_list = QListWidget()
        self.item_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.item_list.setMaximumHeight(200)
        left_panel.addWidget(self.item_list)
        
        control_layout.addLayout(left_panel, 2)
        
        # 右侧：参数设置
        right_panel = QVBoxLayout()
        
        # 时间范围
        time_label = QLabel("时间范围：")
        right_panel.addWidget(time_label)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("起始月份："))
        self.start_month_combo = QComboBox()
        self.start_month_combo.setMinimumWidth(120)
        time_layout.addWidget(self.start_month_combo)
        right_panel.addLayout(time_layout)
        
        time_layout2 = QHBoxLayout()
        time_layout2.addWidget(QLabel("结束月份："))
        self.end_month_combo = QComboBox()
        self.end_month_combo.setMinimumWidth(120)
        time_layout2.addWidget(self.end_month_combo)
        right_panel.addLayout(time_layout2)
        
        # 阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("阈值线："))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setValue(0)
        self.threshold_spin.setSuffix(" (0=不显示)")
        threshold_layout.addWidget(self.threshold_spin)
        right_panel.addLayout(threshold_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.plot_btn = QPushButton("📊 生成图表")
        self.plot_btn.clicked.connect(self.plot_trend)
        btn_layout.addWidget(self.plot_btn)
        
        self.export_btn = QPushButton("💾 导出图表")
        self.export_btn.clicked.connect(self.export_chart)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)
        
        right_panel.addLayout(btn_layout)
        right_panel.addStretch()
        
        control_layout.addLayout(right_panel, 1)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 图表区域
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
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
                self.item_list.clear()
                self.start_month_combo.clear()
                self.end_month_combo.clear()
                return
            
            device = self.device_manager.get_device_by_id(device_id)
            if not device:
                return
            
            # 获取所有数据项
            all_items = self.database.get_all_items(device_id=device_id)
            
            # 更新数据项列表
            self.item_list.clear()
            for item in all_items:
                self.item_list.addItem(item)
            
            # 获取所有月份
            months = self.database.get_available_months(device_id=device_id)
            
            # 更新月份下拉框
            self.start_month_combo.clear()
            self.end_month_combo.clear()
            
            if months:
                self.start_month_combo.addItems(months)
                self.end_month_combo.addItems(months)
                
                # 默认选择第一个和最后一个月份
                self.start_month_combo.setCurrentIndex(0)
                self.end_month_combo.setCurrentIndex(len(months) - 1)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新数据失败：{str(e)}")
    
    def plot_trend(self):
        """绘制趋势图"""
        try:
            # 获取选中的数据项
            selected_items = [item.text() for item in self.item_list.selectedItems()]
            
            if not selected_items:
                QMessageBox.warning(self, "提示", "请至少选择一个数据项")
                return
            
            # 获取时间范围
            start_month = self.start_month_combo.currentText()
            end_month = self.end_month_combo.currentText()
            
            if not start_month or not end_month:
                QMessageBox.warning(self, "提示", "请选择时间范围")
                return
            
            # 获取阈值
            threshold = self.threshold_spin.value()
            threshold = threshold if threshold > 0 else None
            
            # 获取选中的设备
            device_id = self.device_combo.currentData()
            if not device_id:
                QMessageBox.warning(self, "提示", "请先选择设备")
                return
            
            device = self.device_manager.get_device_by_id(device_id)
            if not device:
                QMessageBox.warning(self, "错误", "请先选择设备")
                return
            
            # 清空图表
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # 为每个数据项绘制折线
            import numpy as np
            colors = plt.cm.tab10(np.linspace(0, 1, len(selected_items)))
            
            for idx, item_name in enumerate(selected_items):
                # 查询数据
                df = self.database.query_by_item(item_name, device_id=device_id)
                
                if df.empty:
                    continue
                
                # 过滤月份范围
                df = df[(df['month'] >= start_month) & (df['month'] <= end_month)]
                
                if df.empty:
                    continue
                
                # 排序
                df = df.sort_values('month')
                
                months = df['month'].tolist()
                values = df['value'].tolist()
                
                # 绘制折线
                ax.plot(months, values, marker='o', markersize=6, linewidth=2,
                       label=item_name, color=colors[idx])
                
                # 标注数据点
                for month, value in zip(months, values):
                    if threshold is not None and value > threshold:
                        color = '#FF8800'
                        fontweight = 'bold'
                    else:
                        color = 'black'
                        fontweight = 'normal'
                    
                    ax.annotate(f'{value:.1f}', xy=(month, value),
                               xytext=(0, 5), textcoords='offset points',
                               ha='center', fontsize=8, color=color,
                               fontweight=fontweight)
            
            # 绘制阈值线
            if threshold is not None:
                ax.axhline(y=threshold, color='#FF8800', linestyle='--',
                          linewidth=2, label=f'阈值: {threshold}')
            
            # 设置图表属性
            ax.set_xlabel('月份', fontsize=12)
            ax.set_ylabel('数值', fontsize=12)
            ax.set_title('月度趋势图', fontsize=14, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 旋转x轴标签
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # 调整布局
            self.figure.tight_layout()
            
            # 刷新画布
            self.canvas.draw()
            
            # 启用导出按钮
            self.export_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"绘制图表失败：{str(e)}")
    
    def export_chart(self):
        """导出图表"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出图表", "", "PNG 图片 (*.png);;PDF 文件 (*.pdf)"
            )
            
            if not file_path:
                return
            
            # 保存图表
            self.figure.savefig(file_path, dpi=100, bbox_inches='tight')
            
            QMessageBox.information(self, "成功", f"图表已导出到：\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出图表失败：{str(e)}")
