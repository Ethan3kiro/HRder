#!/usr/bin/env python3
"""
标记参照物工具

用于标记一个固定的参照物区域（如某个固定文字或图标）
用于后续图片对齐
"""
import cv2
import json
import sys
from pathlib import Path
import numpy as np


class ReferenceMarker:
    """参照物标记器"""
    
    def __init__(self, image_path: Path, output_path: Path):
        """初始化"""
        self.image_path = Path(image_path)
        self.output_path = Path(output_path)
        
        # 加载图像
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"无法读取图像: {self.image_path}")
        
        self.height, self.width = self.image.shape[:2]
        
        # 参照物区域
        self.reference_region = None
        self.points = []
        
        print(f"✓ 图像加载成功: {self.image_path}")
        print(f"  尺寸: {self.width} x {self.height}")
        print()
    
    def run(self):
        """运行标记工具"""
        window_name = 'Reference Point Marker'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        self._print_help()
        
        while True:
            display = self._create_display()
            cv2.imshow(window_name, display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s') and self.reference_region:
                self._save_reference()
                break
            elif key == 27:  # ESC
                self.points = []
                print("✗ 已取消选择")
        
        cv2.destroyAllWindows()
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
            print(f"  点 {len(self.points)}: ({x}, {y})")
            
            if len(self.points) == 2:
                x1, y1 = self.points[0]
                x2, y2 = self.points[1]
                self.reference_region = [
                    min(x1, x2), min(y1, y2),
                    max(x1, x2), max(y1, y2)
                ]
                print(f"✓ 参照区域: {self.reference_region}")
                print("  → 按 S 保存，按 ESC 重新选择")
    
    def _create_display(self) -> np.ndarray:
        """创建显示"""
        display = self.image.copy()
        
        # 绘制已选点
        for point in self.points:
            cv2.circle(display, point, 5, (0, 0, 255), -1)
        
        # 绘制参照区域
        if self.reference_region:
            x1, y1, x2, y2 = self.reference_region
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 提取并显示参照物
            ref_roi = self.image[y1:y2, x1:x2]
            
            # 在右上角显示放大的参照物
            scale = 3
            ref_zoomed = cv2.resize(ref_roi, None, fx=scale, fy=scale, 
                                   interpolation=cv2.INTER_CUBIC)
            
            # 放置位置
            rh, rw = ref_zoomed.shape[:2]
            if rw < self.width - 20 and rh < 200:
                x_offset = self.width - rw - 10
                y_offset = 10
                
                # 添加背景
                display[y_offset:y_offset+rh, x_offset:x_offset+rw] = ref_zoomed
                
                # 添加边框
                cv2.rectangle(display, (x_offset, y_offset), 
                            (x_offset+rw, y_offset+rh), (255, 255, 0), 2)
                
                # 添加文字
                cv2.putText(display, "Reference", (x_offset, y_offset-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # 添加状态栏
        status_bar = self._create_status_bar()
        display = np.vstack([display, status_bar])
        
        return display
    
    def _create_status_bar(self) -> np.ndarray:
        """创建状态栏"""
        bar_height = 80
        bar = np.zeros((bar_height, self.width, 3), dtype=np.uint8)
        bar[:] = (40, 40, 40)
        
        y_pos = 25
        
        if not self.reference_region:
            text = "1. 点击图像上的两个点，框选参照物区域（如固定的文字或图标）"
            cv2.putText(bar, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_pos += 30
            text = "   建议选择：明显、固定、不变的区域"
            cv2.putText(bar, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        else:
            text = "2. 参照物已选择，按 S 保存，按 ESC 重新选择"
            cv2.putText(bar, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return bar
    
    def _save_reference(self):
        """保存参照物"""
        # 提取参照物图像
        x1, y1, x2, y2 = self.reference_region
        ref_image = self.image[y1:y2, x1:x2]
        
        # 保存参照物信息
        data = {
            "reference_region": self.reference_region,
            "image_size": [self.width, self.height],
            "source_image": str(self.image_path)
        }
        
        # 确保目录存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 保存参照物图像
        ref_image_path = self.output_path.parent / 'reference_image.png'
        cv2.imwrite(str(ref_image_path), ref_image)
        
        print(f"\n✓ 参照物已保存:")
        print(f"  配置文件: {self.output_path}")
        print(f"  参照图像: {ref_image_path}")
        print(f"  区域坐标: {self.reference_region}")
    
    def _print_help(self):
        """打印帮助"""
        print("="*70)
        print("  参照物标记工具")
        print("="*70)
        print("  操作步骤：")
        print("    1. 用鼠标点击两次，框选一个固定的参照物区域")
        print("       （建议选择：标题文字、固定图标、边框等明显特征）")
        print("    2. 按 S 保存")
        print("    3. 按 ESC 可重新选择")
        print("    4. 按 Q 退出")
        print("="*70)
        print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python mark_reference_point.py <图像路径>")
        print()
        print("示例:")
        print("  python mark_reference_point.py 911-20251016.jpg")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    output_path = Path('config/reference_point.json')
    
    if not image_path.exists():
        print(f"✗ 图像文件不存在: {image_path}")
        sys.exit(1)
    
    try:
        marker = ReferenceMarker(image_path, output_path)
        marker.run()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
