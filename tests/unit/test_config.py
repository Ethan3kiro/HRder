"""
配置模块单元测试

测试跨平台路径管理功能
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.config import Config


class TestPathManagement:
    """路径管理测试类"""

    def test_get_default_db_path_structure(self):
        """测试默认数据库路径结构"""
        db_path = Config.get_default_db_path()

        # 验证返回类型
        assert isinstance(db_path, Path)

        # 验证路径包含Documents目录
        assert "Documents" in str(db_path)

        # 验证文件名正确
        assert db_path.name == "transmitter_data.db"

        # 验证Documents目录存在
        assert db_path.parent.exists()

    @patch("platform.system")
    def test_get_default_db_path_mac(self, mock_system, tmp_path):
        """测试Mac系统默认数据库路径"""
        # 模拟Mac系统
        mock_system.return_value = "Darwin"

        # 使用临时目录
        with patch("pathlib.Path.home", return_value=tmp_path):
            db_path = Config.get_default_db_path()

            # 验证路径格式
            expected_path = tmp_path / "Documents" / "transmitter_data.db"
            assert db_path == expected_path

            # 验证Documents目录被创建
            assert (tmp_path / "Documents").exists()

            # 验证路径使用pathlib（跨平台兼容）
            assert isinstance(db_path, Path)

    @patch("platform.system")
    def test_get_default_db_path_windows(self, mock_system, tmp_path):
        """测试Windows系统默认数据库路径"""
        # 模拟Windows系统
        mock_system.return_value = "Windows"

        # 使用临时目录
        with patch("pathlib.Path.home", return_value=tmp_path):
            db_path = Config.get_default_db_path()

            # 验证路径格式
            expected_path = tmp_path / "Documents" / "transmitter_data.db"
            assert db_path == expected_path

            # 验证Documents目录被创建
            assert (tmp_path / "Documents").exists()

            # 验证pathlib正确处理路径
            assert "Documents" in db_path.parts
            assert db_path.name == "transmitter_data.db"

    def test_get_default_log_path_structure(self):
        """测试默认日志路径结构"""
        log_path = Config.get_default_log_path()

        # 验证返回类型
        assert isinstance(log_path, Path)

        # 验证路径包含Documents目录
        assert "Documents" in str(log_path)

        # 验证目录名正确
        assert log_path.name == "transmitter_logs"

        # 验证目录存在（函数会创建）
        assert log_path.exists()
        assert log_path.is_dir()

    @patch("platform.system")
    def test_get_default_log_path_mac(self, mock_system, tmp_path):
        """测试Mac系统默认日志路径"""
        # 模拟Mac系统
        mock_system.return_value = "Darwin"

        # 使用临时目录
        with patch("pathlib.Path.home", return_value=tmp_path):
            log_path = Config.get_default_log_path()

            # 验证路径格式
            expected_path = tmp_path / "Documents" / "transmitter_logs"
            assert log_path == expected_path

            # 验证目录被创建
            assert log_path.exists()
            assert log_path.is_dir()

    @patch("platform.system")
    def test_get_default_log_path_windows(self, mock_system, tmp_path):
        """测试Windows系统默认日志路径"""
        # 模拟Windows系统
        mock_system.return_value = "Windows"

        # 使用临时目录
        with patch("pathlib.Path.home", return_value=tmp_path):
            log_path = Config.get_default_log_path()

            # 验证路径格式
            expected_path = tmp_path / "Documents" / "transmitter_logs"
            assert log_path == expected_path

            # 验证pathlib正确处理路径
            assert "Documents" in log_path.parts
            assert log_path.name == "transmitter_logs"

            # 验证目录被创建
            assert log_path.exists()
            assert log_path.is_dir()

    def test_path_creation_db(self, tmp_path):
        """测试数据库路径创建功能"""
        # 使用临时目录模拟home目录
        with patch("pathlib.Path.home", return_value=tmp_path):
            db_path = Config.get_default_db_path()

            # 验证Documents目录被创建
            documents_dir = tmp_path / "Documents"
            assert documents_dir.exists()
            assert documents_dir.is_dir()

            # 验证路径正确
            assert db_path == documents_dir / "transmitter_data.db"

    def test_path_creation_log(self, tmp_path):
        """测试日志路径创建功能"""
        # 使用临时目录模拟home目录
        with patch("pathlib.Path.home", return_value=tmp_path):
            log_path = Config.get_default_log_path()

            # 验证Documents目录被创建
            documents_dir = tmp_path / "Documents"
            assert documents_dir.exists()
            assert documents_dir.is_dir()

            # 验证日志目录被创建
            assert log_path.exists()
            assert log_path.is_dir()
            assert log_path == documents_dir / "transmitter_logs"

    def test_path_creation_idempotent(self, tmp_path):
        """测试路径创建的幂等性（多次调用不会出错）"""
        with patch("pathlib.Path.home", return_value=tmp_path):
            # 第一次调用
            db_path1 = Config.get_default_db_path()
            log_path1 = Config.get_default_log_path()

            # 第二次调用
            db_path2 = Config.get_default_db_path()
            log_path2 = Config.get_default_log_path()

            # 验证路径一致
            assert db_path1 == db_path2
            assert log_path1 == log_path2

            # 验证目录仍然存在
            assert log_path1.exists()
            assert log_path2.exists()

    def test_pathlib_cross_platform_compatibility(self):
        """测试pathlib的跨平台兼容性"""
        # 验证使用pathlib而不是字符串拼接
        db_path = Config.get_default_db_path()
        log_path = Config.get_default_log_path()

        # 验证返回的是Path对象
        assert isinstance(db_path, Path)
        assert isinstance(log_path, Path)

        # 验证可以使用Path的方法
        assert hasattr(db_path, "exists")
        assert hasattr(db_path, "parent")
        assert hasattr(db_path, "name")

        # 验证路径分隔符由pathlib自动处理
        # pathlib会根据操作系统自动使用正确的分隔符
        assert db_path.parent.name == "Documents"
        assert log_path.parent.name == "Documents"


class TestTesseractPath:
    """Tesseract路径测试类"""

    @patch("platform.system")
    @patch("pathlib.Path.exists")
    def test_get_tesseract_path_mac(self, mock_exists, mock_system):
        """测试Mac系统Tesseract路径检测"""
        mock_system.return_value = "Darwin"
        mock_exists.return_value = True

        tesseract_path = Config.get_tesseract_path()

        assert tesseract_path == "/usr/local/bin/tesseract"

    @patch("platform.system")
    @patch("pathlib.Path.exists")
    def test_get_tesseract_path_windows(self, mock_exists, mock_system):
        """测试Windows系统Tesseract路径检测"""
        mock_system.return_value = "Windows"
        mock_exists.return_value = True

        tesseract_path = Config.get_tesseract_path()

        assert tesseract_path == r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    @patch("platform.system")
    @patch("pathlib.Path.exists")
    def test_get_tesseract_path_not_found(self, mock_exists, mock_system):
        """测试Tesseract未安装的情况"""
        mock_system.return_value = "Darwin"
        mock_exists.return_value = False

        tesseract_path = Config.get_tesseract_path()

        assert tesseract_path is None


class TestImageFormatValidation:
    """图像格式验证测试类"""

    def test_is_supported_image_png(self):
        """测试PNG格式支持"""
        assert Config.is_supported_image(Path("test.png"))
        assert Config.is_supported_image(Path("test.PNG"))

    def test_is_supported_image_jpg(self):
        """测试JPG格式支持"""
        assert Config.is_supported_image(Path("test.jpg"))
        assert Config.is_supported_image(Path("test.jpeg"))
        assert Config.is_supported_image(Path("test.JPG"))

    def test_is_supported_image_other_formats(self):
        """测试其他支持的格式"""
        assert Config.is_supported_image(Path("test.bmp"))
        assert Config.is_supported_image(Path("test.tiff"))

    def test_is_supported_image_unsupported(self):
        """测试不支持的格式"""
        assert not Config.is_supported_image(Path("test.txt"))
        assert not Config.is_supported_image(Path("test.pdf"))
        assert not Config.is_supported_image(Path("test.doc"))
