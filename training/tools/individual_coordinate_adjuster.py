#!/usr/bin/env python3
"""
独立坐标调整工具 - 每个框都可以单独调整
支持71个独立的框（7个COMBINER + 64个Z-PLANE）
"""

import cv2
import numpy as np
import json
from pathlib import Path


class IndividualCoordinateAdjuster:
    """独立坐标调整器 - 每个框都可以单独移动和调整大小"""
    
    def __init__(self, image_path):
        self.image_path = Path(image_path)
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"无法加载图像: {self.image_path}")
        
        # 创建显示窗口
        self.window_name = "独立坐标调整工具 - 每个框都可单独调整"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1200, 800)
        
        # 加载当前坐标
        self.coords = self.load_coordinates()
        
        # 所有框的ID列表（按顺序）
        self.all_cell_ids = self.get_all_cell_ids()
        
        # 当前选中的框索引
        self.current_cell_index = 0
        
        # 鼠标状态
        self.dragging = False
        self.resizing = False
        self.drag_start = None
        self.original_coords = None
        
        # 设置鼠标回调
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("=" * 60)
        print("独立坐标调整工具")
        print("=" * 60)
        print(f"\n总共 {len(self.all_cell_ids)} 个框可以调整")
        print("\n使用说明:")
        print("  - 左键拖动: 移动当前框")
        print("  - 右键拖动: 调整当前框大小")
        print("  - 方向键: 微调位置 (1像素)")
        print("  - Shift+方向键: 快速移动 (5像素)")
        print("  - W/S: 增加/减少高度")
        print("  - A/D: 减少/增加宽度")
        print("  - N: 下一个框")
        print("  - P: 上一个框")
        print("  - 数字键 1-9: 快速跳转到指定框")
        print("  - Space: 保存当前坐标")
        print("  - Q/ESC: 退出")
        print("=" * 60)
    
    def get_all_cell_ids(self):
        """获取所有框的ID列表"""
        cell_ids = []
        
        # COMBINER 区域 (7个)
        combiner_items = ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']
        cell_ids.extend(combiner_items)
        
        # Z-Plane 区域 (64个 = 8列 × 8行)
        modules = ['A-Current', 'A-ISO Temp', 'B-Current', 'B-ISO Temp',
                   'C-Current', 'C-ISO Temp', 'D-Current', 'D-ISO Temp']
        
        for module in modules:
            for row in range(1, 9):
                cell_ids.append(f'Z-Plane {module}-{row}')
        
        return cell_ids
    
    def load_coordinates(self):
        """从 individual_coordinates.json 加载坐标（如果存在），否则使用默认值"""
        coords = {}
        
        # 尝试加载之前保存的坐标
        saved_coords_file = Path("tools/individual_coordinates.json")
        if saved_coords_file.exists():
            print(f"✓ 加载之前保存的坐标: {saved_coords_file}")
            with open(saved_coords_file, 'r', encoding='utf-8') as f:
                saved_coords = json.load(f)
            # 转换为列表格式
            for key, value in saved_coords.items():
                coords[key] = list(value)
            return coords
        
        print("ℹ 使用默认坐标（未找到保存的坐标文件）")
        
        # COMBINER 区域 - 默认值
        combiner_base_x = 214
        combiner_base_y = 223
        combiner_spacing = 48
        combiner_width = 34
        combiner_height = 23
        
        for i, item in enumerate(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']):
            x = combiner_base_x + i * combiner_spacing
            if item == 'ABCD':
                x += 2
            coords[item] = [x, combiner_base_y, combiner_width, combiner_height]
        
        # Z-Plane 区域配置 - 默认值
        zplane_configs = [
            ('A-Current', 42, 292, 38, 23, 8),
            ('A-ISO Temp', 175, 292, 37, 23, 8),
            ('B-Current', 234, 290, 38, 24, 4),
            ('B-ISO Temp', 366, 290, 38, 24, 4),
            ('C-Current', 426, 290, 39, 24, 4),
            ('C-ISO Temp', 558, 290, 39, 24, 3),
            ('D-Current', 618, 290, 38, 24, 4),
            ('D-ISO Temp', 750, 290, 39, 24, 3),
        ]
        
        for module, base_x, base_y, width, height, middle_gap in zplane_configs:
            for row in range(1, 9):
                if row <= 4:
                    row_y = base_y + (row - 1) * height
                else:
                    row_y = base_y + (row - 1) * height + middle_gap
                
                key = f'Z-Plane {module}-{row}'
                coords[key] = [base_x, row_y, width, height]
        
        return coords
    
    def get_current_cell_id(self):
        """获取当前选中的框ID"""
        return self.all_cell_ids[self.current_cell_index]
    
    def get_current_coords(self):
        """获取当前框的坐标"""
        cell_id = self.get_current_cell_id()
        return self.coords[cell_id]
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标事件回调"""
        cell_id = self.get_current_cell_id()
        cx, cy, cw, ch = self.coords[cell_id]
        
        if event == cv2.EVENT_LBUTTONDOWN:
            # 检查是否点击在当前框内
            if cx <= x <= cx + cw and cy <= y <= cy + ch:
                self.dragging = True
                self.drag_start = (x, y)
                self.original_coords = [cx, cy, cw, ch]
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右键调整大小
            if cx <= x <= cx + cw and cy <= y <= cy + ch:
                self.resizing = True
                self.drag_start = (x, y)
                self.original_coords = [cx, cy, cw, ch]
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging and self.drag_start:
                # 移动框
                dx = x - self.drag_start[0]
                dy = y - self.drag_start[1]
                self.coords[cell_id][0] = self.original_coords[0] + dx
                self.coords[cell_id][1] = self.original_coords[1] + dy
                self.draw()
            
            elif self.resizing and self.drag_start:
                # 调整大小
                dx = x - self.drag_start[0]
                dy = y - self.drag_start[1]
                new_w = max(10, self.original_coords[2] + dx)
                new_h = max(10, self.original_coords[3] + dy)
                self.coords[cell_id][2] = new_w
                self.coords[cell_id][3] = new_h
                self.draw()
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            self.drag_start = None
        
        elif event == cv2.EVENT_RBUTTONUP:
            self.resizing = False
            self.drag_start = None
    
    def draw(self):
        """绘制图像和所有框"""
        display = self.image.copy()
        
        # 绘制所有框（半透明）
        for i, cell_id in enumerate(self.all_cell_ids):
            x, y, w, h = self.coords[cell_id]
            
            if i == self.current_cell_index:
                # 当前选中的框 - 绿色高亮
                color = (0, 255, 0)
                thickness = 3
                # 添加填充
                overlay = display.copy()
                cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
                cv2.addWeighted(overlay, 0.2, display, 0.8, 0, display)
            else:
                # 其他框 - 蓝色半透明
                color = (255, 100, 0)
                thickness = 1
            
            cv2.rectangle(display, (x, y), (x + w, y + h), color, thickness)
            
            # 显示框的标签（只对当前框和附近的框）
            if i == self.current_cell_index or abs(i - self.current_cell_index) <= 2:
                label = f"{i+1}:{cell_id}"
                cv2.putText(display, label, (x, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # 显示当前框信息
        cell_id = self.get_current_cell_id()
        x, y, w, h = self.coords[cell_id]
        info_text = [
            f"当前框: [{self.current_cell_index + 1}/{len(self.all_cell_ids)}] {cell_id}",
            f"坐标: X={x}, Y={y}, W={w}, H={h}",
            f"提示: N/P切换框, 方向键微调, W/S/A/D调整大小, Space保存"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(display, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
        
        cv2.imshow(self.window_name, display)
    
    def next_cell(self):
        """切换到下一个框"""
        self.current_cell_index = (self.current_cell_index + 1) % len(self.all_cell_ids)
        print(f"\n切换到: [{self.current_cell_index + 1}/{len(self.all_cell_ids)}] {self.get_current_cell_id()}")
        self.draw()
    
    def prev_cell(self):
        """切换到上一个框"""
        self.current_cell_index = (self.current_cell_index - 1) % len(self.all_cell_ids)
        print(f"\n切换到: [{self.current_cell_index + 1}/{len(self.all_cell_ids)}] {self.get_current_cell_id()}")
        self.draw()
    
    def jump_to_cell(self, index):
        """跳转到指定索引的框"""
        if 0 <= index < len(self.all_cell_ids):
            self.current_cell_index = index
            print(f"\n跳转到: [{self.current_cell_index + 1}/{len(self.all_cell_ids)}] {self.get_current_cell_id()}")
            self.draw()
    
    def save_coordinates(self):
        """保存坐标到文件"""
        output_file = Path("tools/individual_coordinates.json")
        
        # 保存为JSON格式
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.coords, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 坐标已保存到: {output_file}")
        print(f"  总共保存了 {len(self.coords)} 个框的坐标")
        
        # 同时生成Python代码格式
        self.generate_python_code()
    
    def generate_python_code(self):
        """生成可以直接用于 prepare_dl_data.py 的Python代码"""
        output_file = Path("tools/individual_coordinates.py")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 独立调整后的坐标配置\n")
            f.write("# 每个框都有独立的坐标\n\n")
            f.write("def get_individual_coordinates():\n")
            f.write("    \"\"\"返回所有框的独立坐标\"\"\"\n")
            f.write("    coords = {}\n\n")
            
            # COMBINER 区域
            f.write("    # COMBINER 区域 (7个框)\n")
            for item in ['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']:
                x, y, w, h = self.coords[item]
                f.write(f"    coords['{item}'] = ({x}, {y}, {w}, {h})\n")
            
            f.write("\n")
            
            # Z-Plane 区域
            f.write("    # Z-Plane 区域 (64个框)\n")
            modules = ['A-Current', 'A-ISO Temp', 'B-Current', 'B-ISO Temp',
                       'C-Current', 'C-ISO Temp', 'D-Current', 'D-ISO Temp']
            
            for module in modules:
                f.write(f"\n    # {module}\n")
                for row in range(1, 9):
                    key = f'Z-Plane {module}-{row}'
                    x, y, w, h = self.coords[key]
                    f.write(f"    coords['{key}'] = ({x}, {y}, {w}, {h})\n")
            
            f.write("\n    return coords\n")
        
        print(f"✓ Python代码已生成: {output_file}")
        print(f"  可以在 prepare_dl_data.py 中导入使用")
    
    def run(self):
        """运行调整工具"""
        self.draw()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # Q 或 ESC
                print("\n退出程序...")
                break
            
            elif key == ord('n'):  # 下一个框
                self.next_cell()
            
            elif key == ord('p'):  # 上一个框
                self.prev_cell()
            
            elif key == ord(' '):  # 空格保存
                self.save_coordinates()
            
            # 数字键快速跳转
            elif ord('1') <= key <= ord('9'):
                jump_index = (key - ord('1')) * 10
                self.jump_to_cell(jump_index)
            
            # 方向键微调
            elif key == 82 or key == 0:  # 上箭头
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][1] -= 1
                self.draw()
            
            elif key == 84 or key == 1:  # 下箭头
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][1] += 1
                self.draw()
            
            elif key == 81 or key == 2:  # 左箭头
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][0] -= 1
                self.draw()
            
            elif key == 83 or key == 3:  # 右箭头
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][0] += 1
                self.draw()
            
            # 调整大小
            elif key == ord('w'):  # 增加高度
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][3] += 1
                self.draw()
            
            elif key == ord('s'):  # 减少高度
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][3] = max(5, self.coords[cell_id][3] - 1)
                self.draw()
            
            elif key == ord('d'):  # 增加宽度
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][2] += 1
                self.draw()
            
            elif key == ord('a'):  # 减少宽度
                cell_id = self.get_current_cell_id()
                self.coords[cell_id][2] = max(5, self.coords[cell_id][2] - 1)
                self.draw()
        
        cv2.destroyAllWindows()


def main():
    """主函数"""
    # 使用第一张标注图像
    image_path = "/Users/Ethan/Desktop/Harris样本/调频数据/调频数据/921/2025/20250219.bmp"
    
    if not Path(image_path).exists():
        print(f"❌ 图像不存在: {image_path}")
        print("   请修改 image_path 为你的测试图像路径")
        return 1
    
    adjuster = IndividualCoordinateAdjuster(image_path)
    adjuster.run()
    
    return 0


if __name__ == "__main__":
    exit(main())
