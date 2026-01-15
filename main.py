#!/usr/bin/env python3
"""
发射机数据分析器 - 主入口文件

这是系统的主入口点，负责：
1. 初始化日志系统
2. 检测系统依赖
3. 解析命令行参数
4. 启动CLI界面
5. 处理顶层异常
"""
import sys
import argparse
from pathlib import Path

from src.config import Config
from src.logging_config import setup_logging
from src.dependency_checker import DependencyChecker
from src.cli import TransmitterCLI
from src.exceptions import TransmitterError


def parse_arguments():
    """
    解析命令行参数

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="发射机数据分析器 - 从截图中提取数据并进行分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                           # 使用默认配置启动
  %(prog)s --db-path /path/to/db     # 指定数据库路径
  %(prog)s --log-level DEBUG         # 设置日志级别为DEBUG
  %(prog)s --version                 # 显示版本信息
  %(prog)s --check-deps              # 仅检查依赖，不启动程序
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {Config.VERSION}",
        help="显示版本信息并退出",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        metavar="PATH",
        help=f"指定数据库文件路径（默认：{Config.get_default_db_path()}）",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="设置日志级别（默认：INFO）",
    )

    parser.add_argument(
        "--log-dir",
        type=str,
        metavar="PATH",
        help=f"指定日志目录路径（默认：{Config.get_default_log_path()}）",
    )

    parser.add_argument("--check-deps", action="store_true", help="检查系统依赖并显示报告，然后退出")

    parser.add_argument("--no-log-file", action="store_true", help="不记录日志到文件，仅输出到控制台")

    return parser.parse_args()


def check_dependencies_and_report():
    """
    检查系统依赖并打印报告

    Returns:
        所有依赖是否满足
    """
    print("\n正在检查系统依赖...")
    print()

    checker = DependencyChecker()
    results = checker.check_dependencies()
    checker.print_dependency_report(results)

    return results["all_satisfied"]


def main():
    """
    主函数

    执行流程：
    1. 解析命令行参数
    2. 初始化日志系统
    3. 检测系统依赖
    4. 启动CLI界面
    5. 处理异常和清理
    """
    # 解析命令行参数
    args = parse_arguments()

    # 如果只是检查依赖，执行检查后退出
    if args.check_deps:
        all_satisfied = check_dependencies_and_report()
        sys.exit(0 if all_satisfied else 1)

    # 初始化日志系统
    try:
        log_dir = Path(args.log_dir) if args.log_dir else None
        logger = setup_logging(
            log_level=args.log_level,
            log_dir=log_dir,
            log_to_file=not args.no_log_file,
            log_to_console=True,
        )
        logger.info("=" * 60)
        logger.info(f"发射机数据分析器 v{Config.VERSION} 启动")
        logger.info("=" * 60)
        logger.info(f"日志级别: {args.log_level}")

        if args.db_path:
            logger.info(f"数据库路径: {args.db_path}")

    except Exception as e:
        print(f"错误：日志系统初始化失败 - {e}")
        sys.exit(1)

    # 检测系统依赖
    try:
        logger.info("开始检测系统依赖...")
        checker = DependencyChecker()
        dep_results = checker.check_dependencies()

        if not dep_results["all_satisfied"]:
            logger.warning("存在缺失的依赖")
            print("\n警告：检测到缺失的依赖")
            print("=" * 60)

            # 显示缺失的依赖
            for dep in dep_results["missing_dependencies"]:
                print(f"  ✗ {dep}")

            print()
            print("提示：")
            print("  - 某些功能可能无法正常使用")
            print("  - 运行 'python main.py --check-deps' 查看详细的安装指引")
            print("  - 或按 Ctrl+C 退出程序，安装依赖后再运行")
            print("=" * 60)

            # 询问是否继续
            try:
                choice = input("\n是否继续运行？(y/n): ").strip().lower()
                if choice != "y":
                    logger.info("用户选择退出")
                    print("程序已退出")
                    sys.exit(0)
            except KeyboardInterrupt:
                print("\n\n程序已退出")
                sys.exit(0)
        else:
            logger.info("所有依赖检测通过")

    except Exception as e:
        logger.exception(f"依赖检测过程发生错误: {e}")
        print(f"\n警告：依赖检测失败 - {e}")
        print("程序将尝试继续运行，但某些功能可能不可用")

    # 如果指定了数据库路径，设置环境变量或传递给CLI
    db_path = None
    if args.db_path:
        db_path = Path(args.db_path)
        logger.info(f"使用自定义数据库路径: {db_path}")

    # 启动CLI界面
    try:
        logger.info("启动命令行界面...")
        cli = TransmitterCLI(db_path=db_path)
        cli.run()

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        print("\n\n程序已中断")
        sys.exit(0)

    except TransmitterError as e:
        logger.error(f"程序运行错误: {e}")
        print(f"\n错误：{e}")
        print("请查看日志文件获取详细信息")
        sys.exit(1)

    except Exception as e:
        logger.exception(f"程序发生未预期的错误: {e}")
        print(f"\n严重错误：程序崩溃 - {e}")
        print("请查看日志文件获取详细信息")
        sys.exit(1)

    finally:
        logger.info("程序正常退出")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
