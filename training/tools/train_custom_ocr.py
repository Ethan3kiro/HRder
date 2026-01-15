#!/usr/bin/env python3
"""
自定义 OCR 训练脚本 - 基于标注数据优化识别
"""

import json
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict
import pickle
from tqdm import tqdm


class CustomOCRTrainer:
    """自定义 OCR 训练器"""
    
    def __init__(self, labels_dir="training_data"):
        self.labels_dir = Path(labels_dir)
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        # 存储统计信息
        self.cell_stats = defaultdict(lambda: {
            'values': [],
            'positions': [],
            'sizes': []
        })
    
    def analyze_labels(self):
        """分析标注数据，提取统计信息"""
        print("📊 分析标注数据...")
        
        label_files = list(self.labels_dir.glob("*_labels.json"))
        if not label_files:
            print("❌ 没有找到标注文件")
            return False
        
        print(f"✓ 找到 {len(label_files)} 个标注文件")
        
        for label_file in tqdm(label_files, desc="分析标注"):
            with open(label_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            image_path = Path(data['image_path'])
            if not image_path.exists():
                continue
            
            # 加载图像
            image = cv2.imread(str(image_path))
            if image is None:
                continue
            
            # 收集每个单元格的信息
            for cell_id, value in data['labels'].items():
                self.cell_stats[cell_id]['values'].append(value)
        
        print(f"\n✓ 分析完成！共分析 {len(self.cell_stats)} 个单元格")
        return True
    
    def generate_statistics(self):
        """生成统计报告"""
        print("\n📈 生成统计报告...")
        
        stats_report = {
            'total_cells': len(self.cell_stats),
            'cell_ranges': {},
            'common_values': {}
        }
        
        for cell_id, stats in self.cell_stats.items():
            values = stats['values']
            if not values:
                continue
            
            stats_report['cell_ranges'][cell_id] = {
                'min': min(values),
                'max': max(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'count': len(values)
            }
        
        # 保存统计报告
        report_file = self.model_dir / "statistics.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(stats_report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 统计报告已保存: {report_file}")
        
        # 显示摘要
        print("\n📊 统计摘要:")
        print(f"  总单元格数: {stats_report['total_cells']}")
        
        # 显示几个示例
        print("\n  示例统计（前 5 个）:")
        for i, (cell_id, ranges) in enumerate(list(stats_report['cell_ranges'].items())[:5]):
            print(f"    {cell_id}:")
            print(f"      范围: {ranges['min']:.1f} - {ranges['max']:.1f}")
            print(f"      平均: {ranges['mean']:.1f} ± {ranges['std']:.1f}")
            print(f"      样本数: {ranges['count']}")
        
        return stats_report
    
    def create_validation_rules(self, stats_report):
        """基于统计信息创建验证规则"""
        print("\n🔧 创建验证规则...")
        
        validation_rules = {}
        
        for cell_id, ranges in stats_report['cell_ranges'].items():
            # 创建合理的范围（均值 ± 3倍标准差）
            min_val = max(0, ranges['mean'] - 3 * ranges['std'])
            max_val = ranges['mean'] + 3 * ranges['std']
            
            validation_rules[cell_id] = {
                'min': min_val,
                'max': max_val,
                'expected_mean': ranges['mean'],
                'expected_std': ranges['std']
            }
        
        # 保存验证规则
        rules_file = self.model_dir / "validation_rules.pkl"
        with open(rules_file, 'wb') as f:
            pickle.dump(validation_rules, f)
        
        print(f"✓ 验证规则已保存: {rules_file}")
        print(f"  共创建 {len(validation_rules)} 条规则")
        
        return validation_rules
    
    def train(self):
        """执行训练流程"""
        print("=" * 60)
        print("自定义 OCR 训练")
        print("=" * 60)
        
        # 步骤 1: 分析标注数据
        if not self.analyze_labels():
            return False
        
        # 步骤 2: 生成统计信息
        stats_report = self.generate_statistics()
        
        # 步骤 3: 创建验证规则
        validation_rules = self.create_validation_rules(stats_report)
        
        print("\n" + "=" * 60)
        print("✅ 训练完成！")
        print("=" * 60)
        print("\n生成的文件:")
        print(f"  1. {self.model_dir}/statistics.json - 统计报告")
        print(f"  2. {self.model_dir}/validation_rules.pkl - 验证规则")
        
        print("\n下一步:")
        print("  1. 测试识别器: python3 tools/test_custom_ocr.py")
        print("  2. 集成到主程序: python3 tools/integrate_custom_ocr.py")
        
        return True


def main():
    """主函数"""
    trainer = CustomOCRTrainer()
    trainer.train()


if __name__ == "__main__":
    main()
