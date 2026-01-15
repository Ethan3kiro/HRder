"""
创建测试用的示例图像
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_sample_transmitter_image(output_path: Path):
    """
    创建一个模拟的发射机数据表格图像

    Args:
        output_path: 输出图像路径
    """
    # 创建白色背景图像
    width, height = 800, 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # 绘制表格数据
    y_offset = 50
    line_height = 40

    # 模拟的发射机数据
    data = [
        ("Forward Power", "12.5", "W"),
        ("Reflected Power", "0.3", "W"),
        ("PA Voltage", "28", "V"),
        ("PA Current", "2.5", "A"),
        ("Temperature", "45", "°C"),
        ("Efficiency", "85", "%"),
    ]

    # 绘制数据行
    for item_name, value, unit in data:
        text = f"{item_name}: {value}{unit}"
        draw.text((50, y_offset), text, fill="black")
        y_offset += line_height

    # 保存图像
    image.save(output_path)
    print(f"示例图像已创建: {output_path}")


if __name__ == "__main__":
    # 创建示例图像
    output_dir = Path(__file__).parent / "sample_images"
    output_dir.mkdir(exist_ok=True)

    sample_image_path = output_dir / "sample_transmitter.png"
    create_sample_transmitter_image(sample_image_path)
