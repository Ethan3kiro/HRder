#!/usr/bin/env python3
"""
图片对齐预览工具

功能：
- 显示图片和所有坐标框
- 支持方向键微调图片位置
- 支持缩放调整
- 实时显示识别结果
- 自动保存偏移量
"""
import cv2
import json
import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.template_ocr_extractor import TemplateOCRExtractor


class ImageAligner:
    """图片对齐器"""
    
    def __init__(self, image_path: Path, coords_file: Path):
        """初始化"""
        self.image_path = Path(image_path)
        self.coords_file = Path(coords_file)
        
        # 加载图像
        self.original_image = cv2.imread(str(self.image_path))
        if self.original_image is None:
            raise ValueError(f"无法读取图像: {self.image_path}")
        
        self.height, self.width = self.original_image.shape[:2]
        
        # 加载坐标
        with open(self.coords_file, 'r', encoding='utf-8') as f:
            self.coords = json.load(f)
        
        # 加载参照物（如果存在）
        self.reference_region = None
        ref_file = Path('config/reference_point.json')
        if ref_file.exists():
            with open(ref_file, 'r', encoding='utf-8') as f:
                ref_data = json.load(f)
                self.reference_region = ref_data.get('reference_region')
                print(f"✓ 已加载参照物: {self.reference_region}")
        
        # 偏移量和缩放
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        self.move_step = 1
        
        # OCR提取器
        self.extractor = TemplateOCRExtractor(self.coords_file)
        
        print(f"✓ 图像加载成功: {self.image_path}")
        print(f"  尺寸: {self.width} x {self.height}")
        print(f"  坐标数量: {len(self.coords)}")
        print()
    
    def run(self):
        """运行对齐工具"""
        window_name = 'Image Aligner'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        self._print_help()
        
        while True:
            display = self._create_display()
            cv2.imshow(window_name, display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                self._save_offset()
            elif key == ord('r'):
                self._reset_offset()
            elif key == ord('t'):
                self._test_recognition()
            elif key == 82 or key == 0:  # 上箭头
                self.offset_y -= self.move_step
            elif key == 84 or key == 1:  # 下箭头
                self.offset_y += self.move_step
            elif key == 81 or key == 2:  # 左箭头
                self.offset_x -= self.move_step
            elif key == 83 or key == 3:  # 右箭头
                self.offset_x += self.move_step
            elif key == ord('+') or key == ord('='):
                self.scale = min(1.05, self.scale + 0.001)
                print(f"缩放: {self.scale:.3f}")
            elif key == ord('-') or key == ord('_'):
                self.scale = max(0.95, self.scale - 0.001)
                print(f"缩放: {self.scale:.3f}")
        
        cv2.destroyAllWindows()
    
    def _create_display(self) -> np.ndarray:
        """创建显示"""
        # 应用缩放和偏移
        if self.scale != 1.0:
            new_width = int(self.width * self.scale)
            new_height = int(self.height * self.scale)
            image = cv2.resize(self.original_image, (new_width, new_height))
        else:
            image = self.original_image.copy()
        
        # 创建画布（与原图尺寸相同）
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        canvas[:] = (50, 50, 50)  # 灰色背景
        
        # 计算粘贴位置
        img_h, img_w = image.shape[:2]
        x_start = self.offset_x
        y_start = self.offset_y
        x_end = x_start + img_w
        y_end = y_start + img_h
        
        # 计算有效区域
        src_x1 = max(0, -x_start)
        src_y1 = max(0, -y_start)
        src_x2 = img_w - max(0, x_end - self.width)
        src_y2 = img_h - max(0, y_end - self.height)
        
        dst_x1 = max(0, x_start)
        dst_y1 = max(0, y_start)
        dst_x2 = min(self.width, x_end)
        dst_y2 = min(self.height, y_end)
        
        # 粘贴图像
        if src_x2 > src_x1 and src_y2 > src_y1:
            canvas[dst_y1:dst_y2, dst_x1:dst_x2] = image[src_y1:src_y2, src_x1:src_x2]
        
        # 绘制所有坐标框
        for name, coords in self.coords.items():
            x1, y1, x2, y2 = coords
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 0), 1)
        
        # 绘制参照物框（如果存在）- 用不同颜色突出显示
        if self.reference_region:
            x1, y1, x2, y2 = self.reference_region
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 255, 255), 3)  # 黄色，粗线
            
            # 添加文字标签
            cv2.putText(canvas, "REFERENCE", (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 添加十字中心线（辅助对齐）
        cv2.line(canvas, (self.width//2, 0), (self.width//2, self.height), 
                (100, 100, 100), 1)
        cv2.line(canvas, (0, self.height//2), (self.width, self.height//2),
                (100, 100, 100), 1)
        
        # 添加状态栏
        status_bar = self._create_status_bar()
        display = np.vstack([canvas, status_bar])
        
        return display
    
    def _create_status_bar(self) -> np.ndarray:
        """创建状态栏"""
        bar_height = 120
        bar = np.zeros((bar_height, self.width, 3), dtype=np.uint8)
        bar[:] = (40, 40, 40)
        
        y_pos = 25
        texts = [
            f"偏移: X={self.offset_x:+d}  Y={self.offset_y:+d}",
            f"缩放: {self.scale:.3f}",
        ]
        
        if self.reference_region:
            texts.append("参照物: 黄色框")
        
        texts.append("方向键:移动 | +/-:缩放 | T:测试识别 | S:保存 | R:重置 | Q:退出")
        
        for text in texts:
            cv2.putText(bar, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_pos += 30
        
        return bar
    
    def _test_recognition(self):
        """测试当前偏移下的识别效果"""
        print("\n测试识别...")
        
        # 应用偏移和缩放创建临时图像
        if self.scale != 1.0 or self.offset_x != 0 or self.offset_y != 0:
            # 先缩放
            if self.scale != 1.0:
                new_width = int(self.width * self.scale)
                new_height = int(self.height * self.scale)
                scaled = cv2.resize(self.original_image, (new_width, new_height))
            else:
                scaled = self.original_image.copy()
            
            # 再平移
            canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            img_h, img_w = scaled.shape[:2]
            
            x_start = self.offset_x
            y_start = self.offset_y
            x_end = x_start + img_w
            y_end = y_start + img_h
            
            src_x1 = max(0, -x_start)
            src_y1 = max(0, -y_start)
            src_x2 = img_w - max(0, x_end - self.width)
            src_y2 = img_h - max(0, y_end - self.height)
            
            dst_x1 = max(0, x_start)
            dst_y1 = max(0, y_start)
            dst_x2 = min(self.width, x_end)
            dst_y2 = min(self.height, y_end)
            
            if src_x2 > src_x1 and src_y2 > src_y1:
                canvas[dst_y1:dst_y2, dst_x1:dst_x2] = scaled[src_y1:src_y2, src_x1:src_x2]
            
            # 保存临时图像
            temp_path = Path('temp_aligned.png')
            cv2.imwrite(str(temp_path), canvas)
            
            # 识别
            results = self.extractor.extract_from_image(temp_path)
            
            # 删除临时文件
            temp_path.unlink()
        else:
            results = self.extractor.extract_from_image(self.image_path)
        
        print(f"✓ 识别到 {len(results)}/71 项 ({len(results)/71*100:.1f}%)")
        if len(results) < 71:
            print(f"  缺失 {71 - len(results)} 项")
    
    def _save_offset(self):
        """保存偏移量"""
        offset_file = Path('config/image_alignment.json')
        data = {
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "scale": self.scale
        }
        
        offset_file.parent.mkdir(parents=True, exist_ok=True)
        with open(offset_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ 偏移量已保存: {offset_file}")
        print(f"  X: {self.offset_x}, Y: {self.offset_y}, Scale: {self.scale:.3f}")
    
    def _reset_offset(self):
        """重置偏移"""
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        print("\n✓ 已重置偏移")
    
    def _print_help(self):
        """打印帮助"""
        print("="*70)
        print("  图片对齐工具")
        print("="*70)
        print("  使用说明：")
        print("    1. 用方向键微调图片位置，使数据区域对准绿色框")
        print("    2. 用 +/- 键微调缩放（如果图片略有尺寸差异）")
        print("    3. 按 T 键测试当前设置下的识别率")
        print("    4. 满意后按 S 保存偏移量")
        print("    5. 按 R 可重置为0偏移")
        print("="*70)
        print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python image_aligner.py <图像路径>")
        print()
        print("示例:")
        print("  python image_aligner.py 911-20251111.jpg")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    coords_file = Path('config/template_coordinates.json')
    
    if not image_path.exists():
        print(f"✗ 图像文件不存在: {image_path}")
        sys.exit(1)
    
    if not coords_file.exists():
        print(f"✗ 坐标文件不存在: {coords_file}")
        sys.exit(1)
    
    try:
        aligner = ImageAligner(image_path, coords_file)
        aligner.run()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
