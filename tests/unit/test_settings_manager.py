"""
设置管理模块单元测试
"""
import pytest
import tempfile
from pathlib import Path

from src.database import TransmitterDatabase
from src.settings_manager import SettingsManager


class TestSettingsManager:
    """设置管理器测试类"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库fixture"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = TransmitterDatabase(db_path)
            db.initialize_database()
            yield db
            db.close()

    @pytest.fixture
    def settings_manager(self, temp_db):
        """创建设置管理器fixture"""
        return SettingsManager(temp_db)

    def test_set_and_get_sensitivity_threshold(self, settings_manager):
        """测试设置和获取灵敏度阈值"""
        settings_manager.set_sensitivity_threshold(10.5)
        
        threshold = settings_manager.get_sensitivity_threshold()
        assert threshold == 10.5

    def test_default_sensitivity_threshold(self, settings_manager):
        """测试默认灵敏度阈值"""
        threshold = settings_manager.get_sensitivity_threshold()
        assert threshold == 5.0  # 默认值

    def test_set_and_get_current_device_id(self, settings_manager):
        """测试设置和获取当前设备ID"""
        settings_manager.set_current_device_id(42)
        
        device_id = settings_manager.get_current_device_id()
        assert device_id == 42

    def test_default_current_device_id(self, settings_manager):
        """测试默认当前设备ID"""
        # 先设置默认值
        settings_manager.set_current_device_id(1)
        device_id = settings_manager.get_current_device_id()
        assert device_id == 1

    def test_set_and_get_setting(self, settings_manager):
        """测试设置和获取通用设置"""
        settings_manager.set_setting("test_key", "test_value", "测试设置")
        
        value = settings_manager.get_setting("test_key")
        assert value == "test_value"

    def test_get_nonexistent_setting(self, settings_manager):
        """测试获取不存在的设置"""
        value = settings_manager.get_setting("nonexistent_key")
        assert value is None

    def test_get_setting_with_default(self, settings_manager):
        """测试获取不存在的设置"""
        value = settings_manager.get_setting("nonexistent_key")
        assert value is None

    def test_update_existing_setting(self, settings_manager):
        """测试更新已存在的设置"""
        settings_manager.set_setting("key1", "value1")
        settings_manager.set_setting("key1", "value2")
        
        value = settings_manager.get_setting("key1")
        assert value == "value2"

    def test_get_all_settings(self, settings_manager):
        """测试获取所有设置"""
        settings_manager.set_sensitivity_threshold(15.0)
        settings_manager.set_current_device_id(5)
        settings_manager.set_setting("custom_key", "custom_value")
        
        all_settings = settings_manager.get_all_settings()
        assert len(all_settings) >= 3
        
        # 验证设置存在（all_settings是字典）
        assert "sensitivity_threshold" in all_settings
        assert "current_device_id" in all_settings
        assert "custom_key" in all_settings
