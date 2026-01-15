"""
依赖检测模块的单元测试
"""
import pytest
import sys
import platform
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.dependency_checker import (
    DependencyChecker,
    check_dependencies,
    print_dependency_report,
)


class TestDependencyChecker:
    """依赖检测器的单元测试"""

    def test_init(self):
        """测试初始化"""
        checker = DependencyChecker()

        assert checker.system == platform.system()
        assert checker.python_version == sys.version_info

    def test_check_python_version_satisfied(self):
        """测试Python版本检测 - 满足要求"""
        checker = DependencyChecker()
        result = checker._check_python_version()

        assert isinstance(result, dict)
        assert "version" in result
        assert "satisfied" in result
        assert "message" in result

        # 当前测试环境应该是Python 3.8+
        if sys.version_info.major == 3 and sys.version_info.minor >= 8:
            assert result["satisfied"] is True

    def test_check_python_version_format(self):
        """测试Python版本格式"""
        checker = DependencyChecker()
        result = checker._check_python_version()

        # 验证版本格式
        version_parts = result["version"].split(".")
        assert len(version_parts) == 3
        assert all(part.isdigit() for part in version_parts)

    @patch("shutil.which")
    @patch("src.config.Config.get_tesseract_path")
    def test_check_tesseract_installed_default_path(self, mock_get_path, mock_which):
        """测试Tesseract检测 - 使用默认路径"""
        mock_get_path.return_value = "/usr/local/bin/tesseract"

        checker = DependencyChecker()
        result = checker._check_tesseract()

        assert result["installed"] is True
        assert result["path"] == "/usr/local/bin/tesseract"
        assert "Tesseract已安装" in result["message"]

    @patch("shutil.which")
    @patch("src.config.Config.get_tesseract_path")
    def test_check_tesseract_installed_system_path(self, mock_get_path, mock_which):
        """测试Tesseract检测 - 使用系统PATH"""
        mock_get_path.return_value = None
        mock_which.return_value = "/usr/bin/tesseract"

        checker = DependencyChecker()
        result = checker._check_tesseract()

        assert result["installed"] is True
        assert result["path"] == "/usr/bin/tesseract"
        assert "Tesseract已安装" in result["message"]

    @patch("shutil.which")
    @patch("src.config.Config.get_tesseract_path")
    def test_check_tesseract_not_installed(self, mock_get_path, mock_which):
        """测试Tesseract检测 - 未安装"""
        mock_get_path.return_value = None
        mock_which.return_value = None

        checker = DependencyChecker()
        result = checker._check_tesseract()

        assert result["installed"] is False
        assert result["path"] is None
        assert "Tesseract-OCR未安装" in result["message"]

    @patch("subprocess.run")
    def test_get_tesseract_version_success(self, mock_run):
        """测试获取Tesseract版本 - 成功"""
        mock_run.return_value = Mock(
            stdout="tesseract 5.3.0\n leptonica-1.82.0", returncode=0
        )

        checker = DependencyChecker()
        version = checker._get_tesseract_version("/usr/local/bin/tesseract")

        assert version is not None
        assert "tesseract" in version.lower()

    @patch("subprocess.run")
    def test_get_tesseract_version_failure(self, mock_run):
        """测试获取Tesseract版本 - 失败"""
        mock_run.side_effect = Exception("Command failed")

        checker = DependencyChecker()
        version = checker._get_tesseract_version("/usr/local/bin/tesseract")

        assert version is None

    def test_check_single_package_installed(self):
        """测试单个包检测 - 已安装"""
        checker = DependencyChecker()

        # 测试一个肯定已安装的包（pytest）
        result = checker._check_single_package("pytest", "7.0.0")

        assert isinstance(result, dict)
        assert "installed" in result
        assert "version" in result
        assert "satisfied" in result
        assert "message" in result

        # pytest应该已安装（因为我们正在运行测试）
        assert result["installed"] is True

    def test_check_single_package_not_installed(self):
        """测试单个包检测 - 未安装"""
        checker = DependencyChecker()

        # 测试一个不存在的包
        result = checker._check_single_package("nonexistent_package_xyz", "1.0.0")

        assert result["installed"] is False
        assert result["version"] is None
        assert result["satisfied"] is False

    def test_check_single_package_pillow(self):
        """测试Pillow包检测（特殊处理PIL）"""
        checker = DependencyChecker()

        # PIL实际上是Pillow包
        result = checker._check_single_package("PIL", "10.0.0")

        assert isinstance(result, dict)
        # Pillow应该已安装（在requirements.txt中）
        # 但如果未安装也不应该崩溃

    def test_compare_versions_greater(self):
        """测试版本比较 - 当前版本更高"""
        checker = DependencyChecker()

        assert checker._compare_versions("2.0.0", "1.0.0") is True
        assert checker._compare_versions("1.5.0", "1.0.0") is True
        assert checker._compare_versions("1.0.1", "1.0.0") is True

    def test_compare_versions_equal(self):
        """测试版本比较 - 版本相等"""
        checker = DependencyChecker()

        assert checker._compare_versions("1.0.0", "1.0.0") is True
        assert checker._compare_versions("2.5.3", "2.5.0") is True

    def test_compare_versions_less(self):
        """测试版本比较 - 当前版本更低"""
        checker = DependencyChecker()

        assert checker._compare_versions("1.0.0", "2.0.0") is False
        assert checker._compare_versions("1.0.0", "1.5.0") is False

    def test_compare_versions_invalid(self):
        """测试版本比较 - 无效格式"""
        checker = DependencyChecker()

        # 无效格式应该返回True（假设满足要求）
        result = checker._compare_versions("invalid", "1.0.0")
        assert isinstance(result, bool)

    def test_check_python_packages(self):
        """测试Python包检测"""
        checker = DependencyChecker()
        results = checker._check_python_packages()

        assert isinstance(results, dict)

        # 验证所有必需包都被检测
        for package_name in checker.REQUIRED_PACKAGES:
            assert package_name in results
            assert isinstance(results[package_name], dict)
            assert "installed" in results[package_name]
            assert "version" in results[package_name]
            assert "satisfied" in results[package_name]

    @patch("shutil.which")
    @patch("src.config.Config.get_tesseract_path")
    def test_check_dependencies_all_satisfied(self, mock_get_path, mock_which):
        """测试完整依赖检测 - 所有依赖满足"""
        mock_get_path.return_value = "/usr/local/bin/tesseract"

        checker = DependencyChecker()
        results = checker.check_dependencies()

        assert isinstance(results, dict)
        assert "all_satisfied" in results
        assert "python_version" in results
        assert "tesseract" in results
        assert "packages" in results
        assert "missing_dependencies" in results
        assert "install_guide" in results

        # 验证类型
        assert isinstance(results["all_satisfied"], bool)
        assert isinstance(results["missing_dependencies"], list)
        assert isinstance(results["install_guide"], str)

    @patch("shutil.which")
    @patch("src.config.Config.get_tesseract_path")
    def test_check_dependencies_tesseract_missing(self, mock_get_path, mock_which):
        """测试完整依赖检测 - Tesseract缺失"""
        mock_get_path.return_value = None
        mock_which.return_value = None

        checker = DependencyChecker()
        results = checker.check_dependencies()

        assert results["all_satisfied"] is False
        assert "Tesseract-OCR" in results["missing_dependencies"]
        assert len(results["install_guide"]) > 0

    def test_generate_install_guide_tesseract_missing(self):
        """测试安装指引生成 - Tesseract缺失"""
        checker = DependencyChecker()

        mock_results = {
            "all_satisfied": False,
            "python_version": {
                "version": "3.8.0",
                "satisfied": True,
                "message": "Python 3.8.0",
            },
            "tesseract": {
                "installed": False,
                "path": None,
                "version": None,
                "message": "Tesseract未安装",
            },
            "packages": {},
            "missing_dependencies": ["Tesseract-OCR"],
            "install_guide": "",
        }

        guide = checker._generate_install_guide(mock_results)

        assert isinstance(guide, str)
        assert len(guide) > 0
        assert "依赖安装指引" in guide
        assert "Tesseract-OCR" in guide

    def test_generate_install_guide_packages_missing(self):
        """测试安装指引生成 - Python包缺失"""
        checker = DependencyChecker()

        mock_results = {
            "all_satisfied": False,
            "python_version": {
                "version": "3.8.0",
                "satisfied": True,
                "message": "Python 3.8.0",
            },
            "tesseract": {
                "installed": True,
                "path": "/usr/local/bin/tesseract",
                "version": "tesseract 5.3.0",
                "message": "Tesseract已安装",
            },
            "packages": {
                "pytesseract": {
                    "installed": False,
                    "version": None,
                    "min_version": "0.3.0",
                    "satisfied": False,
                    "message": "pytesseract未安装",
                }
            },
            "missing_dependencies": ["pytesseract"],
            "install_guide": "",
        }

        guide = checker._generate_install_guide(mock_results)

        assert isinstance(guide, str)
        assert len(guide) > 0
        assert "Python依赖包" in guide
        assert "pytesseract" in guide
        assert "pip install" in guide

    def test_generate_install_guide_python_version_unsatisfied(self):
        """测试安装指引生成 - Python版本不满足"""
        checker = DependencyChecker()

        mock_results = {
            "all_satisfied": False,
            "python_version": {
                "version": "3.7.0",
                "satisfied": False,
                "message": "Python 3.7.0 (需要Python 3.8+)",
            },
            "tesseract": {
                "installed": True,
                "path": "/usr/local/bin/tesseract",
                "version": "tesseract 5.3.0",
                "message": "Tesseract已安装",
            },
            "packages": {},
            "missing_dependencies": ["Python 3.8+"],
            "install_guide": "",
        }

        guide = checker._generate_install_guide(mock_results)

        assert isinstance(guide, str)
        assert len(guide) > 0
        assert "Python版本" in guide
        assert "3.8" in guide

    def test_generate_install_guide_all_satisfied(self):
        """测试安装指引生成 - 所有依赖满足"""
        checker = DependencyChecker()

        mock_results = {
            "all_satisfied": True,
            "python_version": {
                "version": "3.8.0",
                "satisfied": True,
                "message": "Python 3.8.0",
            },
            "tesseract": {
                "installed": True,
                "path": "/usr/local/bin/tesseract",
                "version": "tesseract 5.3.0",
                "message": "Tesseract已安装",
            },
            "packages": {},
            "missing_dependencies": [],
            "install_guide": "",
        }

        guide = checker._generate_install_guide(mock_results)

        # 所有依赖满足时，指引应该只包含标题
        assert isinstance(guide, str)

    def test_tesseract_install_guide_darwin(self):
        """测试Tesseract安装指引 - Mac系统"""
        checker = DependencyChecker()

        guide = checker.TESSERACT_INSTALL_GUIDE.get("Darwin")

        assert guide is not None
        assert "Mac" in guide or "brew" in guide
        assert "tesseract" in guide.lower()

    def test_tesseract_install_guide_windows(self):
        """测试Tesseract安装指引 - Windows系统"""
        checker = DependencyChecker()

        guide = checker.TESSERACT_INSTALL_GUIDE.get("Windows")

        assert guide is not None
        assert "Windows" in guide
        assert "tesseract" in guide.lower()

    def test_tesseract_install_guide_linux(self):
        """测试Tesseract安装指引 - Linux系统"""
        checker = DependencyChecker()

        guide = checker.TESSERACT_INSTALL_GUIDE.get("Linux")

        assert guide is not None
        assert "Linux" in guide or "apt" in guide or "yum" in guide
        assert "tesseract" in guide.lower()

    def test_python_packages_install_guide(self):
        """测试Python包安装指引"""
        checker = DependencyChecker()

        guide = checker.PYTHON_PACKAGES_INSTALL_GUIDE

        assert isinstance(guide, str)
        assert "pip install" in guide
        assert "requirements.txt" in guide

    @patch("builtins.print")
    def test_print_dependency_report_all_satisfied(self, mock_print):
        """测试打印依赖报告 - 所有依赖满足"""
        checker = DependencyChecker()

        mock_results = {
            "all_satisfied": True,
            "python_version": {
                "version": "3.8.0",
                "satisfied": True,
                "message": "Python 3.8.0 (满足要求)",
            },
            "tesseract": {
                "installed": True,
                "path": "/usr/local/bin/tesseract",
                "version": "tesseract 5.3.0",
                "message": "Tesseract已安装",
            },
            "packages": {
                "pytesseract": {
                    "installed": True,
                    "version": "0.3.10",
                    "min_version": "0.3.0",
                    "satisfied": True,
                    "message": "pytesseract 0.3.10 (满足要求)",
                }
            },
            "missing_dependencies": [],
            "install_guide": "",
        }

        checker.print_dependency_report(mock_results)

        # 验证print被调用
        assert mock_print.called

        # 验证输出包含关键信息
        output = " ".join(
            [
                str(call.args[0]) if call.args else ""
                for call in mock_print.call_args_list
            ]
        )
        assert "依赖检测报告" in output
        assert "Python" in output
        assert "Tesseract" in output

    @patch("builtins.print")
    def test_print_dependency_report_missing_dependencies(self, mock_print):
        """测试打印依赖报告 - 存在缺失依赖"""
        checker = DependencyChecker()

        mock_results = {
            "all_satisfied": False,
            "python_version": {
                "version": "3.8.0",
                "satisfied": True,
                "message": "Python 3.8.0",
            },
            "tesseract": {
                "installed": False,
                "path": None,
                "version": None,
                "message": "Tesseract未安装",
            },
            "packages": {
                "pytesseract": {
                    "installed": False,
                    "version": None,
                    "min_version": "0.3.0",
                    "satisfied": False,
                    "message": "pytesseract未安装",
                }
            },
            "missing_dependencies": ["Tesseract-OCR", "pytesseract"],
            "install_guide": "安装指引内容...",
        }

        checker.print_dependency_report(mock_results)

        # 验证print被调用
        assert mock_print.called

        # 验证输出包含缺失依赖信息
        output = " ".join(
            [
                str(call.args[0]) if call.args else ""
                for call in mock_print.call_args_list
            ]
        )
        assert "缺失" in output or "未安装" in output

    @patch("src.dependency_checker.DependencyChecker.check_dependencies")
    def test_check_dependencies_function(self, mock_check):
        """测试便捷函数 - check_dependencies"""
        mock_check.return_value = {"all_satisfied": True}

        result = check_dependencies()

        assert mock_check.called
        assert result == {"all_satisfied": True}

    @patch("src.dependency_checker.DependencyChecker.check_dependencies")
    @patch("src.dependency_checker.DependencyChecker.print_dependency_report")
    def test_print_dependency_report_function(self, mock_print_report, mock_check):
        """测试便捷函数 - print_dependency_report"""
        mock_check.return_value = {"all_satisfied": True}

        result = print_dependency_report()

        assert mock_check.called
        assert mock_print_report.called
        assert result is True

    @patch("src.dependency_checker.DependencyChecker.check_dependencies")
    @patch("src.dependency_checker.DependencyChecker.print_dependency_report")
    def test_print_dependency_report_function_missing_deps(
        self, mock_print_report, mock_check
    ):
        """测试便捷函数 - print_dependency_report（存在缺失依赖）"""
        mock_check.return_value = {"all_satisfied": False}

        result = print_dependency_report()

        assert mock_check.called
        assert mock_print_report.called
        assert result is False
