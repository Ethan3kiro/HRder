#!/usr/bin/env python3
"""
交互式坐标微调工具

功能：
- 逐个显示标注区域
- 用方向键调整位置
- 用快捷键调整大小
- 实时显示OCR识别结果
- 自动保存修改
"""
import cv2
import json
import sys
import pytesseract
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional


class CoordinateAdjuster:
    """坐标微调器"""
    
    def __init__(self, image_path: Path, coords_file: Path):
        """初始化"""
        self.image_path = Path(image_path)
        self.coords_file = Path(coords_file)
        
        # 加载图像
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"无法读取图像: {self.image_path}")
        
        self.height, self.width = self.image.shape[:2]
        
        # 加载坐标
        with open(self.coords_file, 'r', encoding='utf-8') as f:
            self.coords = json.load(f)
        
        self.coord_names = list(self.coords.keys())
        self.current_idx = 0
        
        # 调整参数
        self.move_step = 1  # 移动步长（像素）
        self.size_step = 1  # 大小调整步长
        
        # 显示参数
        self.zoom = 3.0
        self.show_ocr = True
        
        # Tesseract配置
        self.tesseract_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.'
        
        print(f"✓ 图像加载成功: {self.image_path}")
        print(f"  尺寸: {self.width} x {self.height}")
        print(f"  坐标数量: {len(self.coords)}")
        print()
    
    def run(self):
        """运行微调工具"""
        window_name = 'Coordinate Adjuster'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        self._print_help()
        
        while True:
            # 显示当前区域
            display = self._create_display()
            cv2.imshow(window_name, display)
            
            # 等待按键
            key = cv2.waitKey(0) & 0xFF
            
            if key == ord('q'):
                # 退出
                self._save_and_exit()
                break
            
            elif key == ord('s'):
                # 保存
                self._save_coords()
            
            elif key == ord('n') or key == ord(']'):
                # 下一个
                self._next_region()
            
            elif key == ord('p') or key == ord('['):
                # 上一个
                self._prev_region()
            
            elif key == ord('j'):
                # 跳转到指定区域
                self._jump_to_region()
            
            elif key == ord('o'):
                # 切换OCR显示
                self.show_ocr = not self.show_ocr
                print(f"OCR显示: {'开' if self.show_ocr else '关'}")
            
            elif key == ord('h'):
                # 帮助
                self._print_help()
            
            elif key == 82 or key == 0:  # 上箭头
                self._move_region(0, -self.move_step)
            
            elif key == 84 or key == 1:  # 下箭头
                self._move_region(0, self.move_step)
            
            elif key == 81 or key == 2:  # 左箭头
                self._move_region(-self.move_step, 0)
            
            elif key == 83 or key == 3:  # 右箭头
                self._move_region(self.move_step, 0)
            
            elif key == ord('w'):
                # 增加高度
                self._resize_region(0, self.size_step)
            
            elif key == ord('x'):
                # 减少高度
                self._resize_region(0, -self.size_step)
            
            elif key == ord('a'):
                # 减少宽度
                self._resize_region(-self.size_step, 0)
            
            elif key == ord('d'):
                # 增加宽度
                self._resize_region(self.size_step, 0)
            
            elif key == ord('r'):
                # 重置为原始坐标
                self._reset_region()
        
        cv2.destroyAllWindows()
        print("\n✓ 微调工具已退出")
    
    def _create_display(self) -> np.ndarray:
        """创建显示图像"""
        name = self.coord_names[self.current_idx]
        coords = self.coords[name]
        x1, y1, x2, y2 = coords
        
        # 提取ROI及周边区域
        margin = 40
        rx1 = max(0, x1 - margin)
        ry1 = max(0, y1 - margin)
        rx2 = min(self.width, x2 + margin)
        ry2 = min(self.height, y2 + margin)
        
        region = self.image[ry1:ry2, rx1:rx2].copy()
        
        # 在region上绘制当前框（相对坐标）
        rel_x1 = x1 - rx1
        rel_y1 = y1 - ry1
        rel_x2 = x2 - rx1
        rel_y2 = y2 - ry1
        
        # 绘制矩形
        cv2.rectangle(region, (rel_x1, rel_y1), (rel_x2, rel_y2), (0, 255, 0), 2)
        
        # 放大显示
        zoomed = cv2.resize(region, None, fx=self.zoom, fy=self.zoom, 
                           interpolation=cv2.INTER_CUBIC)
        
        # 添加信息面板（宽度匹配放大后的图像）
        info_panel = self._create_info_panel(name, coords, zoomed.shape[1])
        
        # 拼接
        display = np.vstack([zoomed, info_panel])
        
        return display
    
    def _create_info_panel(self, name: str, coords: list, display_width: int) -> np.ndarray:
        """创建信息面板"""
        panel_height = 200
        panel_width = display_width
        panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)
        panel[:] = (40, 40, 40)
        
        x1, y1, x2, y2 = coords
        w, h = x2 - x1, y2 - y1
        
        # 基本信息
        y_pos = 25
        texts = [
            f"[{self.current_idx + 1}/{len(self.coords)}] {name}",
            f"坐标: ({x1}, {y1}) -> ({x2}, {y2})",
            f"尺寸: {w} x {h}",
        ]
        
        for text in texts:
            cv2.putText(panel, text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_pos += 25
        
        # OCR识别结果
        if self.show_ocr:
            ocr_result = self._get_ocr_result(coords, name)
            cv2.putText(panel, f"OCR: {ocr_result}", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            y_pos += 30
        
        # 快捷键提示
        y_pos += 10
        help_text = "方向键:移动 | WASD:调整大小 | N/P:下一个/上一个 | S:保存 | Q:退出并保存"
        cv2.putText(panel, help_text, (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        
        return panel
    
    def _get_ocr_result(self, coords: list, name: str) -> str:
        """获取OCR识别结果"""
        try:
            x1, y1, x2, y2 = coords
            roi = self.image[y1:y2, x1:x2]
            
            # 预处理
            if 'Current' in name or 'current' in name:
                # Current字段：灰度
                if len(roi.shape) == 3:
                    processed = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                else:
                    processed = roi
            else:
                # Temperature字段：自适应二值化
                if len(roi.shape) == 3:
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                else:
                    gray = roi
                processed = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
            
            # 放大小区域
            if processed.shape[0] < 30 or processed.shape[1] < 50:
                processed = cv2.resize(processed, None, fx=2, fy=2, 
                                      interpolation=cv2.INTER_CUBIC)
            
            # OCR
            text = pytesseract.image_to_string(processed, config=self.tesseract_config)
            text = text.strip().replace(' ', '').replace('\n', '')
            
            # 清理
            replacements = {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8'}
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
            
            # Current字段小数点修复
            if 'Current' in name and cleaned and '.' not in cleaned and len(cleaned) == 2:
                cleaned = cleaned[0] + '.' + cleaned[1]
            
            if cleaned:
                try:
                    value = float(cleaned)
                    if 'Current' in name:
                        return f"{value:.1f}A"
                    else:
                        return f"{value:.1f}°C"
                except:
                    return f"'{cleaned}' (无法转换)"
            else:
                return "(空)"
        
        except Exception as e:
            return f"(错误: {e})"
    
    def _move_region(self, dx: int, dy: int):
        """移动区域"""
        name = self.coord_names[self.current_idx]
        coords = self.coords[name]
        x1, y1, x2, y2 = coords
        
        # 移动
        new_coords = [x1 + dx, y1 + dy, x2 + dx, y2 + dy]
        
        # 边界检查
        if (new_coords[0] >= 0 and new_coords[1] >= 0 and
            new_coords[2] <= self.width and new_coords[3] <= self.height):
            self.coords[name] = new_coords
            print(f"✓ 移动: {name} -> {new_coords}")
    
    def _resize_region(self, dw: int, dh: int):
        """调整大小"""
        name = self.coord_names[self.current_idx]
        coords = self.coords[name]
        x1, y1, x2, y2 = coords
        
        # 调整右下角
        new_coords = [x1, y1, x2 + dw, y2 + dh]
        
        # 确保宽高至少为5
        if new_coords[2] - new_coords[0] >= 5 and new_coords[3] - new_coords[1] >= 5:
            if new_coords[2] <= self.width and new_coords[3] <= self.height:
                self.coords[name] = new_coords
                print(f"✓ 调整大小: {name} -> {new_coords}")
    
    def _next_region(self):
        """下一个区域"""
        self.current_idx = (self.current_idx + 1) % len(self.coords)
        name = self.coord_names[self.current_idx]
        print(f"\n→ [{self.current_idx + 1}/{len(self.coords)}] {name}")
    
    def _prev_region(self):
        """上一个区域"""
        self.current_idx = (self.current_idx - 1) % len(self.coords)
        name = self.coord_names[self.current_idx]
        print(f"\n← [{self.current_idx + 1}/{len(self.coords)}] {name}")
    
    def _jump_to_region(self):
        """跳转到指定区域"""
        print("\n" + "="*60)
        print("跳转到区域")
        print("="*60)
        
        # 显示部分区域名称
        print("区域列表（显示前20个）：")
        for i in range(min(20, len(self.coord_names))):
            print(f"  {i + 1}. {self.coord_names[i]}")
        
        if len(self.coord_names) > 20:
            print(f"  ... 还有 {len(self.coord_names) - 20} 个")
        
        print("="*60)
        
        try:
            idx_str = input(f"输入序号 (1-{len(self.coords)}) 或名称: ").strip()
            
            # 尝试解析为数字
            try:
                idx = int(idx_str) - 1
                if 0 <= idx < len(self.coords):
                    self.current_idx = idx
                    name = self.coord_names[self.current_idx]
                    print(f"✓ 跳转到: [{self.current_idx + 1}] {name}")
                else:
                    print("✗ 序号超出范围")
            except ValueError:
                # 尝试名称匹配
                if idx_str in self.coord_names:
                    self.current_idx = self.coord_names.index(idx_str)
                    print(f"✓ 跳转到: [{self.current_idx + 1}] {idx_str}")
                else:
                    print("✗ 未找到该名称")
        
        except Exception as e:
            print(f"✗ 输入错误: {e}")
    
    def _reset_region(self):
        """重置当前区域（恢复原始坐标）"""
        # 这里简单处理，实际应该从备份文件读取
        print("重置功能需要原始坐标备份")
    
    def _save_coords(self):
        """保存坐标"""
        with open(self.coords_file, 'w', encoding='utf-8') as f:
            json.dump(self.coords, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 坐标已保存到: {self.coords_file}")
    
    def _save_and_exit(self):
        """保存并退出"""
        # 直接保存，不需要询问（避免阻塞）
        self._save_coords()
        print("\n✓ 坐标已自动保存")
    
    def _print_help(self):
        """打印帮助"""
        print("\n" + "="*70)
        print("  坐标微调工具 - 操作说明")
        print("="*70)
        print("  方向键：")
        print("    ↑↓←→          移动区域（1像素）")
        print()
        print("  大小调整：")
        print("    W              增加高度")
        print("    X              减少高度")
        print("    A              减少宽度")
        print("    D              增加宽度")
        print()
        print("  导航：")
        print("    N 或 ]         下一个区域")
        print("    P 或 [         上一个区域")
        print("    J              跳转到指定区域")
        print()
        print("  其他：")
        print("    O              切换OCR显示")
        print("    S              保存坐标")
        print("    H              显示帮助")
        print("    Q              退出（自动保存）")
        print("="*70)
        print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python coordinate_adjuster.py <图像路径> [坐标文件]")
        print()
        print("示例:")
        print("  python coordinate_adjuster.py 911-20251016.jpg")
        print("  python coordinate_adjuster.py 911-20251016.jpg config/template_coordinates.json")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    coords_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('config/template_coordinates.json')
    
    if not image_path.exists():
        print(f"✗ 图像文件不存在: {image_path}")
        sys.exit(1)
    
    if not coords_file.exists():
        print(f"✗ 坐标文件不存在: {coords_file}")
        sys.exit(1)
    
    try:
        adjuster = CoordinateAdjuster(image_path, coords_file)
        adjuster.run()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
