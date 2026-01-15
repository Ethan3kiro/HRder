#!/usr/bin/env python3
"""
交互式坐标调整工具
允许用户通过拖动和调整大小来设置正确的坐标
"""

import json
import cv2
import numpy as np
from pathlib import Path
import sys


class InteractiveCoordinateAdjuster:
    """交互式坐标调整器"""
    
    def __init__(self, image_path, label_path):
        self.image_path = Path(image_path)
        self.label_path = Path(label_path)
        
        # 加载图像
        self.original_image = cv2.imread(str(image_path))
        if self.original_image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        self.image = self.original_image.copy()
        self.display_image = self.image.copy()
        
        # 加载标注数据
        with open(label_path, 'r', encoding='utf-8') as f:
            self.label_data = json.load(f)
        
        # 当前坐标配置
        self.coords = self.get_initial_coordinates()
        
        # 当前选中的区域
        self.current_region = 'combiner'  # 'combiner' 或 'zplane' - 默认 COMBINER
        self.selected_cell = None
        self.selected_column = None  # 用于 Z-Plane: (module, column_type)
        
        # 鼠标状态
        self.dragging = False
        self.resizing = False
        self.drag_start = None
        self.resize_start_size = None
        
        # UI 状态
        self.show_labels = True
        self.zoom_level = 1.0
        
        # 窗口名称
        self.window_name = "坐标调整工具 - 按 H 查看帮助"
        
    def get_initial_coordinates(self):
        """获取初始坐标配置"""
        return {
            'combiner': {
                'base_x': 214,
                'base_y': 223,
                'spacing': 48,
                'width': 34,
                'height': 23,
                'abcd_offset': 2  # ABCD 项的额外偏移
            },
            'zplane': {
                # 每个模块的每一列都有独立的坐标
                # 注意：第4和第5个框之间有额外的间隙（middle_gap）
                'A': {
                    'Current': {'x': 43, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30},
                    'ISO Temp': {'x': 93, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30}
                },
                'B': {
                    'Current': {'x': 233, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30},
                    'ISO Temp': {'x': 283, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30}
                },
                'C': {
                    'Current': {'x': 423, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30},
                    'ISO Temp': {'x': 473, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30}
                },
                'D': {
                    'Current': {'x': 613, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30},
                    'ISO Temp': {'x': 663, 'y': 292, 'width': 35, 'height': 30, 'middle_gap': 30}
                }
            }
        }
    
    def get_cell_boxes(self):
        """根据当前坐标配置生成所有单元格的边界框"""
        boxes = {}
        
        # COMBINER 区域
        combiner = self.coords['combiner']
        for i, item in enumerate(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']):
            x = combiner['base_x'] + i * combiner['spacing']
            # ABCD 项单独偏移
            if item == 'ABCD':
                x += combiner['abcd_offset']
            y = combiner['base_y']
            boxes[item] = {
                'x': x,
                'y': y,
                'w': combiner['width'],
                'h': combiner['height'],
                'region': 'combiner'
            }
        
        # Z-Plane 区域 - 每列独立坐标
        zplane = self.coords['zplane']
        for module in ['A', 'B', 'C', 'D']:
            for col_type in ['Current', 'ISO Temp']:
                col_config = zplane[module][col_type]
                base_x = col_config['x']
                base_y = col_config['y']
                width = col_config['width']
                height = col_config['height']
                middle_gap = col_config.get('middle_gap', 0)  # 第4和第5框之间的额外间隙
                
                for row in range(1, 9):
                    # 计算 Y 坐标：前4行正常间距，第5-8行需要加上额外间隙
                    if row <= 4:
                        row_y = base_y + (row - 1) * height
                    else:
                        row_y = base_y + (row - 1) * height + middle_gap
                    
                    key = f'Z-Plane {module}-{col_type}-{row}'
                    boxes[key] = {
                        'x': base_x,
                        'y': row_y,
                        'w': width,
                        'h': height,
                        'region': 'zplane',
                        'module': module,
                        'column': col_type
                    }
        
        return boxes
    
    def draw_boxes(self):
        """绘制所有边界框"""
        self.display_image = self.image.copy()
        boxes = self.get_cell_boxes()
        
        for cell_id, box in boxes.items():
            if cell_id not in self.label_data['labels']:
                continue
            
            x, y, w, h = box['x'], box['y'], box['w'], box['h']
            
            # 根据区域选择颜色
            if box['region'] == self.current_region:
                color = (0, 255, 0)  # 绿色 - 当前区域
                thickness = 2
            else:
                color = (128, 128, 128)  # 灰色 - 其他区域
                thickness = 1
            
            # 如果是选中的单元格，使用特殊颜色
            if cell_id == self.selected_cell:
                color = (0, 255, 255)  # 黄色
                thickness = 3
            
            # 绘制矩形
            cv2.rectangle(self.display_image, (x, y), (x + w, y + h), color, thickness)
            
            # 绘制标签
            if self.show_labels:
                label_text = cell_id.replace('Z-Plane ', '').replace('-Current', '-C').replace('-ISO Temp', '-T')
                cv2.putText(self.display_image, label_text, (x, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        # 绘制帮助信息
        self.draw_help_overlay()
    
    def draw_help_overlay(self):
        """绘制帮助信息覆盖层"""
        overlay = self.display_image.copy()
        
        # 半透明背景
        cv2.rectangle(overlay, (10, 10), (450, 240), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, self.display_image, 0.3, 0, self.display_image)
        
        # 文本信息
        combiner = self.coords['combiner']
        
        # 显示当前选中的列信息
        if self.selected_column:
            module, col_type = self.selected_column
            col = self.coords['zplane'][module][col_type]
            middle_gap = col.get('middle_gap', 0)
            zplane_info = f"Z-PLANE: {module}-{col_type}: X={col['x']}, Y={col['y']}, W={col['width']}, H={col['height']}, Gap={middle_gap}"
        else:
            zplane_info = "Z-PLANE: (点击任意框查看详情)"
        
        info_lines = [
            f"当前区域: {self.current_region.upper()}",
            f"COMBINER: X={combiner['base_x']}, Y={combiner['base_y']}",
            f"          间距={combiner['spacing']}, 大小={combiner['width']}x{combiner['height']}",
            zplane_info,
            "",
            "快捷键:",
            "  C - 切换到 COMBINER 区域",
            "  Z - 切换到 Z-PLANE 区域",
            "  方向键 - 移动整个区域",
            "  COMBINER: I/O - 调整横向间距",
            "  Z-PLANE: I/O - 调整行高(需先点击列)",
            "  Z-PLANE: M/N - 调整中间间隙(需先点击列)",
            "  W/H - 增加宽度/高度",
            "  鼠标左键拖动 - 移动位置",
            "  鼠标右键拖动 - 调整大小",
            "  S - 保存坐标",
            "  R - 重置坐标",
            "  Q/ESC - 退出"
        ]
        
        y_offset = 25
        for line in info_lines:
            cv2.putText(self.display_image, line, (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_offset += 15
    
    def find_cell_at_position(self, x, y):
        """查找指定位置的单元格"""
        boxes = self.get_cell_boxes()
        
        for cell_id, box in boxes.items():
            bx, by, bw, bh = box['x'], box['y'], box['w'], box['h']
            if bx <= x <= bx + bw and by <= y <= by + bh:
                return cell_id, box
        
        return None, None
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标事件回调"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 左键：拖动移动位置
            cell_id, box = self.find_cell_at_position(x, y)
            if cell_id:
                self.selected_cell = cell_id
                self.current_region = box['region']
                
                # 如果是 Z-Plane，记录选中的列
                if self.current_region == 'zplane':
                    self.selected_column = (box['module'], box['column'])
                else:
                    self.selected_column = None
                
                self.dragging = True
                self.drag_start = (x, y)
                self.draw_boxes()
                cv2.imshow(self.window_name, self.display_image)
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右键：调整大小
            cell_id, box = self.find_cell_at_position(x, y)
            if cell_id:
                self.selected_cell = cell_id
                self.current_region = box['region']
                
                # 如果是 Z-Plane，记录选中的列
                if self.current_region == 'zplane':
                    self.selected_column = (box['module'], box['column'])
                else:
                    self.selected_column = None
                
                self.resizing = True
                self.drag_start = (x, y)
                
                # 保存当前大小
                if self.current_region == 'combiner':
                    self.resize_start_size = (
                        self.coords['combiner']['width'],
                        self.coords['combiner']['height']
                    )
                else:
                    # Z-Plane: 保存选中列的大小
                    module, col_type = self.selected_column
                    col_config = self.coords['zplane'][module][col_type]
                    self.resize_start_size = (col_config['width'], col_config['height'])
                
                self.draw_boxes()
                cv2.imshow(self.window_name, self.display_image)
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging and self.drag_start:
                # 拖动移动
                dx = x - self.drag_start[0]
                dy = y - self.drag_start[1]
                
                if self.current_region == 'combiner':
                    self.coords['combiner']['base_x'] += dx
                    self.coords['combiner']['base_y'] += dy
                else:
                    # Z-Plane: 移动选中的列
                    if self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['x'] += dx
                        self.coords['zplane'][module][col_type]['y'] += dy
                
                self.drag_start = (x, y)
                self.draw_boxes()
                cv2.imshow(self.window_name, self.display_image)
            
            elif self.resizing and self.drag_start and self.resize_start_size:
                # 调整大小
                dx = x - self.drag_start[0]
                dy = y - self.drag_start[1]
                
                if self.current_region == 'combiner':
                    # 调整 COMBINER 框大小
                    new_width = max(10, self.resize_start_size[0] + dx)
                    new_height = max(10, self.resize_start_size[1] + dy)
                    self.coords['combiner']['width'] = new_width
                    self.coords['combiner']['height'] = new_height
                else:
                    # Z-Plane: 调整选中列的大小
                    if self.selected_column:
                        module, col_type = self.selected_column
                        new_width = max(10, self.resize_start_size[0] + dx)
                        new_height = max(10, self.resize_start_size[1] + dy)
                        self.coords['zplane'][module][col_type]['width'] = new_width
                        self.coords['zplane'][module][col_type]['height'] = new_height
                
                self.draw_boxes()
                cv2.imshow(self.window_name, self.display_image)
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            self.drag_start = None
        
        elif event == cv2.EVENT_RBUTTONUP:
            self.resizing = False
            self.drag_start = None
            self.resize_start_size = None
    
    def save_coordinates(self):
        """保存坐标到文件"""
        # 更新 prepare_dl_data.py
        self.update_prepare_dl_data()
        
        # 更新 visualize_coordinates.py
        self.update_visualize_coordinates()
        
        # 更新 test_dl_model.py
        self.update_test_dl_model()
        
        print("\n" + "=" * 60)
        print("✅ 坐标已保存到所有文件！")
        print("=" * 60)
        print(f"\nCOMBINER 坐标:")
        print(f"  base_x: {self.coords['combiner']['base_x']}")
        print(f"  base_y: {self.coords['combiner']['base_y']}")
        print(f"  spacing: {self.coords['combiner']['spacing']}")
        print(f"  width: {self.coords['combiner']['width']}")
        print(f"  height: {self.coords['combiner']['height']}")
        print(f"  abcd_offset: {self.coords['combiner']['abcd_offset']}")
        print(f"\nZ-PLANE 坐标 (每列独立):")
        for module in ['A', 'B', 'C', 'D']:
            print(f"  模块 {module}:")
            for col_type in ['Current', 'ISO Temp']:
                col = self.coords['zplane'][module][col_type]
                middle_gap = col.get('middle_gap', 0)
                print(f"    {col_type}: x={col['x']}, y={col['y']}, w={col['width']}, h={col['height']}, gap={middle_gap}")
        print("\n下一步: 运行 ./train_dl_ocr.sh 重新训练模型")
    
    def update_prepare_dl_data(self):
        """更新 prepare_dl_data.py 中的坐标"""
        file_path = Path("tools/prepare_dl_data.py")
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到 get_cell_coordinates 方法并重写
        in_method = False
        method_start = -1
        indent_level = 0
        
        for i, line in enumerate(lines):
            if 'def get_cell_coordinates(self):' in line:
                in_method = True
                method_start = i
                indent_level = len(line) - len(line.lstrip())
            elif in_method and line.strip().startswith('def ') and i > method_start:
                # 找到下一个方法，结束
                method_end = i
                break
            elif in_method and line.strip().startswith('return coords'):
                method_end = i + 1
                break
        
        # 生成新的方法代码
        combiner = self.coords['combiner']
        zplane = self.coords['zplane']
        
        new_method = f'''    def get_cell_coordinates(self):
        """定义所有单元格的坐标（根据实际图像调整）"""
        coords = {{}}
        
        # 格式: {{cell_id: (x, y, width, height)}}
        
        # COMBINER 区域 - 横向排列在图像中上部
        # AZ, BZ, CZ, DZ, AB, CD, ABCD 从左到右排列
        combiner_base_x = {combiner['base_x']}
        combiner_base_y = {combiner['base_y']}
        combiner_spacing = {combiner['spacing']}
        combiner_width = {combiner['width']}
        combiner_height = {combiner['height']}
        
        for i, item in enumerate(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']):
            x = combiner_base_x + i * combiner_spacing
            # ABCD 项单独向右移动 {combiner['abcd_offset']} 像素
            if item == 'ABCD':
                x += {combiner['abcd_offset']}
            coords[item] = (x, combiner_base_y, combiner_width, combiner_height)
        
        # Z-Plane 区域 - 每个模块的每一列都有独立坐标
'''
        
        for module in ['A', 'B', 'C', 'D']:
            for col_type in ['Current', 'ISO Temp']:
                col = zplane[module][col_type]
                col_var = col_type.replace(' ', '_').lower()
                middle_gap = col.get('middle_gap', 0)
                new_method += f'''        # 模块 {module} - {col_type}
        {module}_{col_var}_x = {col['x']}
        {module}_{col_var}_y = {col['y']}
        {module}_{col_var}_width = {col['width']}
        {module}_{col_var}_height = {col['height']}
        {module}_{col_var}_middle_gap = {middle_gap}  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = {module}_{col_var}_y + (row - 1) * {module}_{col_var}_height
            else:
                row_y = {module}_{col_var}_y + (row - 1) * {module}_{col_var}_height + {module}_{col_var}_middle_gap
            key = 'Z-Plane {module}-{col_type}-{{row}}'
            coords[key] = ({module}_{col_var}_x, row_y, {module}_{col_var}_width, {module}_{col_var}_height)
        
'''
        
        new_method += '''        return coords
    
'''
        
        # 替换方法
        lines[method_start:method_end] = [new_method]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def update_visualize_coordinates(self):
        """更新 visualize_coordinates.py 中的坐标"""
        # 使用与 prepare_dl_data 相同的逻辑
        self._update_file_coordinates(Path("tools/visualize_coordinates.py"))
    
    def update_test_dl_model(self):
        """更新 test_dl_model.py 中的坐标"""
        # 使用与 prepare_dl_data 相同的逻辑
        self._update_file_coordinates(Path("tools/test_dl_model.py"))
    
    def _update_file_coordinates(self, file_path):
        """通用的坐标更新函数"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到 get_cell_coordinates 或 get_current_coordinates 方法
        in_method = False
        method_start = -1
        
        for i, line in enumerate(lines):
            if ('def get_cell_coordinates' in line or 'def get_current_coordinates' in line):
                in_method = True
                method_start = i
            elif in_method and line.strip().startswith('def ') and i > method_start:
                method_end = i
                break
            elif in_method and line.strip().startswith('return coords'):
                method_end = i + 1
                break
        
        # 生成新的方法代码（与 prepare_dl_data 相同）
        combiner = self.coords['combiner']
        zplane = self.coords['zplane']
        
        # 判断方法名
        method_name = 'get_current_coordinates' if 'visualize' in str(file_path) else 'get_cell_coordinates'
        
        new_method = f'''    def {method_name}(self):
        """获取当前定义的坐标"""
        coords = {{}}
        
        # COMBINER 区域 - 横向排列
        combiner_base_x = {combiner['base_x']}
        combiner_base_y = {combiner['base_y']}
        combiner_spacing = {combiner['spacing']}
        combiner_width = {combiner['width']}
        combiner_height = {combiner['height']}
        
        for i, item in enumerate(['AZ', 'BZ', 'CZ', 'DZ', 'AB', 'CD', 'ABCD']):
            x = combiner_base_x + i * combiner_spacing
            # ABCD 项单独向右移动 {combiner['abcd_offset']} 像素
            if item == 'ABCD':
                x += {combiner['abcd_offset']}
            coords[item] = (x, combiner_base_y, combiner_width, combiner_height)
        
        # Z-Plane 区域 - 每个模块的每一列都有独立坐标
'''
        
        for module in ['A', 'B', 'C', 'D']:
            for col_type in ['Current', 'ISO Temp']:
                col = zplane[module][col_type]
                col_var = col_type.replace(' ', '_').lower()
                middle_gap = col.get('middle_gap', 0)
                new_method += f'''        # 模块 {module} - {col_type}
        {module}_{col_var}_x = {col['x']}
        {module}_{col_var}_y = {col['y']}
        {module}_{col_var}_width = {col['width']}
        {module}_{col_var}_height = {col['height']}
        {module}_{col_var}_middle_gap = {middle_gap}  # 第4和第5框之间的额外间隙
        
        for row in range(1, 9):
            # 前4行正常间距，第5-8行需要加上额外间隙
            if row <= 4:
                row_y = {module}_{col_var}_y + (row - 1) * {module}_{col_var}_height
            else:
                row_y = {module}_{col_var}_y + (row - 1) * {module}_{col_var}_height + {module}_{col_var}_middle_gap
            key = 'Z-Plane {module}-{col_type}-{{row}}'
            coords[key] = ({module}_{col_var}_x, row_y, {module}_{col_var}_width, {module}_{col_var}_height)
        
'''
        
        new_method += '''        return coords
    
'''
        
        # 替换方法
        lines[method_start:method_end] = [new_method]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def run(self):
        """运行交互式调整器"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1200, 800)  # 设置窗口大小
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\n" + "=" * 60)
        print("交互式坐标调整工具")
        print("=" * 60)
        print("\n使用说明:")
        print("  - 用鼠标左键拖动绿色框来移动位置")
        print("  - 用鼠标右键拖动绿色框来调整大小")
        print("  - Z-Plane 区域：每一列可以单独调整位置和大小")
        print("  - 按 C 切换到 COMBINER 区域")
        print("  - 按 Z 切换到 Z-PLANE 区域")
        print("  - 使用方向键微调位置")
        print("  - COMBINER: 按 I/O 调整横向间距")
        print("  - Z-PLANE: 先点击一列，然后按 I/O 调整行高")
        print("  - Z-PLANE: 先点击一列，然后按 M/N 调整中间间隙")
        print("  - 按 W/H 增加宽度/高度")
        print("  - 按 S 保存坐标")
        print("  - 按 Q 或 ESC 退出")
        print("\n" + "=" * 60 + "\n")
        
        self.draw_boxes()
        cv2.imshow(self.window_name, self.display_image)
        
        print("窗口已打开，如果看不到窗口，请检查 Dock 或其他桌面...")
        print("提示：如果按键没有反应，请确保窗口处于激活状态（点击窗口）")
        print()
        print("⚠️  重要提示：")
        print("   当前区域：COMBINER（默认）")
        print("   - COMBINER: I/O 键调整横向间距")
        print("   - Z-PLANE: 先点击一列，然后 I/O 键调整行高")
        print("   - Z-PLANE: 先点击一列，然后 M/N 键调整中间间隙（第4-5框之间）")
        print()
        
        try:
            while True:
                key = cv2.waitKey(1) & 0xFF
                
                if key == 255:  # 没有按键
                    continue
                
                # 打印按键码用于调试
                print(f"按键码: {key}, 字符: {chr(key) if 32 <= key < 127 else 'N/A'}")
                
                # 退出键
                if key == ord('q') or key == ord('Q') or key == 27:
                    print("退出程序...")
                    break
                
                # 区域切换
                elif key == ord('c') or key == ord('C'):
                    self.current_region = 'combiner'
                    self.selected_column = None
                    print("✓ 切换到 COMBINER 区域")
                
                elif key == ord('z') or key == ord('Z'):
                    self.current_region = 'zplane'
                    print("✓ 切换到 Z-PLANE 区域")
                
                # I/O 键调整间距
                elif key == ord('i') or key == ord('I'):
                    if self.current_region == 'combiner':
                        self.coords['combiner']['spacing'] += 1
                        print(f"✓ COMBINER 间距增加: {self.coords['combiner']['spacing']}px")
                    elif self.selected_column:
                        # Z-PLANE: 增加行高
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['height'] += 1
                        print(f"✓ Z-PLANE {module}-{col_type} 行高增加: {self.coords['zplane'][module][col_type]['height']}px")
                    else:
                        print("ℹ Z-PLANE: 请先点击一列，然后用 I/O 调整行高")
                
                elif key == ord('o') or key == ord('O'):
                    if self.current_region == 'combiner':
                        self.coords['combiner']['spacing'] = max(1, self.coords['combiner']['spacing'] - 1)
                        print(f"✓ COMBINER 间距减少: {self.coords['combiner']['spacing']}px")
                    elif self.selected_column:
                        # Z-PLANE: 减少行高
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['height'] = max(1, self.coords['zplane'][module][col_type]['height'] - 1)
                        print(f"✓ Z-PLANE {module}-{col_type} 行高减少: {self.coords['zplane'][module][col_type]['height']}px")
                    else:
                        print("ℹ Z-PLANE: 请先点击一列，然后用 I/O 调整行高")
                
                # M/N 键调整中间间隙（Z-PLANE 专用）
                elif key == ord('m') or key == ord('M'):
                    if self.current_region == 'zplane' and self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['middle_gap'] += 1
                        print(f"✓ Z-PLANE {module}-{col_type} 中间间隙增加: {self.coords['zplane'][module][col_type]['middle_gap']}px")
                    elif self.current_region == 'zplane':
                        print("ℹ Z-PLANE: 请先点击一列，然后用 M/N 调整中间间隙")
                    else:
                        print("ℹ 中间间隙调整仅适用于 Z-PLANE 区域")
                
                elif key == ord('n') or key == ord('N'):
                    if self.current_region == 'zplane' and self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['middle_gap'] = max(0, self.coords['zplane'][module][col_type]['middle_gap'] - 1)
                        print(f"✓ Z-PLANE {module}-{col_type} 中间间隙减少: {self.coords['zplane'][module][col_type]['middle_gap']}px")
                    elif self.current_region == 'zplane':
                        print("ℹ Z-PLANE: 请先点击一列，然后用 M/N 调整中间间隙")
                    else:
                        print("ℹ 中间间隙调整仅适用于 Z-PLANE 区域")
                
                # W/H 键调整宽度/高度
                elif key == ord('w'):
                    if self.current_region == 'combiner':
                        self.coords['combiner']['width'] += 1
                        print(f"✓ COMBINER 宽度增加: {self.coords['combiner']['width']}px")
                    elif self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['width'] += 1
                        print(f"✓ Z-PLANE {module}-{col_type} 宽度增加: {self.coords['zplane'][module][col_type]['width']}px")
                
                elif key == ord('h'):
                    if self.current_region == 'combiner':
                        self.coords['combiner']['height'] += 1
                        print(f"✓ COMBINER 高度增加: {self.coords['combiner']['height']}px")
                    elif self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['height'] += 1
                        print(f"✓ Z-PLANE {module}-{col_type} 高度增加: {self.coords['zplane'][module][col_type]['height']}px")
                
                # 方向键
                elif key == 81 or key == 2 or key == 63234:  # 左箭头
                    if self.current_region == 'combiner':
                        self.coords['combiner']['base_x'] -= 1
                        print(f"← COMBINER 向左移动 1px")
                    elif self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['x'] -= 1
                        print(f"← Z-PLANE {module}-{col_type} 向左移动 1px")
                
                elif key == 83 or key == 3 or key == 63235:  # 右箭头
                    if self.current_region == 'combiner':
                        self.coords['combiner']['base_x'] += 1
                        print(f"→ COMBINER 向右移动 1px")
                    elif self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['x'] += 1
                        print(f"→ Z-PLANE {module}-{col_type} 向右移动 1px")
                
                elif key == 82 or key == 0 or key == 63232:  # 上箭头
                    if self.current_region == 'combiner':
                        self.coords['combiner']['base_y'] -= 1
                        print(f"↑ COMBINER 向上移动 1px")
                    elif self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['y'] -= 1
                        print(f"↑ Z-PLANE {module}-{col_type} 向上移动 1px")
                
                elif key == 84 or key == 1 or key == 63233:  # 下箭头
                    if self.current_region == 'combiner':
                        self.coords['combiner']['base_y'] += 1
                        print(f"↓ COMBINER 向下移动 1px")
                    elif self.selected_column:
                        module, col_type = self.selected_column
                        self.coords['zplane'][module][col_type]['y'] += 1
                        print(f"↓ Z-PLANE {module}-{col_type} 向下移动 1px")
                
                # 保存
                elif key == ord('s') or key == ord('S'):
                    self.save_coordinates()
                
                # 重置
                elif key == ord('r') or key == ord('R'):
                    self.coords = self.get_initial_coordinates()
                    print("✓ 坐标已重置")
                
                # 切换标签显示
                elif key == ord('l') or key == ord('L'):
                    self.show_labels = not self.show_labels
                    print(f"✓ 标签显示: {'开' if self.show_labels else '关'}")
                
                # 重新绘制
                self.draw_boxes()
                cv2.imshow(self.window_name, self.display_image)
                
        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"\n运行时错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cv2.destroyAllWindows()


def main():
    """主函数"""
    # 查找标注文件
    labels_dir = Path("training_data")
    label_files = list(labels_dir.glob("*_labels.json"))
    
    if not label_files:
        print("❌ 没有找到标注文件")
        return 1
    
    # 使用第一个标注文件
    label_file = label_files[0]
    
    with open(label_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_path = Path(data['image_path'])
    if not image_path.exists():
        print(f"❌ 图像文件不存在: {image_path}")
        return 1
    
    # 创建并运行调整器
    adjuster = InteractiveCoordinateAdjuster(image_path, label_file)
    adjuster.run()
    
    return 0


if __name__ == "__main__":
    exit(main())
