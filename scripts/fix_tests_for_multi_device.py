"""
修复测试以支持多设备功能

这个脚本会自动更新测试文件，添加device_id参数
"""
import re
from pathlib import Path


def fix_database_tests():
    """修复数据库测试"""
    test_file = Path("tests/unit/test_database.py")
    content = test_file.read_text()

    # 替换insert_monthly_data调用
    content = re.sub(
        r'db\.insert_monthly_data\("([^"]+)",\s*([^,\)]+)(?:,\s*overwrite=([^)]+))?\)',
        r'db.insert_monthly_data("\1", \2, device_id=1\3)',
        content,
    )

    # 修复overwrite参数
    content = content.replace("device_id=1True", "device_id=1, overwrite=True")
    content = content.replace("device_id=1False", "device_id=1, overwrite=False")

    # 替换query_by_month调用
    content = re.sub(
        r'db\.query_by_month\("([^"]+)"\)', r'db.query_by_month("\1", device_id=1)', content
    )

    # 替换query_by_item调用
    content = re.sub(
        r'db\.query_by_item\("([^"]+)"\)', r'db.query_by_item("\1", device_id=1)', content
    )

    # 替换delete_month调用
    content = re.sub(
        r'db\.delete_month\("([^"]+)"\)', r'db.delete_month("\1", device_id=1)', content
    )

    test_file.write_text(content)
    print(f"✅ 已更新: {test_file}")


def fix_analyzer_tests():
    """修复分析器测试"""
    test_file = Path("tests/unit/test_analyzer.py")
    content = test_file.read_text()

    # 替换compare_two_months调用
    content = re.sub(
        r'analyzer\.compare_two_months\("([^"]+)",\s*"([^"]+)"\)',
        r'analyzer.compare_two_months("\1", "\2", device_id=1)',
        content,
    )

    # 替换calculate_statistics调用
    content = re.sub(
        r'analyzer\.calculate_statistics\("([^"]+)"(?:,\s*start_month="([^"]*)")?(?:,\s*end_month="([^"]*)")?\)',
        lambda m: f'analyzer.calculate_statistics("{m.group(1)}", device_id=1'
        + (f', start_month="{m.group(2)}"' if m.group(2) else "")
        + (f', end_month="{m.group(3)}"' if m.group(3) else "")
        + ")",
        content,
    )

    # 替换detect_anomalies调用
    content = re.sub(
        r'analyzer\.detect_anomalies\("([^"]+)"(?:,\s*threshold=([^)]+))?\)',
        lambda m: f'analyzer.detect_anomalies("{m.group(1)}", device_id=1'
        + (f", threshold={m.group(2)}" if m.group(2) else "")
        + ")",
        content,
    )

    test_file.write_text(content)
    print(f"✅ 已更新: {test_file}")


def fix_property_tests():
    """修复属性测试"""
    # 数据库属性测试
    test_file = Path("tests/property/test_properties_database.py")
    if test_file.exists():
        content = test_file.read_text()

        # 添加device_id参数
        content = re.sub(
            r'db\.insert_monthly_data\(month,\s*data\)',
            r"db.insert_monthly_data(month, data, device_id=1)",
            content,
        )
        content = re.sub(
            r'db\.query_by_month\(month\)', r"db.query_by_month(month, device_id=1)", content
        )

        test_file.write_text(content)
        print(f"✅ 已更新: {test_file}")

    # 分析器属性测试
    test_file = Path("tests/property/test_properties_analyzer.py")
    if test_file.exists():
        content = test_file.read_text()

        content = re.sub(
            r'analyzer\.compare_two_months\(month1,\s*month2\)',
            r"analyzer.compare_two_months(month1, month2, device_id=1)",
            content,
        )

        test_file.write_text(content)
        print(f"✅ 已更新: {test_file}")


def fix_integration_tests():
    """修复集成测试"""
    test_file = Path("tests/integration/test_end_to_end.py")
    if test_file.exists():
        content = test_file.read_text()

        # 添加device_id参数
        content = re.sub(
            r'db\.insert_monthly_data\("([^"]+)",\s*([^)]+)\)',
            r'db.insert_monthly_data("\1", \2, device_id=1)',
            content,
        )
        content = re.sub(
            r'analyzer\.compare_two_months\("([^"]+)",\s*"([^"]+)"\)',
            r'analyzer.compare_two_months("\1", "\2", device_id=1)',
            content,
        )

        test_file.write_text(content)
        print(f"✅ 已更新: {test_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("修复测试以支持多设备功能")
    print("=" * 60)
    print()

    try:
        fix_database_tests()
        fix_analyzer_tests()
        fix_property_tests()
        fix_integration_tests()

        print()
        print("=" * 60)
        print("✅ 所有测试文件已更新！")
        print("=" * 60)
        print()
        print("下一步：运行测试验证")
        print("  python3 -m pytest tests/unit/test_database.py -v")
        print("  python3 -m pytest tests/unit/test_analyzer.py -v")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()
