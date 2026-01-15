#!/usr/bin/env python3
"""
示例数据生成脚本

生成模拟的发射机数据库和截图，用于演示和测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import TransmitterDatabase
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import random
from datetime import datetime, timedelta


def create_sample_database(db_path: Path):
    """
    创建示例数据库，包含多个月份的数据
    
    Args:
        db_path: 数据库文件路径
    """
    print(f"创建示例数据库: {db_path}")
    
    # 初始化数据库
    db = TransmitterDatabase(db_path)
    db.initialize_database()
    
    # 定义发射机数据项
    items_config = [
        ("Forward Power", (400, 450), "W"),
        ("Reflected Power", (0.1, 2.0), "W"),
        ("PA Voltage", (26, 30), "V"),
        ("PA Current", (15, 18), "A"),
        ("APC Volts", (3.0, 4.5), "V"),
        ("Airflow %", (75, 95), "%"),
        ("FM EXC Power %", (85, 100), "%"),
        ("Ambient Temp", (20, 35), "°C"),
        ("IPA AB Current", (2.5, 3.5), "A"),
        ("IPA AB Voltage", (12, 14), "V"),
        ("IPA AB Power", (30, 45), "W"),
        ("Driver Power", (50, 70), "W"),
        ("Exciter Power", (10, 15), "W"),
        ("VSWR", (1.0, 1.5), ""),
        ("Efficiency", (80, 90), "%"),
    ]
    
    # 生成最近6个月的数据
    base_date = datetime.now()
    months = []
    for i in range(6):
        month_date = base_date - timedelta(days=30 * i)
        months.append(month_date.strftime('%Y-%m'))
    
    months.reverse()  # 从旧到新排序
    
    # 为每个月生成数据
    for month in months:
        data_records = []
        
        for item_name, (min_val, max_val), unit in items_config:
            # 生成基础值
            base_value = random.uniform(min_val, max_val)
            
            # 添加一些月度趋势（某些参数逐月变化）
            if "Temp" in item_name:
                # 温度有季节性变化
                month_num = int(month.split('-')[1])
                seasonal_factor = 1.0 + 0.2 * (month_num - 6) / 6
                base_value *= seasonal_factor
            elif "Power" in item_name and "Reflected" not in item_name:
                # 功率可能有轻微下降趋势
                month_index = months.index(month)
                base_value *= (1.0 - 0.01 * month_index)
            
            data_records.append({
                'item_name': item_name,
                'value': round(base_value, 2),
                'unit': unit
            })
        
        df = pd.DataFrame(data_records)
        db.insert_monthly_data(month, df, overwrite=True)
        print(f"  已插入 {month} 的数据 ({len(df)} 条记录)")
    
    print(f"\n示例数据库创建完成！")
    print(f"包含月份: {', '.join(months)}")
    print(f"数据项数量: {len(items_config)}")


def create_sample_images(output_dir: Path, num_images: int = 3):
    """
    创建多个示例发射机截图
    
    Args:
        output_dir: 输出目录
        num_images: 生成图像数量
    """
    print(f"\n创建示例截图到: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 定义不同的数据集
    datasets = [
        {
            "name": "sample_transmitter_1.png",
            "title": "Transmitter Status - 2026-01",
            "data": [
                ("Forward Power", "425.3", "W"),
                ("Reflected Power", "1.2", "W"),
                ("PA Voltage", "28.5", "V"),
                ("PA Current", "16.8", "A"),
                ("APC Volts", "3.8", "V"),
                ("Airflow %", "87", "%"),
                ("Ambient Temp", "28", "°C"),
                ("Efficiency", "85.2", "%"),
            ]
        },
        {
            "name": "sample_transmitter_2.png",
            "title": "Transmitter Status - 2025-12",
            "data": [
                ("Forward Power", "430.1", "W"),
                ("Reflected Power", "0.8", "W"),
                ("PA Voltage", "29.0", "V"),
                ("PA Current", "17.2", "A"),
                ("IPA AB Current", "3.1", "A"),
                ("IPA AB Voltage", "13.2", "V"),
                ("Driver Power", "62.5", "W"),
                ("VSWR", "1.2", ""),
            ]
        },
        {
            "name": "sample_transmitter_3.png",
            "title": "Transmitter Status - 2025-11",
            "data": [
                ("Forward Power", "407.8", "W"),
                ("Reflected Power", "1.5", "W"),
                ("PA Voltage", "27.8", "V"),
                ("PA Current", "16.2", "A"),
                ("Ambient Temp", "25", "°C"),
                ("FM EXC Power %", "92", "%"),
                ("Exciter Power", "12.3", "W"),
                ("Efficiency", "83.5", "%"),
            ]
        }
    ]
    
    for i, dataset in enumerate(datasets[:num_images]):
        image_path = output_dir / dataset["name"]
        create_transmitter_image(
            image_path,
            dataset["title"],
            dataset["data"]
        )
        print(f"  已创建: {dataset['name']}")


def create_transmitter_image(
    output_path: Path,
    title: str,
    data: list
):
    """
    创建一个发射机数据表格图像
    
    Args:
        output_path: 输出路径
        title: 图像标题
        data: 数据列表 [(名称, 数值, 单位), ...]
    """
    # 图像尺寸
    width, height = 900, 100 + len(data) * 50 + 100
    
    # 创建白色背景
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # 尝试使用系统字体
    try:
        # 尝试不同的字体路径
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        
        title_font = None
        data_font = None
        
        for font_path in font_paths:
            if Path(font_path).exists():
                title_font = ImageFont.truetype(font_path, 24)
                data_font = ImageFont.truetype(font_path, 18)
                break
        
        if title_font is None:
            title_font = ImageFont.load_default()
            data_font = ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
        data_font = ImageFont.load_default()
    
    # 绘制标题
    draw.text((50, 30), title, fill='black', font=title_font)
    
    # 绘制分隔线
    draw.line([(50, 70), (width - 50, 70)], fill='gray', width=2)
    
    # 绘制表头
    y_offset = 90
    draw.text((80, y_offset), "Parameter", fill='black', font=data_font)
    draw.text((450, y_offset), "Value", fill='black', font=data_font)
    draw.text((650, y_offset), "Unit", fill='black', font=data_font)
    
    # 绘制分隔线
    y_offset += 30
    draw.line([(50, y_offset), (width - 50, y_offset)], fill='lightgray', width=1)
    
    # 绘制数据行
    y_offset += 20
    for item_name, value, unit in data:
        draw.text((80, y_offset), item_name, fill='black', font=data_font)
        draw.text((450, y_offset), value, fill='blue', font=data_font)
        draw.text((650, y_offset), unit, fill='green', font=data_font)
        y_offset += 50
    
    # 绘制边框
    draw.rectangle([(40, 20), (width - 40, height - 20)], outline='gray', width=2)
    
    # 保存图像
    image.save(output_path)


def main():
    """主函数"""
    print("=" * 60)
    print("发射机数据分析器 - 示例数据生成工具")
    print("=" * 60)
    
    # 确定输出目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 创建示例数据目录
    examples_dir = project_root / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    # 1. 创建示例数据库
    db_path = examples_dir / "sample_transmitter_data.db"
    create_sample_database(db_path)
    
    # 2. 创建示例截图
    images_dir = examples_dir / "sample_images"
    create_sample_images(images_dir, num_images=3)
    
    print("\n" + "=" * 60)
    print("示例数据生成完成！")
    print("=" * 60)
    print(f"\n示例数据库: {db_path}")
    print(f"示例截图目录: {images_dir}")
    print("\n您可以使用这些示例数据来测试系统功能。")


if __name__ == "__main__":
    main()
