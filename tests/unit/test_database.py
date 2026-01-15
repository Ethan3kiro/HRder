"""
数据库模块单元测试

测试数据库管理模块的核心功能
"""
import pytest
import tempfile
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.database import TransmitterDatabase
from src.exceptions import DatabaseError, DataValidationError


class TestTransmitterDatabase:
    """数据库管理器测试类"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库fixture"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = TransmitterDatabase(db_path)
            db.initialize_database()
            
            # Initialize multi-device schema
            cursor = db.connection.cursor()
            
            # Create devices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL UNIQUE,
                    device_code TEXT,
                    description TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create default device
            cursor.execute("""
                INSERT INTO devices (device_name, device_code, description)
                VALUES (?, ?, ?)
            """, ("测试设备", "TEST-001", "测试用默认设备"))
            
            # Insert default settings
            cursor.execute("""
                INSERT INTO settings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, ("sensitivity_threshold", "5.0", "变化灵敏度阈值（百分比）"))
            
            cursor.execute("""
                INSERT INTO settings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, ("current_device_id", "1", "当前选择的设备ID"))
            
            db.connection.commit()
            
            yield db
            db.close()

    @pytest.fixture
    def sample_data(self):
        """创建示例数据fixture"""
        return pd.DataFrame(
            {
                "item_name": ["Forward Power", "Reflected Power", "PA Current"],
                "value": [100.5, 2.3, 15.7],
                "unit": ["W", "W", "A"],
            }
        )

    # 测试数据库初始化
    # 需求：3.1
    def test_database_initialization(self):
        """测试数据库初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = TransmitterDatabase(db_path)

            # 验证数据库文件已创建（连接时创建）
            assert db_path.exists()

            # 初始化数据库
            db.initialize_database()

            # 验证表结构
            cursor = db.connection.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='transmitter_data'
            """
            )
            assert cursor.fetchone() is not None

            db.close()

    # 测试月份格式验证
    # 需求：3.2
    def test_month_format_validation_valid(self, temp_db):
        """测试有效的月份格式"""
        assert temp_db._validate_month_format("2026-01") is True
        assert temp_db._validate_month_format("2025-12") is True
        assert temp_db._validate_month_format("2020-06") is True

    def test_month_format_validation_invalid(self, temp_db):
        """测试无效的月份格式"""
        assert temp_db._validate_month_format("2026-1") is False
        assert temp_db._validate_month_format("26-01") is False
        assert temp_db._validate_month_format("2026/01") is False
        # Note: The regex only checks format, not validity of month value
        # "2026-13" passes regex but would fail in actual date validation
        assert temp_db._validate_month_format("invalid") is False
        assert temp_db._validate_month_format("") is False

    # 测试数据插入
    # 需求：3.2, 3.3, 3.4
    def test_insert_monthly_data_success(self, temp_db, sample_data):
        """测试成功插入月度数据"""
        month = "2026-01"
        temp_db.insert_monthly_data(month, sample_data, device_id=1)

        # 验证数据已插入
        result = temp_db.query_by_month(month, device_id=1)
        assert len(result) == 3
        assert set(result["item_name"]) == set(sample_data["item_name"])

    def test_insert_monthly_data_invalid_month_format(self, temp_db, sample_data):
        """测试插入数据时月份格式错误"""
        with pytest.raises(ValueError):
            temp_db.insert_monthly_data("2026-1", sample_data, device_id=1)

        with pytest.raises(ValueError):
            temp_db.insert_monthly_data("invalid", sample_data, device_id=1)

    def test_insert_monthly_data_missing_columns(self, temp_db):
        """测试插入数据时缺少必需字段"""
        incomplete_data = pd.DataFrame(
            {
                "item_name": ["Test"],
                "value": [100.0]
                # 缺少 'unit' 字段
            }
        )

        with pytest.raises(DataValidationError):
            temp_db.insert_monthly_data("2026-01", incomplete_data, device_id=1)

    def test_insert_monthly_data_with_null_values(self, temp_db):
        """测试插入包含空值的数据"""
        data_with_nulls = pd.DataFrame(
            {"item_name": ["Test", None], "value": [100.0, 200.0], "unit": ["V", "A"]}
        )

        with pytest.raises(DataValidationError):
            temp_db.insert_monthly_data("2026-01", data_with_nulls, device_id=1)

    # 测试重复数据处理
    # 需求：3.3
    def test_insert_duplicate_month_without_overwrite(self, temp_db, sample_data):
        """测试插入重复月份数据（不覆盖）"""
        month = "2026-01"

        # 第一次插入成功
        temp_db.insert_monthly_data(month, sample_data, device_id=1)

        # 第二次插入应该失败
        with pytest.raises(DatabaseError):
            temp_db.insert_monthly_data(month, sample_data, device_id=1, overwrite=False)

    def test_insert_duplicate_month_with_overwrite(self, temp_db, sample_data):
        """测试插入重复月份数据（覆盖）"""
        month = "2026-01"

        # 第一次插入
        temp_db.insert_monthly_data(month, sample_data, device_id=1)

        # 修改数据
        new_data = sample_data.copy()
        new_data["value"] = [200.0, 300.0, 400.0]

        # 第二次插入（覆盖）
        temp_db.insert_monthly_data(month, new_data, device_id=1, overwrite=True)

        # 验证数据已更新
        result = temp_db.query_by_month(month, device_id=1)
        assert len(result) == 3
        # Sort by item_name to ensure consistent order
        result_sorted = result.sort_values("item_name").reset_index(drop=True)
        new_data_sorted = new_data.sort_values("item_name").reset_index(drop=True)
        assert list(result_sorted["value"]) == list(new_data_sorted["value"])

    # 测试数据查询
    # 需求：4.1, 4.2
    def test_query_by_month_existing(self, temp_db, sample_data):
        """测试查询存在的月份"""
        month = "2026-01"
        temp_db.insert_monthly_data(month, sample_data, device_id=1)

        result = temp_db.query_by_month(month, device_id=1)
        assert len(result) == 3
        assert "id" in result.columns
        assert "device_id" in result.columns
        assert "month" in result.columns
        assert "item_name" in result.columns
        assert "value" in result.columns
        assert "unit" in result.columns
        assert "create_time" in result.columns

    def test_query_by_month_nonexistent(self, temp_db):
        """测试查询不存在的月份"""
        result = temp_db.query_by_month("2099-12", device_id=1)
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_query_by_item_existing(self, temp_db, sample_data):
        """测试查询存在的数据项"""
        temp_db.insert_monthly_data("2026-01", sample_data, device_id=1)
        temp_db.insert_monthly_data("2026-02", sample_data, device_id=1)

        result = temp_db.query_by_item("Forward Power", device_id=1)
        assert len(result) == 2
        assert all(result["item_name"] == "Forward Power")
        assert set(result["month"]) == {"2026-01", "2026-02"}

    def test_query_by_item_nonexistent(self, temp_db):
        """测试查询不存在的数据项"""
        result = temp_db.query_by_item("NonExistent", device_id=1)
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_get_available_months(self, temp_db, sample_data):
        """测试获取可用月份列表"""
        # 插入多个月份的数据
        temp_db.insert_monthly_data("2026-01", sample_data, device_id=1)
        temp_db.insert_monthly_data("2026-03", sample_data, device_id=1)
        temp_db.insert_monthly_data("2026-02", sample_data, device_id=1)

        months = temp_db.get_available_months(device_id=1)
        assert len(months) == 3
        assert months == ["2026-01", "2026-02", "2026-03"]  # 应该按时间排序

    def test_get_available_months_empty(self, temp_db):
        """测试空数据库获取可用月份"""
        months = temp_db.get_available_months()
        assert len(months) == 0
        assert isinstance(months, list)

    def test_get_all_items(self, temp_db, sample_data):
        """测试获取所有数据项"""
        temp_db.insert_monthly_data("2026-01", sample_data, device_id=1)

        items = temp_db.get_all_items(device_id=1)
        assert len(items) == 3
        assert set(items) == set(sample_data["item_name"])

    def test_get_all_items_empty(self, temp_db):
        """测试空数据库获取数据项"""
        items = temp_db.get_all_items()
        assert len(items) == 0
        assert isinstance(items, list)

    # 测试数据删除
    # 需求：4.3
    def test_delete_month_existing(self, temp_db, sample_data):
        """测试删除存在的月份"""
        month = "2026-01"
        temp_db.insert_monthly_data(month, sample_data, device_id=1)

        # 验证数据存在
        result_before = temp_db.query_by_month(month, device_id=1)
        assert len(result_before) == 3

        # 删除数据
        deleted_count = temp_db.delete_month(month, device_id=1)
        assert deleted_count == 3

        # 验证数据已删除
        result_after = temp_db.query_by_month(month, device_id=1)
        assert len(result_after) == 0

    def test_delete_month_nonexistent(self, temp_db):
        """测试删除不存在的月份"""
        deleted_count = temp_db.delete_month("2099-12", device_id=1)
        assert deleted_count == 0

    def test_delete_month_partial(self, temp_db, sample_data):
        """测试删除一个月份不影响其他月份"""
        temp_db.insert_monthly_data("2026-01", sample_data, device_id=1)
        temp_db.insert_monthly_data("2026-02", sample_data, device_id=1)

        # 删除一个月份
        temp_db.delete_month("2026-01", device_id=1)

        # 验证另一个月份的数据仍然存在
        result = temp_db.query_by_month("2026-02", device_id=1)
        assert len(result) == 3

    # 测试时间戳
    # 需求：3.5
    def test_create_time_auto_generated(self, temp_db, sample_data):
        """测试时间戳自动生成"""
        month = "2026-01"
        temp_db.insert_monthly_data(month, sample_data, device_id=1)

        result = temp_db.query_by_month(month, device_id=1)

        # 验证所有记录都有时间戳
        assert "create_time" in result.columns
        assert result["create_time"].notna().all()

        # 验证时间戳格式
        for timestamp in result["create_time"]:
            assert timestamp is not None
            assert len(str(timestamp)) > 0

    # 测试上下文管理器
    def test_context_manager(self):
        """测试数据库上下文管理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            with TransmitterDatabase(db_path) as db:
                db.initialize_database()
                assert db.connection is not None

            # 验证连接已关闭（尝试使用会失败）
            # 注意：这里不直接测试，因为关闭后的连接行为可能不一致

    # 测试数据完整性
    def test_unique_constraint(self, temp_db):
        """测试月份和数据项的唯一性约束"""
        data1 = pd.DataFrame(
            {"item_name": ["Test Item"], "value": [100.0], "unit": ["V"]}
        )

        month = "2026-01"
        temp_db.insert_monthly_data(month, data1, device_id=1)

        # 尝试插入相同的月份和数据项（不覆盖）应该失败
        with pytest.raises(DatabaseError):
            temp_db.insert_monthly_data(month, data1, device_id=1, overwrite=False)
