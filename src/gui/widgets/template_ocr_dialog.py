"""
模板OCR识别对话框

功能：
- 图片预览和对齐
- 坐标框叠加显示
- 方向键微调位置
- 缩放调整
- 实时识别测试
- 一键识别并填入
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QGroupBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
import cv2
import numpy as np
from pathlib import Path
import json


class AlignmentWidget(QLabel):
    """图片对齐显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_image = None
        self.coords = {}
        self.reference_region = None
        self.offset_x = 0.0  # 改为浮点数支持亚像素精度
        self.offset_y = 0.0
        self.scale = 1.0
        
        self.setMinimumSize(800, 600)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid #ccc; background-color: #2b2b2b;")
    
    def load_image(self, image_path: str):
        """加载图像"""
        try:
            from PIL import Image
            import numpy as np
            
            # 使用PIL加载（跨平台兼容性最好）
            pil_image = Image.open(image_path)
            
            # 转换为RGB模式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # 转换为numpy数组，再转为BGR（OpenCV格式）
            img_rgb = np.array(pil_image)
            self.original_image = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            print(f"加载图像失败: {str(e)}")
            return False
        
        # 加载坐标
        coords_file = Path('config/template_coordinates.json')
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                self.coords = json.load(f)
        
        # 加载参照物
        ref_file = Path('config/reference_point.json')
        if ref_file.exists():
            with open(ref_file, 'r', encoding='utf-8') as f:
                ref_data = json.load(f)
                self.reference_region = ref_data.get('reference_region')
        
        # 加载已保存的偏移
        alignment_file = Path('config/image_alignment.json')
        if alignment_file.exists():
            with open(alignment_file, 'r', encoding='utf-8') as f:
                align_data = json.load(f)
                self.offset_x = align_data.get('offset_x', 0)
                self.offset_y = align_data.get('offset_y', 0)
                self.scale = align_data.get('scale', 1.0)
        
        self.update_display()
        return True
    
    def update_display(self):
        """更新显示"""
        if self.original_image is None:
            return
        
        # 应用缩放和偏移
        img = self.original_image.copy()
        h, w = img.shape[:2]
        
        if self.scale != 1.0:
            new_w = int(w * self.scale)
            new_h = int(h * self.scale)
            img = cv2.resize(img, (new_w, new_h))
        
        # 创建画布
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        canvas[:] = (50, 50, 50)
        
        # 粘贴图像（使用整数偏移）
        img_h, img_w = img.shape[:2]
        x_start = int(round(self.offset_x))  # 四舍五入到整数像素
        y_start = int(round(self.offset_y))
        x_end = x_start + img_w
        y_end = y_start + img_h
        
        src_x1 = max(0, -x_start)
        src_y1 = max(0, -y_start)
        src_x2 = img_w - max(0, x_end - w)
        src_y2 = img_h - max(0, y_end - h)
        
        dst_x1 = max(0, x_start)
        dst_y1 = max(0, y_start)
        dst_x2 = min(w, x_end)
        dst_y2 = min(h, y_end)
        
        if src_x2 > src_x1 and src_y2 > src_y1:
            canvas[dst_y1:dst_y2, dst_x1:dst_x2] = img[src_y1:src_y2, src_x1:src_x2]
        
        # 绘制坐标框
        for coords in self.coords.values():
            x1, y1, x2, y2 = coords
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 1)
        
        # 绘制参照物
        if self.reference_region:
            x1, y1, x2, y2 = self.reference_region
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 255), 3)
            cv2.putText(canvas, "REF", (x1, y1-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # 转换为QPixmap
        canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        h, w, ch = canvas_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(canvas_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # 缩放以适应窗口
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
    
    def move_offset(self, dx: float, dy: float):
        """移动偏移（支持亚像素精度）"""
        self.offset_x += dx
        self.offset_y += dy
        self.update_display()
    
    def set_scale(self, scale: float):
        """设置缩放"""
        self.scale = scale
        self.update_display()
    
    def get_aligned_image_path(self) -> str:
        """获取对齐后的图像路径"""
        if self.original_image is None:
            return None
        
        # 应用变换并保存临时图像
        img = self.original_image.copy()
        h, w = img.shape[:2]
        
        if self.scale != 1.0:
            new_w = int(w * self.scale)
            new_h = int(h * self.scale)
            img = cv2.resize(img, (new_w, new_h))
        
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        img_h, img_w = img.shape[:2]
        x_start = int(round(self.offset_x))  # 四舍五入到整数像素
        y_start = int(round(self.offset_y))
        x_end = x_start + img_w
        y_end = y_start + img_h
        
        src_x1 = max(0, -x_start)
        src_y1 = max(0, -y_start)
        src_x2 = img_w - max(0, x_end - w)
        src_y2 = img_h - max(0, y_end - h)
        
        dst_x1 = max(0, x_start)
        dst_y1 = max(0, y_start)
        dst_x2 = min(w, x_end)
        dst_y2 = min(h, y_end)
        
        if src_x2 > src_x1 and src_y2 > src_y1:
            canvas[dst_y1:dst_y2, dst_x1:dst_x2] = img[src_y1:src_y2, src_x1:src_x2]
        
        temp_path = Path('temp_aligned_image.png')
        cv2.imwrite(str(temp_path), canvas)
        return str(temp_path)


class RecognitionWorker(QThread):
    """识别工作线程"""
    
    finished = pyqtSignal(object, int)  # (结果, 识别数量)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        """执行识别"""
        try:
            self.progress.emit("正在加载模板...")
            
            from src.template_ocr_extractor import TemplateOCRExtractor
            extractor = TemplateOCRExtractor()
            
            self.progress.emit("正在识别...")
            result = extractor.extract_from_image(Path(self.image_path))
            
            self.progress.emit(f"识别完成：{len(result)} 项")
            self.finished.emit(result, len(result))
            
        except Exception as e:
            self.error.emit(f"识别失败：{str(e)}")


class TemplateOCRDialog(QDialog):
    """模板OCR识别对话框"""
    
    recognition_completed = pyqtSignal(object)  # 识别完成信号
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.recognition_result = None
        self._is_fullscreen = False  # 跟踪全屏状态
        
        self.setWindowTitle("模板OCR识别")
        self.setModal(True)
        self.resize(1000, 800)
        
        self.init_ui()
        
        # 加载图像
        if not self.alignment_widget.load_image(image_path):
            QMessageBox.critical(self, "错误", "无法加载图像")
            self.reject()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📸 图片对齐和识别")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 图片显示区域
        self.alignment_widget = AlignmentWidget()
        layout.addWidget(self.alignment_widget)
        
        # 控制面板
        controls = self._create_controls()
        layout.addWidget(controls)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("使用方向键微调图片位置，使绿色框对准数据区域")
        self.status_label.setStyleSheet("padding: 5px; color: #888;")
        layout.addWidget(self.status_label)
    
    def _create_controls(self) -> QGroupBox:
        """创建控制面板"""
        group = QGroupBox("控制")
        layout = QVBoxLayout(group)
        
        # 偏移控制
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("偏移量:"))
        
        self.offset_label = QLabel(f"X: {self.alignment_widget.offset_x:+.1f}  Y: {self.alignment_widget.offset_y:+.1f}")
        offset_layout.addWidget(self.offset_label)
        
        offset_layout.addStretch()
        layout.addLayout(offset_layout)
        
        # 缩放控制（更精细）
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放:"))
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(9800)  # 0.9800 (98%)
        self.scale_slider.setMaximum(10200)  # 1.0200 (102%)
        self.scale_slider.setValue(10000)  # 1.0000 (100%)
        self.scale_slider.setTickInterval(10)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        scale_layout.addWidget(self.scale_slider)
        
        self.scale_label = QLabel("100.00%")
        scale_layout.addWidget(self.scale_label)
        
        layout.addLayout(scale_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        fullscreen_btn = QPushButton("🖥️ 全屏模式")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        button_layout.addWidget(fullscreen_btn)
        
        test_btn = QPushButton("🧪 测试识别")
        test_btn.clicked.connect(self.test_recognition)
        button_layout.addWidget(test_btn)
        
        recognize_btn = QPushButton("✅ 识别并填入")
        recognize_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        recognize_btn.clicked.connect(self.recognize_and_accept)
        button_layout.addWidget(recognize_btn)
        
        reset_btn = QPushButton("🔄 重置")
        reset_btn.clicked.connect(self.reset_alignment)
        button_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 说明
        help_text = QLabel(
            "💡 提示：\n"
            "   • 方向键：移动1像素\n"
            "   • Shift+方向键：移动0.5像素（精细调整）\n"
            "   • 黄色框=参照物，绿色框=数据区域"
        )
        help_text.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
        layout.addWidget(help_text)
        
        return group
    
    def keyPressEvent(self, event):
        """键盘事件"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Shift键按下时使用0.5像素步进，否则使用1像素
        step = 0.5 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1.0
        
        if key == Qt.Key.Key_Up:
            self.alignment_widget.move_offset(0, -step)
            self.update_offset_label()
        elif key == Qt.Key.Key_Down:
            self.alignment_widget.move_offset(0, step)
            self.update_offset_label()
        elif key == Qt.Key.Key_Left:
            self.alignment_widget.move_offset(-step, 0)
            self.update_offset_label()
        elif key == Qt.Key.Key_Right:
            self.alignment_widget.move_offset(step, 0)
            self.update_offset_label()
        else:
            super().keyPressEvent(event)
    
    def on_scale_changed(self, value: int):
        """缩放改变"""
        scale = value / 10000.0
        self.alignment_widget.set_scale(scale)
        self.scale_label.setText(f"{scale*100:.2f}%")
    
    def update_offset_label(self):
        """更新偏移标签"""
        self.offset_label.setText(
            f"X: {self.alignment_widget.offset_x:+.1f}  "
            f"Y: {self.alignment_widget.offset_y:+.1f}"
        )
    
    def test_recognition(self):
        """测试识别"""
        aligned_path = self.alignment_widget.get_aligned_image_path()
        if not aligned_path:
            return
        
        self.status_label.setText("正在测试识别...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        worker = RecognitionWorker(aligned_path)
        worker.finished.connect(self.on_test_finished)
        worker.error.connect(self.on_test_error)
        worker.start()
        
        self.test_worker = worker
    
    def on_test_finished(self, result, count):
        """测试完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✓ 测试完成：识别到 {count}/71 项 ({count/71*100:.1f}%)")
        
        # 清理临时文件
        temp_path = Path('temp_aligned_image.png')
        if temp_path.exists():
            temp_path.unlink()
    
    def on_test_error(self, error_msg):
        """测试错误"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✗ {error_msg}")
        QMessageBox.warning(self, "测试失败", error_msg)
    
    def recognize_and_accept(self):
        """识别并接受"""
        aligned_path = self.alignment_widget.get_aligned_image_path()
        if not aligned_path:
            return
        
        self.status_label.setText("正在识别...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        worker = RecognitionWorker(aligned_path)
        worker.finished.connect(self.on_recognition_finished)
        worker.error.connect(self.on_recognition_error)
        worker.start()
        
        self.recognition_worker = worker
    
    def on_recognition_finished(self, result, count):
        """识别完成"""
        self.progress_bar.setVisible(False)
        self.recognition_result = result
        
        # 保存偏移量
        self.save_alignment()
        
        # 发送信号并关闭
        self.recognition_completed.emit(result)
        self.accept()
        
        # 清理临时文件
        temp_path = Path('temp_aligned_image.png')
        if temp_path.exists():
            temp_path.unlink()
    
    def on_recognition_error(self, error_msg):
        """识别错误"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✗ {error_msg}")
        QMessageBox.critical(self, "识别失败", error_msg)
    
    def reset_alignment(self):
        """重置对齐"""
        self.alignment_widget.offset_x = 0.0
        self.alignment_widget.offset_y = 0.0
        self.alignment_widget.scale = 1.0
        self.scale_slider.setValue(10000)
        self.alignment_widget.update_display()
        self.update_offset_label()
        self.status_label.setText("已重置对齐参数")
    
    def save_alignment(self):
        """保存对齐参数"""
        alignment_file = Path('config/image_alignment.json')
        data = {
            'offset_x': self.alignment_widget.offset_x,
            'offset_y': self.alignment_widget.offset_y,
            'scale': self.alignment_widget.scale
        }
        
        alignment_file.parent.mkdir(parents=True, exist_ok=True)
        with open(alignment_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self._is_fullscreen:
            self.showNormal()
            self._is_fullscreen = False
        else:
            self.showFullScreen()
            self._is_fullscreen = True
