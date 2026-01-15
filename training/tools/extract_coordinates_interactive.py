#!/usr/bin/env python3
"""
交互式坐标提取工具
通过点击图像来获取关键点的坐标
"""

import cv2
import json
from pathlib import Path


class CoordinateExtractor:
    """交互式坐标提取器"""
    
    def __init__(self, image_path):
        self.image_path = Path(image_path)
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        self.coordinates = {}
        self.current_label = None
        self.window_name = "点击标记坐标 (按 ESC 退出)"
        
        # 创建显示窗口
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.current_label:
                self.coordinates[self.current_label] = (x, y)
                print(f"✓ {self.current_label}: ({x}, {y})")
                
                # 在图像上标记
                cv2.circle(self.display_image, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(self.display_image, self.current_label, (x + 10, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.imshow(self.window_name, self.display_image)
    
    def extract(self):
        """提取坐标"""
        print("=" * 60)
        print("交互式坐标提取")
        print("=" * 60)
        print("\n请在图像上点击以下位置的左上角：")
        print()
        
        # 需要标记的关键点
        labels = [
            ("AZ", "COMBINER 区域第一个单元格 (AZ) 的左上角"),
            ("BZ", "COMBINER 区域第二个单元格 (BZ) 的左上角"),
            ("Z-Plane A-Current-1", "Z-Plane A 模块 Current 列第 1 行的左上角"),
            ("Z-Plane A-Current-2", "Z-Plane A 模块 Current 列第 2 行的左上角"),
            ("Z-Plane A-ISO Temp-1", "Z-Plane A 模块 ISO Temp 列第 1 行的左上角"),
            ("Z-Plane B-Current-1", "Z-Plane B 模块 Current 列第 1 行的左上角"),
        ]
        
        self.display_image = self.image.copy()
        cv2.imshow(self.window_name, self.display_image)
        
        for label, description in labels:
            self.current_label = label
            print(f"\n请点击: {description}")
            print(f"标签: {label}")
            
            # 等待用户点击
            while label not in self.coordinates:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    print("\n用户取消")
                    cv2.destroyAllWindows()
                    return None
        
        cv2.destroyAllWindows()
        
        # 计算坐标参数
        print("\n" + "=" * 60)
        print("计算坐标参数")
        print("=" * 60)
        
        params = self.calculate_parameters()
        
        print("\n计算结果:")
        print(json.dumps(params, indent=2, ensure_ascii=False))
        
        # 保存结果
        output_path = Path("coordinate_parameters.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 参数已保存: {output_path}")
        
        return params
    
    def calculate_parameters(self):
        """根据标记的点计算坐标参数"""
        params = {}
        
        # COMBINER 区域
        if "AZ" in self.coordinates and "BZ" in self.coordinates:
            az_x, az_y = self.coordinates["AZ"]
            bz_x, bz_y = self.coordinates["BZ"]
            
            params["combiner"] = {
                "base_x": az_x,
                "base_y": az_y,
                "spacing": bz_y - az_y,
                "width": 80,  # 估计值，可能需要调整
                "height": 30  # 估计值，可能需要调整
            }
        
        # Z-Plane 区域
        if all(k in self.coordinates for k in ["Z-Plane A-Current-1", "Z-Plane A-Current-2", 
                                                 "Z-Plane A-ISO Temp-1", "Z-Plane B-Current-1"]):
            a_c1_x, a_c1_y = self.coordinates["Z-Plane A-Current-1"]
            a_c2_x, a_c2_y = self.coordinates["Z-Plane A-Current-2"]
            a_t1_x, a_t1_y = self.coordinates["Z-Plane A-ISO Temp-1"]
            b_c1_x, b_c1_y = self.coordinates["Z-Plane B-Current-1"]
            
            params["zplane"] = {
                "base_x": a_c1_x,
                "base_y": a_c1_y,
                "cell_height": a_c2_y - a_c1_y,
                "cell_width": a_t1_x - a_c1_x,
                "module_spacing": b_c1_x - a_c1_x,
                "column_spacing": a_t1_x - a_c1_x
            }
        
        return params


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
    
    print(f"使用图像: {image_path.name}")
    
    # 提取坐标
    extractor = CoordinateExtractor(image_path)
    params = extractor.extract()
    
    if params:
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print("=" * 60)
        print("\n下一步:")
        print("1. 查看 coordinate_parameters.json")
        print("2. 运行: python3 tools/apply_coordinates.py")
        print("3. 这会自动更新 tools/prepare_dl_data.py 中的坐标")
    
    return 0


if __name__ == "__main__":
    exit(main())
