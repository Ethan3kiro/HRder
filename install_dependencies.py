#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Install Dependencies Script
Supports Windows, macOS, Linux
"""

import sys
import subprocess
import platform
import shutil
from pathlib import Path


def print_header(text):
    """Print header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step, text):
    """Print step"""
    print(f"\n[{step}] {text}")


def run_command(command, check=True):
    """Run command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_python_version():
    """Check Python version"""
    print_step("1/5", "Checking Python version")
    
    version = sys.version_info
    print(f"  Current version: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("  [OK] Python version meets requirements (3.9+)")
        return True
    else:
        print(f"  [ERROR] Python version too old, need 3.9 or higher")
        print(f"  Please visit https://www.python.org/downloads/")
        return False


def check_pip():
    """Check if pip is available"""
    print_step("2/5", "Checking pip")
    
    # Try different pip commands
    pip_commands = ['pip3', 'pip']
    
    for cmd in pip_commands:
        success, stdout, stderr = run_command(f"{cmd} --version", check=False)
        if success:
            print(f"  [OK] Found pip: {cmd}")
            return cmd
    
    print("  [ERROR] pip not found")
    print("  Please install pip: https://pip.pypa.io/en/stable/installation/")
    return None


def install_requirements(pip_cmd):
    """Install Python dependencies"""
    print_step("3/5", "Installing Python dependencies")
    
    requirements_files = [
        ('requirements.txt', 'Core dependencies', True),
        ('requirements-gui.txt', 'GUI dependencies', True),
        ('requirements-training.txt', 'Training dependencies (optional)', False),
    ]
    
    all_success = True
    
    for req_file, desc, required in requirements_files:
        if not Path(req_file).exists():
            print(f"  [WARN] {req_file} not found, skipping")
            continue
        
        print(f"\n  Installing {desc} ({req_file})...")
        
        # Use --upgrade to ensure latest version
        success, stdout, stderr = run_command(
            f"{pip_cmd} install -r {req_file}",
            check=False
        )
        
        if success:
            print(f"  [OK] {desc} installed successfully")
        else:
            if required:
                print(f"  [ERROR] {desc} installation failed")
                print(f"  Error message: {stderr}")
                all_success = False
            else:
                print(f"  [WARN] {desc} installation failed (optional, can be ignored)")
    
    return all_success


def check_tesseract():
    """Check Tesseract OCR"""
    print_step("4/5", "Checking Tesseract OCR")
    
    # Check if tesseract command is available
    success, stdout, stderr = run_command("tesseract --version", check=False)
    
    if success:
        # Extract version
        version_line = stdout.split('\n')[0]
        print(f"  [OK] Tesseract installed: {version_line}")
        return True
    else:
        print("  [WARN] Tesseract OCR not installed")
        print_tesseract_install_guide()
        return False


def print_tesseract_install_guide():
    """Print Tesseract installation guide"""
    system = platform.system()
    
    print("\n  Tesseract OCR Installation Guide:")
    
    if system == "Windows":
        print("  1. Visit: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  2. Download the latest installer")
        print("  3. Run installer, remember installation path")
        print("  4. Add installation path to system PATH")
        print("     Default path: C:\\Program Files\\Tesseract-OCR")
    
    elif system == "Darwin":  # macOS
        print("  Install using Homebrew:")
        print("  $ brew install tesseract")
    
    elif system == "Linux":
        print("  Ubuntu/Debian:")
        print("  $ sudo apt update")
        print("  $ sudo apt install tesseract-ocr")
        print("\n  CentOS/RHEL:")
        print("  $ sudo yum install tesseract")
    
    print("\n  After installation, please run this script again")


def verify_installation():
    """Verify installation"""
    print_step("5/5", "Verifying installation")
    
    print("\n  Verifying dependencies...")
    
    # Run verification script
    if Path("verify_dependencies.py").exists():
        success, stdout, stderr = run_command(
            f"{sys.executable} verify_dependencies.py",
            check=False
        )
        
        if success:
            print("\n" + stdout)
            return True
        else:
            print("\n  Error during verification:")
            print(stderr)
            return False
    else:
        print("  [WARN] Verification script not found, skipping")
        return True


def main():
    """Main function"""
    print_header("Harris Reader - Auto Install Dependencies")
    
    print(f"\nOperating System: {platform.system()} {platform.release()}")
    print(f"Python Path: {sys.executable}")
    
    # 1. Check Python version
    if not check_python_version():
        return 1
    
    # 2. Check pip
    pip_cmd = check_pip()
    if not pip_cmd:
        return 1
    
    # 3. Install Python dependencies
    if not install_requirements(pip_cmd):
        print("\n[WARN] Some dependencies failed to install, but can continue")
    
    # 4. Check Tesseract
    tesseract_ok = check_tesseract()
    
    # 5. Verify installation
    verify_ok = verify_installation()
    
    # Summary
    print_header("Installation Complete")
    
    if verify_ok:
        print("\n[OK] All required dependencies installed")
        
        if not tesseract_ok:
            print("\n[WARN] Tesseract OCR not installed")
            print("   - Traditional OCR features will not be available")
            print("   - You can use deep learning model or manual input")
            print("   - To use traditional OCR, install Tesseract following the guide above")
        
        print("\nNext Steps:")
        print("  1. Start the application:")
        if platform.system() == "Windows":
            print("     Double-click start_gui.bat")
            print("     Or run: py main_gui.py")
        else:
            print("     Run: ./start_gui.sh")
            print("     Or run: python main_gui.py")
        
        print("\n  2. For model training, see TRAINING.md")
        
        return 0
    else:
        print("\n[ERROR] Errors occurred during installation")
        print("\nPlease check error messages, or refer to DEPENDENCIES.md for manual installation")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nException during installation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
