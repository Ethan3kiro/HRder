"""
依赖检测模块

检测系统依赖和Python包依赖，提供安装指引
"""
import shutil
import sys
import platform
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from src.config import Config


logger = logging.getLogger("transmitter.dependency")


class DependencyChecker:
    """依赖检测器"""

    # 必需的Python包及其最小版本
    REQUIRED_PACKAGES = {
        "pytesseract": "0.3.0",
        "PIL": "10.0.0",  # Pillow
        "pandas": "2.0.0",
        "numpy": "1.24.0",
        "matplotlib": "3.7.0",
        "plotly": "5.15.0",
        "openpyxl": "3.1.0",
        "xlsxwriter": "3.1.0",
    }

    # Tesseract安装指引
    TESSERACT_INSTALL_GUIDE = {
        "Darwin": (
            "Mac系统安装Tesseract-OCR:\n"
            "1. 使用Homebrew安装:\n"
            "   brew install tesseract\n"
            "2. 或从官网下载安装包:\n"
            "   https://github.com/tesseract-ocr/tesseract/wiki\n"
        ),
        "Windows": (
            "Windows系统安装Tesseract-OCR:\n"
            "1. 下载安装程序:\n"
            "   https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. 运行安装程序，建议安装到默认路径:\n"
            "   C:\\Program Files\\Tesseract-OCR\n"
            "3. 安装完成后，可能需要将Tesseract添加到系统PATH\n"
        ),
        "Linux": (
            "Linux系统安装Tesseract-OCR:\n"
            "1. Ubuntu/Debian:\n"
            "   sudo apt-get update\n"
            "   sudo apt-get install tesseract-ocr\n"
            "2. Fedora/CentOS:\n"
            "   sudo yum install tesseract\n"
            "3. Arch Linux:\n"
            "   sudo pacman -S tesseract\n"
        ),
    }

    # Python包安装指引
    PYTHON_PACKAGES_INSTALL_GUIDE = (
        "安装Python依赖包:\n"
        "1. 确保已安装pip:\n"
        "   python -m pip --version\n"
        "2. 安装所有依赖:\n"
        "   pip install -r requirements.txt\n"
        "3. 或单独安装缺失的包:\n"
        "   pip install <package_name>\n"
    )

    def __init__(self):
        """初始化依赖检测器"""
        self.system = platform.system()
        self.python_version = sys.version_info
        logger.info(
            f"系统: {self.system}, Python版本: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}"
        )

    def check_dependencies(self) -> Dict[str, any]:
        """
        检查所有依赖

        Returns:
            包含检测结果的字典:
            {
                'all_satisfied': bool,  # 所有依赖是否满足
                'python_version': dict,  # Python版本信息
                'tesseract': dict,  # Tesseract检测结果
                'packages': dict,  # Python包检测结果
                'missing_dependencies': list,  # 缺失的依赖列表
                'install_guide': str  # 安装指引
            }
        """
        logger.info("开始检测系统依赖...")

        results = {
            "all_satisfied": True,
            "python_version": self._check_python_version(),
            "tesseract": self._check_tesseract(),
            "packages": self._check_python_packages(),
            "missing_dependencies": [],
            "install_guide": "",
        }

        # 检查Python版本
        if not results["python_version"]["satisfied"]:
            results["all_satisfied"] = False
            results["missing_dependencies"].append("Python 3.8+")

        # 检查Tesseract
        if not results["tesseract"]["installed"]:
            results["all_satisfied"] = False
            results["missing_dependencies"].append("Tesseract-OCR")

        # 检查Python包
        missing_packages = [
            pkg for pkg, info in results["packages"].items() if not info["installed"]
        ]
        if missing_packages:
            results["all_satisfied"] = False
            results["missing_dependencies"].extend(missing_packages)

        # 生成安装指引
        if not results["all_satisfied"]:
            results["install_guide"] = self._generate_install_guide(results)

        logger.info(f"依赖检测完成。所有依赖满足: {results['all_satisfied']}")

        return results

    def _check_python_version(self) -> Dict[str, any]:
        """
        检查Python版本

        Returns:
            Python版本信息字典
        """
        major, minor, micro = self.python_version[:3]
        version_str = f"{major}.{minor}.{micro}"

        # 要求Python 3.8+
        satisfied = major == 3 and minor >= 8

        result = {
            "version": version_str,
            "satisfied": satisfied,
            "message": f"Python {version_str}"
            + (" (满足要求)" if satisfied else " (需要Python 3.8+)"),
        }

        logger.info(result["message"])
        return result

    def _check_tesseract(self) -> Dict[str, any]:
        """
        检查Tesseract-OCR安装

        Returns:
            Tesseract检测结果字典
        """
        result = {"installed": False, "path": None, "version": None, "message": ""}

        # 1. 检查配置的默认路径
        default_path = Config.get_tesseract_path()
        if default_path:
            result["installed"] = True
            result["path"] = default_path
            result["message"] = f"Tesseract已安装 (路径: {default_path})"
            logger.info(result["message"])

            # 尝试获取版本
            try:
                result["version"] = self._get_tesseract_version(default_path)
            except Exception as e:
                logger.warning(f"无法获取Tesseract版本: {e}")

            return result

        # 2. 检查系统PATH
        tesseract_cmd = shutil.which("tesseract")
        if tesseract_cmd:
            result["installed"] = True
            result["path"] = tesseract_cmd
            result["message"] = f"Tesseract已安装 (系统PATH: {tesseract_cmd})"
            logger.info(result["message"])

            # 尝试获取版本
            try:
                result["version"] = self._get_tesseract_version(tesseract_cmd)
            except Exception as e:
                logger.warning(f"无法获取Tesseract版本: {e}")

            return result

        # 3. 未找到Tesseract
        result["message"] = "Tesseract-OCR未安装或无法找到"
        logger.warning(result["message"])

        return result

    def _get_tesseract_version(self, tesseract_path: str) -> Optional[str]:
        """
        获取Tesseract版本

        Args:
            tesseract_path: Tesseract可执行文件路径

        Returns:
            版本字符串，如果无法获取则返回None
        """
        try:
            import subprocess

            result = subprocess.run(
                [tesseract_path, "--version"], capture_output=True, text=True, timeout=5
            )
            # 解析版本信息（通常在第一行）
            if result.stdout:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "tesseract" in line.lower():
                        return line.strip()
            return None
        except Exception as e:
            logger.debug(f"获取Tesseract版本失败: {e}")
            return None

    def _check_python_packages(self) -> Dict[str, Dict[str, any]]:
        """
        检查Python包依赖

        Returns:
            包检测结果字典，键为包名，值为检测信息
        """
        results = {}

        for package_name, min_version in self.REQUIRED_PACKAGES.items():
            result = self._check_single_package(package_name, min_version)
            results[package_name] = result

            if result["installed"]:
                logger.info(f"✓ {package_name} {result['version']} (已安装)")
            else:
                logger.warning(f"✗ {package_name} (未安装)")

        return results

    def _check_single_package(
        self, package_name: str, min_version: str
    ) -> Dict[str, any]:
        """
        检查单个Python包

        Args:
            package_name: 包名
            min_version: 最小版本要求

        Returns:
            包检测结果字典
        """
        result = {
            "installed": False,
            "version": None,
            "min_version": min_version,
            "satisfied": False,
            "message": "",
        }

        # 特殊处理：PIL实际上是Pillow包
        import_name = "PIL" if package_name == "PIL" else package_name

        try:
            # 尝试导入包
            spec = importlib.util.find_spec(import_name)
            if spec is None:
                result["message"] = f"{package_name} 未安装"
                return result

            # 包已安装
            result["installed"] = True

            # 尝试获取版本
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, "__version__", None)

                if version:
                    result["version"] = version
                    # 简单的版本比较（仅比较主版本号和次版本号）
                    result["satisfied"] = self._compare_versions(version, min_version)

                    if result["satisfied"]:
                        result[
                            "message"
                        ] = f"{package_name} {version} (满足要求 >= {min_version})"
                    else:
                        result[
                            "message"
                        ] = f"{package_name} {version} (需要 >= {min_version})"
                else:
                    result["version"] = "未知"
                    result["satisfied"] = True  # 假设满足要求
                    result["message"] = f"{package_name} 已安装 (版本未知)"

            except Exception as e:
                logger.debug(f"获取{package_name}版本失败: {e}")
                result["version"] = "未知"
                result["satisfied"] = True  # 假设满足要求
                result["message"] = f"{package_name} 已安装 (版本未知)"

        except Exception as e:
            logger.debug(f"检查{package_name}失败: {e}")
            result["message"] = f"{package_name} 检测失败: {str(e)}"

        return result

    def _compare_versions(self, current: str, minimum: str) -> bool:
        """
        比较版本号

        Args:
            current: 当前版本
            minimum: 最小版本要求

        Returns:
            当前版本是否满足最小版本要求
        """
        try:
            # 解析版本号（只比较主版本号和次版本号）
            current_parts = [int(x) for x in current.split(".")[:2]]
            minimum_parts = [int(x) for x in minimum.split(".")[:2]]

            # 补齐到相同长度
            while len(current_parts) < 2:
                current_parts.append(0)
            while len(minimum_parts) < 2:
                minimum_parts.append(0)

            return current_parts >= minimum_parts
        except Exception as e:
            logger.debug(f"版本比较失败: {e}")
            return True  # 无法比较时假设满足要求

    def _generate_install_guide(self, results: Dict[str, any]) -> str:
        """
        生成安装指引

        Args:
            results: 依赖检测结果

        Returns:
            安装指引文本
        """
        guide_parts = []

        guide_parts.append("=" * 60)
        guide_parts.append("依赖安装指引")
        guide_parts.append("=" * 60)
        guide_parts.append("")

        # Python版本
        if not results["python_version"]["satisfied"]:
            guide_parts.append("【Python版本】")
            guide_parts.append(f"当前版本: {results['python_version']['version']}")
            guide_parts.append("需要: Python 3.8 或更高版本")
            guide_parts.append("请访问 https://www.python.org/downloads/ 下载安装")
            guide_parts.append("")

        # Tesseract
        if not results["tesseract"]["installed"]:
            guide_parts.append("【Tesseract-OCR】")
            tesseract_guide = self.TESSERACT_INSTALL_GUIDE.get(
                self.system,
                "请访问 https://github.com/tesseract-ocr/tesseract/wiki 查看安装说明",
            )
            guide_parts.append(tesseract_guide)
            guide_parts.append("")

        # Python包
        missing_packages = [
            pkg for pkg, info in results["packages"].items() if not info["installed"]
        ]
        if missing_packages:
            guide_parts.append("【Python依赖包】")
            guide_parts.append(f"缺失的包: {', '.join(missing_packages)}")
            guide_parts.append("")
            guide_parts.append(self.PYTHON_PACKAGES_INSTALL_GUIDE)
            guide_parts.append("")

        guide_parts.append("=" * 60)

        return "\n".join(guide_parts)

    def print_dependency_report(self, results: Dict[str, any]) -> None:
        """
        打印依赖检测报告

        Args:
            results: 依赖检测结果
        """
        print("\n" + "=" * 60)
        print("依赖检测报告")
        print("=" * 60)
        print()

        # Python版本
        print(f"Python版本: {results['python_version']['message']}")
        print()

        # Tesseract
        print(f"Tesseract-OCR: {results['tesseract']['message']}")
        if results["tesseract"]["version"]:
            print(f"  版本: {results['tesseract']['version']}")
        print()

        # Python包
        print("Python依赖包:")
        for package_name, info in results["packages"].items():
            status = "✓" if info["installed"] else "✗"
            print(f"  {status} {package_name}: {info['message']}")
        print()

        # 总结
        if results["all_satisfied"]:
            print("✓ 所有依赖已满足！")
        else:
            print("✗ 存在缺失的依赖:")
            for dep in results["missing_dependencies"]:
                print(f"  - {dep}")
            print()
            print("请查看下方的安装指引:")
            print()
            print(results["install_guide"])

        print("=" * 60)
        print()


def check_dependencies() -> Dict[str, any]:
    """
    检查系统依赖（便捷函数）

    Returns:
        依赖检测结果字典
    """
    checker = DependencyChecker()
    return checker.check_dependencies()


def print_dependency_report() -> bool:
    """
    检查依赖并打印报告（便捷函数）

    Returns:
        所有依赖是否满足
    """
    checker = DependencyChecker()
    results = checker.check_dependencies()
    checker.print_dependency_report(results)
    return results["all_satisfied"]


if __name__ == "__main__":
    # 命令行运行时直接检测并打印报告
    import sys

    all_satisfied = print_dependency_report()
    sys.exit(0 if all_satisfied else 1)
