"""
设备管理模块单元测试
"""
import pytest
import tempfile
from pathlib import Path

from src.database import TransmitterDatabase
from src.device_manager import DeviceManager
from src.exceptions import DatabaseError


class TestDeviceManager:
    """设备管理器测试类"""

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
    def device_manager(self, temp_db):
        """创建设备管理器fixture"""
        return DeviceManager(temp_db)

    def test_add_device(self, device_manager):
        """测试添加设备"""
        device_id = device_manager.add_device(
            device_name="测试设备A",
            device_code="TEST-A-001",
            description="测试用设备A"
        )
        
        assert device_id > 0
        
        # 验证设备已添加
        device = device_manager.get_device_by_id(device_id)
        assert device is not None
        assert device["device_name"] == "测试设备A"
        assert device["device_code"] == "TEST-A-001"

    def test_add_duplicate_device_name(self, device_manager):
        """测试添加重复设备名"""
        device_manager.add_device("设备A", "CODE-001")
        
        with pytest.raises(DatabaseError):
            device_manager.add_device("设备A", "CODE-002")

    def test_get_all_devices(self, device_manager):
        """测试获取所有设备"""
        device_manager.add_device("设备A", "CODE-A")
        device_manager.add_device("设备B", "CODE-B")
        device_manager.add_device("设备C", "CODE-C")
        
        devices = device_manager.get_all_devices()
        assert len(devices) == 3
        assert {d["device_name"] for d in devices} == {"设备A", "设备B", "设备C"}

    def test_get_device_by_id(self, device_manager):
        """测试根据ID获取设备"""
        device_id = device_manager.add_device("设备A", "CODE-A")
        
        device = device_manager.get_device_by_id(device_id)
        assert device is not None
        assert device["id"] == device_id
        assert device["device_name"] == "设备A"

    def test_get_device_by_id_nonexistent(self, device_manager):
        """测试获取不存在的设备"""
        device = device_manager.get_device_by_id(9999)
        assert device is None

    def test_update_device(self, device_manager):
        """测试更新设备信息"""
        device_id = device_manager.add_device("设备A", "CODE-A", "描述A")
        
        device_manager.update_device(
            device_id=device_id,
            device_name="设备A更新",
            device_code="CODE-A-NEW",
            description="新描述"
        )
        
        device = device_manager.get_device_by_id(device_id)
        assert device["device_name"] == "设备A更新"
        assert device["device_code"] == "CODE-A-NEW"
        assert device["description"] == "新描述"

    def test_delete_device(self, device_manager):
        """测试删除设备"""
        device_id = device_manager.add_device("设备A", "CODE-A")
        
        result = device_manager.delete_device(device_id, confirm=True)
        assert result >= 0
        
        device = device_manager.get_device_by_id(device_id)
        assert device is None

    def test_delete_nonexistent_device(self, device_manager):
        """测试删除不存在的设备"""
        with pytest.raises(DatabaseError):
            device_manager.delete_device(9999, confirm=True)
