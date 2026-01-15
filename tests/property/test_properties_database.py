"""
数据库模块属性测试

使用Hypothesis进行基于属性的测试
"""
import pytest
from hypothesis import given, strategies as st, settings
import tempfile
from pathlib import Path
import pandas as pd

from src.database import TransmitterDatabase
from src.exceptions import DatabaseError, DataValidationError


# 属性 5: 月份格式验证
# 验证：需求 3.2
@given(month_str=st.text())
@settings(max_examples=100)
def test_property_month_format_validation(month_str):
    """
    Feature: transmitter-data-analyzer, Property 5: 月份格式验证

    对于任何月份字符串输入，系统应该验证其是否符合YYYY-MM格式
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        result = db._validate_month_format(month_str)

        # 验证结果是布尔值
        assert isinstance(result, bool)

        # 如果返回True，则字符串必须符合YYYY-MM格式
        if result:
            assert len(month_str) == 7
            assert month_str[4] == "-"
            assert month_str[:4].isdigit()
            assert month_str[5:7].isdigit()

        db.close()


# 属性 6: 重复数据处理
# 验证：需求 3.3
@given(
    item_names=st.lists(
        st.text(min_size=1, max_size=20), min_size=1, max_size=10, unique=True
    ),
    values=st.lists(
        st.floats(
            min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        min_size=1,
        max_size=10,
    ),
)
@settings(max_examples=100)
def test_property_duplicate_data_handling(item_names, values):
    """
    Feature: transmitter-data-analyzer, Property 6: 重复数据处理

    对于任何已存在月份的数据插入操作，系统应该检测到重复并提示用户选择覆盖或取消
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 确保数据长度一致
        min_len = min(len(item_names), len(values))
        item_names = item_names[:min_len]
        values = values[:min_len]

        # 创建测试数据
        test_data = pd.DataFrame(
            {"item_name": item_names, "value": values, "unit": ["V"] * len(item_names)}
        )

        month = "2026-01"

        # 第一次插入应该成功
        db.insert_monthly_data(month, test_data, overwrite=False)

        # 第二次插入相同月份应该抛出异常（不覆盖）
        with pytest.raises(DatabaseError):
            db.insert_monthly_data(month, test_data, overwrite=False)

        # 使用覆盖选项应该成功
        db.insert_monthly_data(month, test_data, overwrite=True)

        db.close()


# 属性 7: 时间戳记录不变性
# 验证：需求 3.5
@given(
    item_names=st.lists(
        st.text(min_size=1, max_size=20), min_size=1, max_size=5, unique=True
    ),
    values=st.lists(
        st.floats(
            min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        min_size=1,
        max_size=5,
    ),
)
@settings(max_examples=100)
def test_property_timestamp_invariance(item_names, values):
    """
    Feature: transmitter-data-analyzer, Property 7: 时间戳记录不变性

    对于任何插入到数据库的记录，都应该自动包含create_time时间戳字段
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 确保数据长度一致
        min_len = min(len(item_names), len(values))
        item_names = item_names[:min_len]
        values = values[:min_len]

        # 创建测试数据
        test_data = pd.DataFrame(
            {"item_name": item_names, "value": values, "unit": ["A"] * len(item_names)}
        )

        month = "2026-02"

        # 插入数据
        db.insert_monthly_data(month, test_data, overwrite=False)

        # 查询数据并验证时间戳
        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT create_time FROM transmitter_data WHERE month = ?", (month,)
        )
        results = cursor.fetchall()

        # 验证所有记录都有时间戳
        assert len(results) == len(item_names)
        for row in results:
            assert row["create_time"] is not None
            assert row["create_time"] != ""

        db.close()


# 属性 8: 查询结果正确性
# 验证：需求 4.1, 4.2, 4.5
@given(
    item_names=st.lists(
        st.text(min_size=1, max_size=20), min_size=1, max_size=10, unique=True
    ),
    values=st.lists(
        st.floats(
            min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        min_size=1,
        max_size=10,
    ),
)
@settings(max_examples=100)
def test_property_query_correctness(item_names, values):
    """
    Feature: transmitter-data-analyzer, Property 8: 查询结果正确性

    对于任何有效的查询条件，查询应该返回且仅返回满足条件的所有记录；
    对于不存在的查询条件，应该返回空结果
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 确保数据长度一致
        min_len = min(len(item_names), len(values))
        item_names = item_names[:min_len]
        values = values[:min_len]

        # 创建测试数据
        test_data = pd.DataFrame(
            {"item_name": item_names, "value": values, "unit": ["W"] * len(item_names)}
        )

        month = "2026-03"

        # 插入数据
        db.insert_monthly_data(month, test_data, overwrite=False)

        # 测试按月份查询
        result_by_month = db.query_by_month(month, device_id=1)
        assert len(result_by_month) == len(item_names)
        assert set(result_by_month["item_name"]) == set(item_names)

        # 测试查询不存在的月份
        result_nonexistent_month = db.query_by_month("2099-12")
        assert len(result_nonexistent_month) == 0

        # 测试按数据项查询
        if len(item_names) > 0:
            test_item = item_names[0]
            result_by_item = db.query_by_item(test_item)
            assert len(result_by_item) >= 1
            assert all(result_by_item["item_name"] == test_item)

        # 测试查询不存在的数据项
        result_nonexistent_item = db.query_by_item("NonExistentItem_XYZ_123")
        assert len(result_nonexistent_item) == 0

        db.close()


# 属性 9: 删除操作完整性
# 验证：需求 4.3
@given(
    item_names=st.lists(
        st.text(min_size=1, max_size=20), min_size=1, max_size=10, unique=True
    ),
    values=st.lists(
        st.floats(
            min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        min_size=1,
        max_size=10,
    ),
)
@settings(max_examples=100)
def test_property_deletion_integrity(item_names, values):
    """
    Feature: transmitter-data-analyzer, Property 9: 删除操作完整性

    对于任何月份的删除操作，该月份的所有记录都应该被移除，
    且删除后查询该月份应该返回空结果
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = TransmitterDatabase(db_path)
        db.initialize_database()

        # 确保数据长度一致
        min_len = min(len(item_names), len(values))
        item_names = item_names[:min_len]
        values = values[:min_len]

        # 创建测试数据
        test_data = pd.DataFrame(
            {"item_name": item_names, "value": values, "unit": ["%"] * len(item_names)}
        )

        month = "2026-04"

        # 插入数据
        db.insert_monthly_data(month, test_data, overwrite=False)

        # 验证数据已插入
        result_before = db.query_by_month(month, device_id=1)
        assert len(result_before) == len(item_names)

        # 删除数据
        deleted_count = db.delete_month(month)
        assert deleted_count == len(item_names)

        # 验证数据已删除
        result_after = db.query_by_month(month, device_id=1)
        assert len(result_after) == 0

        db.close()
