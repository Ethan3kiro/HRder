"""
路径管理属性测试

测试跨平台路径管理功能的正确性属性
"""
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest

from src.config import Config


class TestPathProperties:
    """路径管理属性测试类"""

    @settings(
        max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        home_dir=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
            min_size=1,
            max_size=20,
        )
    )
    def test_property_cross_platform_path_detection(self, home_dir, tmp_path):
        """
        Feature: transmitter-data-analyzer, Property 4: 跨平台路径检测

        对于任何操作系统（Mac或Windows），系统应该能够自动检测并使用正确的默认数据库路径和Tesseract路径。
        **验证：需求 2.4**
        """
        # 创建临时home目录
        mock_home = tmp_path / home_dir
        mock_home.mkdir(parents=True, exist_ok=True)

        with patch("pathlib.Path.home", return_value=mock_home):
            # 测试数据库路径
            db_path = Config.get_default_db_path()

            # 验证路径是Path对象
            assert isinstance(db_path, Path), "数据库路径应该是Path对象"

            # 验证路径包含Documents目录
            assert "Documents" in str(db_path), "路径应该包含Documents目录"

            # 验证路径以正确的数据库文件名结尾
            assert (
                db_path.name == Config.DEFAULT_DB_NAME
            ), f"数据库文件名应该是{Config.DEFAULT_DB_NAME}"

            # 验证Documents目录被创建
            documents_dir = mock_home / "Documents"
            assert documents_dir.exists(), "Documents目录应该被自动创建"

            # 测试日志路径
            log_path = Config.get_default_log_path()

            # 验证路径是Path对象
            assert isinstance(log_path, Path), "日志路径应该是Path对象"

            # 验证路径包含Documents目录
            assert "Documents" in str(log_path), "日志路径应该包含Documents目录"

            # 验证路径以正确的日志目录名结尾
            assert (
                log_path.name == Config.DEFAULT_LOG_DIR_NAME
            ), f"日志目录名应该是{Config.DEFAULT_LOG_DIR_NAME}"

            # 验证日志目录被创建
            assert log_path.exists(), "日志目录应该被自动创建"

    def test_property_path_consistency_across_platforms(self):
        """
        Feature: transmitter-data-analyzer, Property 4: 跨平台路径检测

        验证在不同操作系统上路径结构的一致性

        **验证：需求 2.4**
        """
        current_system = platform.system()

        # 获取默认路径
        db_path = Config.get_default_db_path()
        log_path = Config.get_default_log_path()

        # 验证路径使用正确的分隔符（pathlib会自动处理）
        # 在所有平台上，pathlib.Path都应该正确工作
        assert isinstance(db_path, Path)
        assert isinstance(log_path, Path)

        # 验证路径是绝对路径
        assert db_path.is_absolute(), "数据库路径应该是绝对路径"
        assert log_path.is_absolute(), "日志路径应该是绝对路径"

        # 验证路径包含home目录
        home = Path.home()
        assert str(home) in str(db_path), "数据库路径应该在home目录下"
        assert str(home) in str(log_path), "日志路径应该在home目录下"

        # 验证路径结构
        assert db_path.parent.name == "Documents", "数据库应该在Documents目录下"
        assert log_path.parent.name == "Documents", "日志目录应该在Documents目录下"

    @settings(
        max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        db_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
            min_size=1,
            max_size=20,
        ).map(lambda x: f"{x}.db" if x else "test.db")
    )
    def test_property_path_with_different_filenames(self, db_name, tmp_path):
        """
        Feature: transmitter-data-analyzer, Property 4: 跨平台路径检测

        验证路径函数对不同文件名的处理

        **验证：需求 2.4**
        """
        mock_home = tmp_path / "test_home"
        mock_home.mkdir(parents=True, exist_ok=True)

        with patch("pathlib.Path.home", return_value=mock_home):
            # 临时修改默认数据库名称
            original_db_name = Config.DEFAULT_DB_NAME
            try:
                Config.DEFAULT_DB_NAME = db_name

                db_path = Config.get_default_db_path()

                # 验证路径正确包含新的文件名
                assert db_path.name == db_name, f"数据库文件名应该是{db_name}"

                # 验证路径仍然在Documents目录下
                assert db_path.parent.name == "Documents", "数据库应该在Documents目录下"

            finally:
                # 恢复原始配置
                Config.DEFAULT_DB_NAME = original_db_name

    def test_property_tesseract_path_detection(self):
        """
        Feature: transmitter-data-analyzer, Property 4: 跨平台路径检测

        验证Tesseract路径检测功能

        **验证：需求 2.4**
        """
        current_system = platform.system()

        # 获取Tesseract路径
        tesseract_path = Config.get_tesseract_path()

        # 验证返回值类型
        assert tesseract_path is None or isinstance(
            tesseract_path, str
        ), "Tesseract路径应该是字符串或None"

        # 如果返回了路径，验证它对应当前系统
        if tesseract_path:
            expected_path = Config.TESSERACT_PATHS.get(current_system)
            assert (
                tesseract_path == expected_path
            ), f"Tesseract路径应该匹配当前系统({current_system})的默认路径"

            # 验证路径存在
            assert Path(tesseract_path).exists(), "返回的Tesseract路径应该存在"
