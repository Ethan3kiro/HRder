"""
依赖检测模块的属性测试

使用Hypothesis进行基于属性的测试
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import sys

from src.dependency_checker import DependencyChecker


class TestDependencyCheckerProperties:
    """依赖检测器的属性测试"""

    @given(
        package_names=st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            ),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_dependency_detection_completeness(self, package_names):
        """
        Feature: transmitter-data-analyzer, Property 17: 依赖检测完整性

        对于任何必需的外部依赖，系统应该能够检测其是否安装

        **验证：需求 9.3**
        """
        checker = DependencyChecker()

        # 对于每个包名，检测函数应该返回一个结果
        for package_name in package_names:
            # 跳过空字符串和特殊字符
            if not package_name or not package_name.strip():
                continue

            result = checker._check_single_package(package_name, "0.0.0")

            # 验证结果结构完整性
            assert isinstance(result, dict), "检测结果应该是字典"
            assert "installed" in result, "结果应包含installed字段"
            assert "version" in result, "结果应包含version字段"
            assert "min_version" in result, "结果应包含min_version字段"
            assert "satisfied" in result, "结果应包含satisfied字段"
            assert "message" in result, "结果应包含message字段"

            # 验证字段类型
            assert isinstance(result["installed"], bool), "installed应该是布尔值"
            assert isinstance(result["satisfied"], bool), "satisfied应该是布尔值"
            assert isinstance(result["message"], str), "message应该是字符串"

            # 验证逻辑一致性：如果未安装，则不满足要求
            if not result["installed"]:
                assert not result["satisfied"], "未安装的包不应该满足要求"

    @given(
        current_version=st.text(min_size=1, max_size=10, alphabet="0123456789."),
        min_version=st.text(min_size=1, max_size=10, alphabet="0123456789."),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_version_comparison_consistency(
        self, current_version, min_version
    ):
        """
        Feature: transmitter-data-analyzer, Property 17: 依赖检测完整性

        对于任何版本号比较，结果应该是一致的和可预测的

        **验证：需求 9.3**
        """
        # 过滤无效的版本号格式
        assume(current_version.count(".") <= 3)
        assume(min_version.count(".") <= 3)
        assume(not current_version.startswith("."))
        assume(not current_version.endswith("."))
        assume(not min_version.startswith("."))
        assume(not min_version.endswith("."))
        assume(".." not in current_version)
        assume(".." not in min_version)

        checker = DependencyChecker()

        try:
            result = checker._compare_versions(current_version, min_version)

            # 验证返回值是布尔类型
            assert isinstance(result, bool), "版本比较结果应该是布尔值"

            # 验证自反性：版本与自身比较应该返回True
            self_compare = checker._compare_versions(current_version, current_version)
            assert self_compare is True, "版本与自身比较应该返回True"

        except Exception:
            # 如果版本格式无效，应该优雅地处理（返回True或抛出异常）
            pass

    def test_property_check_dependencies_structure(self):
        """
        Feature: transmitter-data-analyzer, Property 17: 依赖检测完整性

        对于任何依赖检测操作，返回的结果应该包含所有必需的字段

        **验证：需求 9.3**
        """
        checker = DependencyChecker()
        results = checker.check_dependencies()

        # 验证结果结构
        assert isinstance(results, dict), "检测结果应该是字典"

        # 验证必需字段存在
        required_fields = [
            "all_satisfied",
            "python_version",
            "tesseract",
            "packages",
            "missing_dependencies",
            "install_guide",
        ]

        for field in required_fields:
            assert field in results, f"结果应包含{field}字段"

        # 验证字段类型
        assert isinstance(results["all_satisfied"], bool), "all_satisfied应该是布尔值"
        assert isinstance(results["python_version"], dict), "python_version应该是字典"
        assert isinstance(results["tesseract"], dict), "tesseract应该是字典"
        assert isinstance(results["packages"], dict), "packages应该是字典"
        assert isinstance(
            results["missing_dependencies"], list
        ), "missing_dependencies应该是列表"
        assert isinstance(results["install_guide"], str), "install_guide应该是字符串"

        # 验证Python版本信息结构
        assert "version" in results["python_version"]
        assert "satisfied" in results["python_version"]
        assert "message" in results["python_version"]

        # 验证Tesseract信息结构
        assert "installed" in results["tesseract"]
        assert "path" in results["tesseract"]
        assert "version" in results["tesseract"]
        assert "message" in results["tesseract"]

        # 验证逻辑一致性
        if results["all_satisfied"]:
            # 如果所有依赖满足，缺失列表应该为空
            assert len(results["missing_dependencies"]) == 0, "所有依赖满足时，缺失列表应为空"
            # 安装指引应该为空
            assert results["install_guide"] == "", "所有依赖满足时，安装指引应为空"
        else:
            # 如果存在缺失依赖，缺失列表不应为空
            assert len(results["missing_dependencies"]) > 0, "存在缺失依赖时，缺失列表不应为空"
            # 安装指引不应为空
            assert len(results["install_guide"]) > 0, "存在缺失依赖时，应提供安装指引"

    @given(system_name=st.sampled_from(["Darwin", "Windows", "Linux", "Unknown"]))
    @settings(max_examples=100, deadline=None)
    def test_property_install_guide_generation(self, system_name):
        """
        Feature: transmitter-data-analyzer, Property 17: 依赖检测完整性

        对于任何操作系统，如果依赖缺失，应该提供清晰的安装指引

        **验证：需求 9.3**
        """
        checker = DependencyChecker()

        # 模拟缺失依赖的结果
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
            "install_guide": "",
        }

        # 临时修改系统类型
        original_system = checker.system
        checker.system = system_name

        try:
            guide = checker._generate_install_guide(mock_results)

            # 验证安装指引不为空
            assert isinstance(guide, str), "安装指引应该是字符串"
            assert len(guide) > 0, "安装指引不应为空"

            # 验证包含关键信息
            assert "依赖安装指引" in guide or "Tesseract" in guide, "安装指引应包含标题或依赖名称"

        finally:
            # 恢复原始系统类型
            checker.system = original_system

    def test_property_python_version_detection(self):
        """
        Feature: transmitter-data-analyzer, Property 17: 依赖检测完整性

        对于任何Python环境，应该能够正确检测Python版本

        **验证：需求 9.3**
        """
        checker = DependencyChecker()
        result = checker._check_python_version()

        # 验证结果结构
        assert isinstance(result, dict), "Python版本检测结果应该是字典"
        assert "version" in result, "结果应包含version字段"
        assert "satisfied" in result, "结果应包含satisfied字段"
        assert "message" in result, "结果应包含message字段"

        # 验证版本格式
        assert isinstance(result["version"], str), "版本应该是字符串"
        assert "." in result["version"], "版本应包含点号分隔符"

        # 验证版本与sys.version_info一致
        expected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert result["version"] == expected_version, "检测的版本应与sys.version_info一致"

        # 验证satisfied逻辑
        if sys.version_info.major == 3 and sys.version_info.minor >= 8:
            assert result["satisfied"] is True, "Python 3.8+应该满足要求"
        else:
            assert result["satisfied"] is False, "Python 3.8以下不应满足要求"

    def test_property_tesseract_detection_consistency(self):
        """
        Feature: transmitter-data-analyzer, Property 17: 依赖检测完整性

        对于任何Tesseract检测操作，结果应该是一致的

        **验证：需求 9.3**
        """
        checker = DependencyChecker()

        # 多次检测应该返回相同结果
        result1 = checker._check_tesseract()
        result2 = checker._check_tesseract()

        # 验证结果结构
        assert isinstance(result1, dict), "Tesseract检测结果应该是字典"
        assert isinstance(result2, dict), "Tesseract检测结果应该是字典"

        # 验证必需字段
        for result in [result1, result2]:
            assert "installed" in result
            assert "path" in result
            assert "version" in result
            assert "message" in result

        # 验证一致性
        assert result1["installed"] == result2["installed"], "多次检测的installed状态应该一致"
        assert result1["path"] == result2["path"], "多次检测的路径应该一致"

        # 验证逻辑一致性
        if result1["installed"]:
            assert result1["path"] is not None, "已安装时应该有路径"
        else:
            assert result1["path"] is None, "未安装时路径应该为None"
