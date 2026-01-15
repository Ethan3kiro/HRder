#!/usr/bin/env python3
"""
自动安装依赖脚本
支持 Windows, macOS, Linux
"""

import sys
import subprocess
import platform
import shutil
from pathlib import Path


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step, text):
    """打印步骤"""
    print(f"\n[{step}] {text}")


def run_command(command, check=True):
    """运行命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_python_version():
    """检查 Python 版本"""
    print_step("1/5", "检查 Python 版本")
    
    version = sys.version_info
    print(f"  当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("  ✓ Python 版本符合要求 (3.9+)")
        return True
    else:
        print(f"  ✗ Python 版本过低，需要 3.9 或更高版本")
        print(f"  请访问 https://www.python.org/downloads/ 下载最新版本")
        return False


def check_pip():
    """检查 pip 是否可用"""
    print_step("2/5", "检查 pip")
    
    # 尝试不同的 pip 命令
    pip_commands = ['pip3', 'pip']
    
    for cmd in pip_commands:
        success, stdout, stderr = run_command(f"{cmd} --version", check=False)
        if success:
            print(f"  ✓ 找到 pip: {cmd}")
            return cmd
    
    print("  ✗ 未找到 pip")
    print("  请先安装 pip: https://pip.pypa.io/en/stable/installation/")
    return None


def install_requirements(pip_cmd):
    """安装 Python 依赖"""
    print_step("3/5", "安装 Python 依赖")
    
    requirements_files = [
        ('requirements.txt', '核心依赖', True),
        ('requirements-gui.txt', 'GUI 依赖', True),
        ('requirements-training.txt', '训练依赖 (可选)', False),
    ]
    
    all_success = True
    
    for req_file, desc, required in requirements_files:
        if not Path(req_file).exists():
            print(f"  ⚠️  {req_file} 不存在，跳过")
            continue
        
        print(f"\n  安装 {desc} ({req_file})...")
        
        # 使用 --upgrade 确保安装最新版本
        success, stdout, stderr = run_command(
            f"{pip_cmd} install -r {req_file}",
            check=False
        )
        
        if success:
            print(f"  ✓ {desc} 安装成功")
        else:
            if required:
                print(f"  ✗ {desc} 安装失败")
                print(f"  错误信息: {stderr}")
                all_success = False
            else:
                print(f"  ⚠️  {desc} 安装失败（可选依赖，可忽略）")
    
    return all_success


def check_tesseract():
    """检查 Tesseract OCR"""
    print_step("4/5", "检查 Tesseract OCR")
    
    # 检查 tesseract 命令是否可用
    success, stdout, stderr = run_command("tesseract --version", check=False)
    
    if success:
        # 提取版本号
        version_line = stdout.split('\n')[0]
        print(f"  ✓ Tesseract 已安装: {version_line}")
        return True
    else:
        print("  ⚠️  Tesseract OCR 未安装")
        print_tesseract_install_guide()
        return False


def print_tesseract_install_guide():
    """打印 Tesseract 安装指南"""
    system = platform.system()
    
    print("\n  Tesseract OCR 安装指南:")
    
    if system == "Windows":
        print("  1. 访问: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  2. 下载最新版本的安装程序")
        print("  3. 运行安装程序，记住安装路径")
        print("  4. 将安装路径添加到系统 PATH 环境变量")
        print("     默认路径: C:\\Program Files\\Tesseract-OCR")
    
    elif system == "Darwin":  # macOS
        print("  使用 Homebrew 安装:")
        print("  $ brew install tesseract")
    
    elif system == "Linux":
        print("  Ubuntu/Debian:")
        print("  $ sudo apt update")
        print("  $ sudo apt install tesseract-ocr")
        print("\n  CentOS/RHEL:")
        print("  $ sudo yum install tesseract")
    
    print("\n  安装完成后，请重新运行此脚本")


def verify_installation():
    """验证安装"""
    print_step("5/5", "验证安装")
    
    print("\n  正在验证依赖...")
    
    # 运行验证脚本
    if Path("verify_dependencies.py").exists():
        success, stdout, stderr = run_command(
            f"{sys.executable} verify_dependencies.py",
            check=False
        )
        
        if success:
            print("\n" + stdout)
            return True
        else:
            print("\n  验证过程中出现错误:")
            print(stderr)
            return False
    else:
        print("  ⚠️  验证脚本不存在，跳过验证")
        return True


def main():
    """主函数"""
    print_header("发射机数据分析器 - 自动安装依赖")
    
    print(f"\n操作系统: {platform.system()} {platform.release()}")
    print(f"Python 路径: {sys.executable}")
    
    # 1. 检查 Python 版本
    if not check_python_version():
        return 1
    
    # 2. 检查 pip
    pip_cmd = check_pip()
    if not pip_cmd:
        return 1
    
    # 3. 安装 Python 依赖
    if not install_requirements(pip_cmd):
        print("\n⚠️  部分依赖安装失败，但可以继续")
    
    # 4. 检查 Tesseract
    tesseract_ok = check_tesseract()
    
    # 5. 验证安装
    verify_ok = verify_installation()
    
    # 总结
    print_header("安装完成")
    
    if verify_ok:
        print("\n✓ 所有必需依赖已安装")
        
        if not tesseract_ok:
            print("\n⚠️  Tesseract OCR 未安装")
            print("   - 传统 OCR 功能将不可用")
            print("   - 可以使用深度学习模型或手动输入")
            print("   - 如需使用传统 OCR，请按照上述指南安装 Tesseract")
        
        print("\n下一步:")
        print("  1. 启动应用:")
        if platform.system() == "Windows":
            print("     双击 start_gui.bat")
        else:
            print("     运行 ./start_gui.sh")
        
        print("\n  2. 如需训练模型，参考 TRAINING.md")
        
        return 0
    else:
        print("\n✗ 安装过程中出现错误")
        print("\n请检查错误信息，或参考 DEPENDENCIES.md 手动安装")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n用户取消安装")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n安装过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
