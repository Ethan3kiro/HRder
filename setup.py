"""
发射机数据分析器安装配置
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_file = Path(__file__).parent / "README.md"
long_description = (
    readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
)

# 读取requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

setup(
    name="transmitter-data-analyzer",
    version="0.1.0",
    author="Transmitter Data Analyzer Team",
    description="跨平台的发射机数据分析工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/transmitter-data-analyzer",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.82.0",
            "pylint>=2.17.4",
            "black>=23.7.0",
            "mypy>=1.4.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "transmitter-analyzer=src.main:main",
        ],
    },
)
