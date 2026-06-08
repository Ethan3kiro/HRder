#!/usr/bin/env python3
"""
交互式坐标标定工具

用于标记发射机截图中需要识别的数据区域坐标
支持鼠标框选和键盘快捷键操作
"""
import cv2
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CoordinateCalibrator:
    """坐标标定器
    
    操作说明：
    - 鼠标左键点击两次：框选区域（左上角 → 右下角）
    - 空格键：确认当前选择并输入区域名称
    - Z 键：撤销上一次标定
    - S 键：保存坐标到文件
    - Q 键：退出程序
    - +/- 键：放大/缩小显示
    """
    
    def __init__(self, image_path: Path, output_path: Optional[Path] = None):
        """
        初始化标定器
        
        Args:
            image_path: 输入图像路径
            output_path: 坐标输出路径，默认为 config/template_coordinates.json
        """
        self.image_path = Path(image_path)
        self.output_path = output_path or Path('config/template_coordinates.json')
        
        # 加载图像
        self.original_image = cv2.imread(str(self.image_path))
        if self.original_image is None:
            raise ValueError(f"无法读取图像: {self.image_path}")
        
        self.image = self.original_image.copy()
        self.height, self.width = self.image.shape[:2]
        
        # 标定数据
        self.coords: Dict[str, Tuple[int, int, int, int]] = {}
        self.coord_order: List[str] = []  # 记录添加顺序
        
        # 当前选择
        self.points: List[Tuple[int, int]] = []
        self.temp_name: Optional[str] = None
        
        # 显示控制
        self.scale = 1.0
        self.show_labels = False  # 默认不显示标签，避免遮挡
        
        # 加载已有坐标（如果存在）
        self._load_existing_coords()
        
        print(f"✓ 图像加载成功: {self.image_path}")
        print(f"  尺寸: {self.width} x {self.height}")
        print(f"  已加载 {len(self.coords)} 个标定区域")
    
    def _load_existing_coords(self):
        """加载已有坐标"""
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 直接使用扁平格式，如果已经是扁平的就不需要处理
                    if self._is_flat_format(data):
                        # 已经是扁平格式（如：{"AZ": [x1,y1,x2,y2], ...}）
                        self.coords = {k: tuple(v) for k, v in data.items()}
                    else:
                        # 嵌套格式，需要展平
                        self.coords = self._flatten_coords(data)
                    self.coord_order = list(self.coords.keys())
                print(f"✓ 已加载坐标文件: {self.output_path}")
            except Exception as e:
                print(f"⚠ 加载坐标文件失败: {e}")
    
    def _is_flat_format(self, data: Dict) -> bool:
        """判断是否为扁平格式"""
        # 扁平格式：所有值都是4元素列表
        for value in data.values():
            if not isinstance(value, list) or len(value) != 4:
                return False
            if not all(isinstance(x, int) for x in value):
                return False
        return True
    
    def _flatten_coords(self, data: Dict) -> Dict[str, Tuple[int, int, int, int]]:
        """展平嵌套的坐标字典"""
        flat = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # 嵌套字典（如 COMBINER）
                for sub_key, coords in value.items():
                    flat[f"{key}.{sub_key}"] = tuple(coords)
            elif isinstance(value, list):
                # 列表（如 ZPLANE_A）
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        for sub_key, coords in item.items():
                            flat[f"{key}[{i}].{sub_key}"] = tuple(coords)
                    else:
                        flat[f"{key}[{i}]"] = tuple(item)
            else:
                flat[key] = tuple(value)
        return flat
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 转换为原图坐标
            orig_x = int(x / self.scale)
            orig_y = int(y / self.scale)
            
            self.points.append((orig_x, orig_y))
            print(f"  点 {len(self.points)}: ({orig_x}, {orig_y})")
            
            if len(self.points) == 2:
                print("  → 请按空格键确认并输入区域名称，或按 ESC 取消")
    
    def calibrate(self):
        """启动交互式标定"""
        window_name = 'Coordinate Calibrator'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        self._print_help()
        
        while True:
            display = self._create_display()
            
            cv2.imshow(window_name, display)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                # 退出
                if self._confirm_exit():
                    break
            
            elif key == ord(' ') and len(self.points) == 2:
                # 空格键：确认选择
                self._add_region()
            
            elif key == 27:  # ESC
                # 取消当前选择
                self.points = []
                print("✗ 已取消当前选择")
            
            elif key == ord('z'):
                # 撤销最后一个标定
                self._undo_last()
            
            elif key == ord('d'):
                # 删除指定区域
                self._delete_region()
            
            elif key == ord('s'):
                # 保存
                self._save_coordinates()
            
            elif key == ord('l'):
                # 切换标签显示
                self.show_labels = not self.show_labels
                print(f"✓ 标签显示: {'开' if self.show_labels else '关'}")
            
            elif key == ord('=') or key == ord('+'):
                # 放大
                self.scale = min(3.0, self.scale + 0.1)
                print(f"✓ 缩放: {self.scale:.1f}x")
            
            elif key == ord('-') or key == ord('_'):
                # 缩小
                self.scale = max(0.5, self.scale - 0.1)
                print(f"✓ 缩放: {self.scale:.1f}x")
            
            elif key == ord('h'):
                # 帮助
                self._print_help()
        
        cv2.destroyAllWindows()
        print("\n✓ 标定工具已退出")
    
    def _create_display(self) -> 'numpy.ndarray':
        """创建显示图像"""
        display = self.original_image.copy()
        
        # 绘制已标定区域
        for name in self.coord_order:
            coords = self.coords[name]
            x1, y1, x2, y2 = coords
            
            # 绘制矩形
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            if self.show_labels:
                label_bg_height = 20
                cv2.rectangle(display, (x1, y1 - label_bg_height), 
                            (x1 + len(name) * 8, y1), (0, 255, 0), -1)
                cv2.putText(display, name, (x1 + 2, y1 - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # 绘制当前选择
        if len(self.points) >= 1:
            # 第一个点
            x1, y1 = self.points[0]
            cv2.circle(display, (x1, y1), 5, (0, 0, 255), -1)
            
            if len(self.points) == 2:
                # 第二个点和矩形
                x2, y2 = self.points[1]
                cv2.circle(display, (x2, y2), 5, (0, 0, 255), -1)
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # 显示尺寸
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                size_text = f"{width}x{height}"
                cv2.putText(display, size_text, 
                          (min(x1, x2), max(y1, y2) + 20),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # 添加状态栏
        status_bar = self._create_status_bar()
        display = cv2.vconcat([display, status_bar])
        
        # 缩放显示
        if self.scale != 1.0:
            new_width = int(display.shape[1] * self.scale)
            new_height = int(display.shape[0] * self.scale)
            display = cv2.resize(display, (new_width, new_height))
        
        return display
    
    def _create_status_bar(self) -> 'numpy.ndarray':
        """创建状态栏"""
        import numpy as np
        
        bar_height = 60
        bar = np.zeros((bar_height, self.width, 3), dtype=np.uint8)
        bar[:] = (40, 40, 40)
        
        # 状态信息
        status_texts = [
            f"已标定: {len(self.coords)} 个区域",
            f"缩放: {self.scale:.1f}x",
            f"标签: {'显示' if self.show_labels else '隐藏'}"
        ]
        
        y_pos = 20
        for text in status_texts:
            cv2.putText(bar, text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 20
        
        # 快捷键提示
        help_text = "空格:确认 | Z:撤销 | D:删除 | S:保存 | L:标签 | +/-:缩放 | H:帮助 | Q:退出"
        cv2.putText(bar, help_text, (self.width - 680, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        return bar
    
    def _add_region(self):
        """添加区域"""
        if len(self.points) != 2:
            return
        
        print("\n" + "="*60)
        print("请输入区域名称")
        print("="*60)
        print("命名建议：")
        print("  COMBINER 区域: COMBINER.AZ, COMBINER.BZ, ...")
        print("  Z-Plane 区域: ZPLANE_A[0].Current, ZPLANE_A[0].ISO_Temp, ...")
        print("=" * 60)
        
        name = input("区域名称: ").strip()
        
        if not name:
            print("✗ 名称不能为空")
            return
        
        if name in self.coords:
            overwrite = input(f"⚠ 区域 '{name}' 已存在，是否覆盖？(y/n): ").strip().lower()
            if overwrite != 'y':
                print("✗ 已取消")
                self.points = []
                return
            # 移除旧的，保持顺序
            self.coord_order.remove(name)
        
        # 规范化坐标（确保左上到右下）
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]
        
        coords = (
            min(x1, x2),
            min(y1, y2),
            max(x1, x2),
            max(y1, y2)
        )
        
        self.coords[name] = coords
        self.coord_order.append(name)
        
        print(f"✓ 已添加区域: {name} → {coords}")
        print(f"  尺寸: {coords[2]-coords[0]} x {coords[3]-coords[1]}")
        
        # 清空选择
        self.points = []
    
    def _undo_last(self):
        """撤销最后一个标定"""
        if not self.coord_order:
            print("✗ 没有可撤销的标定")
            return
        
        last_name = self.coord_order.pop()
        del self.coords[last_name]
        print(f"✓ 已撤销: {last_name}")
    
    def _delete_region(self):
        """删除指定区域"""
        if not self.coords:
            print("✗ 没有可删除的区域")
            return
        
        print("\n" + "="*60)
        print("当前已标注的区域：")
        print("="*60)
        for idx, name in enumerate(self.coord_order, 1):
            coords = self.coords[name]
            print(f"  {idx:2d}. {name:30s} - {coords}")
        print("="*60)
        
        region_name = input("请输入要删除的区域名称（或按回车取消）: ").strip()
        
        if not region_name:
            print("✗ 已取消")
            return
        
        if region_name not in self.coords:
            print(f"✗ 区域 '{region_name}' 不存在")
            return
        
        confirm = input(f"⚠️  确认删除 '{region_name}'？(y/n): ").strip().lower()
        if confirm == 'y':
            self.coord_order.remove(region_name)
            del self.coords[region_name]
            print(f"✓ 已删除: {region_name}")
        else:
            print("✗ 已取消")
    
    def _save_coordinates(self):
        """保存坐标到文件"""
        if not self.coords:
            print("✗ 没有可保存的坐标")
            return
        
        # 使用扁平格式保存（简单直接）
        # 格式：{"AZ": [x1, y1, x2, y2], "BZ": [x1, y1, x2, y2], ...}
        flat_coords = {name: list(coords) for name, coords in self.coords.items()}
        
        # 确保目录存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(flat_coords, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 坐标已保存到: {self.output_path}")
        print(f"  共 {len(self.coords)} 个区域")
    
    def _structure_coords(self) -> Dict:
        """将扁平坐标重组为结构化格式"""
        structured = {}
        
        for name, coords in self.coords.items():
            if '.' in name and '[' not in name:
                # 如 COMBINER.AZ
                group, sub = name.split('.', 1)
                if group not in structured:
                    structured[group] = {}
                structured[group][sub] = list(coords)
            
            elif '[' in name:
                # 如 ZPLANE_A[0].Current
                import re
                match = re.match(r'([A-Z_]+)\[(\d+)\]\.(.+)', name)
                if match:
                    group, idx, sub = match.groups()
                    idx = int(idx)
                    
                    if group not in structured:
                        structured[group] = []
                    
                    # 确保列表足够长
                    while len(structured[group]) <= idx:
                        structured[group].append({})
                    
                    structured[group][idx][sub] = list(coords)
                else:
                    structured[name] = list(coords)
            else:
                structured[name] = list(coords)
        
        return structured
    
    def _confirm_exit(self) -> bool:
        """确认退出"""
        if not self.coords:
            return True
        
        print("\n" + "="*60)
        save = input("是否保存坐标后退出？(y/n/c 取消): ").strip().lower()
        
        if save == 'c':
            return False
        elif save == 'y':
            self._save_coordinates()
        
        return True
    
    def _print_help(self):
        """打印帮助信息"""
        print("\n" + "="*70)
        print("  坐标标定工具 - 操作说明")
        print("="*70)
        print("  鼠标操作：")
        print("    左键点击两次    框选区域（左上角 → 右下角）")
        print()
        print("  键盘快捷键：")
        print("    空格键          确认当前选择并输入区域名称")
        print("    ESC             取消当前选择")
        print("    Z               撤销上一次标定")
        print("    D               删除指定区域（用于重新标注）")
        print("    S               保存坐标到文件")
        print("    L               切换标签显示/隐藏")
        print("    +/-             放大/缩小显示")
        print("    H               显示帮助")
        print("    Q               退出程序")
        print()
        print("  重新标注某个区域的方法：")
        print("    方法1: 按D键删除该区域，然后重新框选并输入相同名称")
        print("    方法2: 直接框选并输入相同名称，确认时选择覆盖(y)")
        print("="*70)
        print()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python coordinate_calibrator.py <图像路径> [输出路径]")
        print()
        print("示例:")
        print("  python coordinate_calibrator.py 911-20251016.jpg")
        print("  python coordinate_calibrator.py 911-20251016.jpg config/coords.json")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not image_path.exists():
        print(f"✗ 图像文件不存在: {image_path}")
        sys.exit(1)
    
    try:
        calibrator = CoordinateCalibrator(image_path, output_path)
        calibrator.calibrate()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
