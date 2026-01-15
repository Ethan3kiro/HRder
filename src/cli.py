"""
命令行界面模块

提供用户交互和流程控制功能
"""
import logging
from pathlib import Path
from typing import Optional
import sys

from src.ocr_extractor_v7 import OCRExtractorV7 as OCRExtractor
from src.database import TransmitterDatabase
from src.analyzer import DataAnalyzer
from src.visualizer import DataVisualizer
from src.exporter import DataExporter
from src.device_manager import DeviceManager
from src.settings_manager import SettingsManager
from src.exceptions import (
    TransmitterError,
    OCRError,
    DatabaseError,
    DataValidationError,
    FileError,
)
from src.config import Config
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


class TransmitterCLI:
    """命令行界面"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化CLI和所有模块

        Args:
            db_path: 数据库文件路径（可选，使用默认路径）
        """
        logger.info("初始化命令行界面")

        # 初始化数据库
        try:
            self.database = TransmitterDatabase(db_path=db_path)
            self.database.initialize_database()
            logger.info("数据库初始化成功")
        except DatabaseError as e:
            logger.error(f"数据库初始化失败: {e}")
            print(f"错误：数据库初始化失败 - {e}")
            sys.exit(1)

        # 初始化OCR提取器
        try:
            self.ocr_extractor = OCRExtractor()
            logger.info("OCR提取器初始化成功")
        except OCRError as e:
            logger.error(f"OCR提取器初始化失败: {e}")
            print(f"警告：OCR提取器初始化失败 - {e}")
            print("数据录入功能将不可用")
            self.ocr_extractor = None

        # 初始化分析器
        self.analyzer = DataAnalyzer(self.database)

        # 初始化可视化器
        self.visualizer = DataVisualizer(self.database)

        # 初始化导出器
        self.exporter = DataExporter()

        # 初始化设备管理器
        self.device_manager = DeviceManager(self.database)

        # 初始化设置管理器
        self.settings_manager = SettingsManager(self.database)

        # 当前选择的设备ID
        self.current_device_id = self.settings_manager.get_current_device_id()
        if self.current_device_id is None:
            # 如果没有设置，创建默认设备
            try:
                device_id = self.device_manager.add_device(
                    device_name="默认设备",
                    device_code="DEFAULT-001",
                    description="系统默认设备"
                )
                self.settings_manager.set_current_device_id(device_id)
                self.current_device_id = device_id
                logger.info(f"创建默认设备，ID: {device_id}")
            except DatabaseError:
                # 设备可能已存在
                devices = self.device_manager.get_all_devices()
                if devices:
                    self.current_device_id = devices[0]["id"]
                    self.settings_manager.set_current_device_id(self.current_device_id)
                else:
                    logger.error("无法创建或获取默认设备")
                    self.current_device_id = 1

        # 运行标志
        self.running = True

        logger.info("命令行界面初始化完成")

    def run(self) -> None:
        """运行主循环"""
        logger.info("启动命令行界面主循环")

        print("\n" + "=" * 60)
        print("欢迎使用发射机数据分析器")
        print(f"版本: {Config.VERSION}")
        print("=" * 60 + "\n")

        while self.running:
            try:
                self.show_main_menu()
                choice = input("\n请选择操作 (1-7): ").strip()

                if choice == "1":
                    self.handle_device_management()
                elif choice == "2":
                    self.handle_system_settings()
                elif choice == "3":
                    self.handle_data_entry()
                elif choice == "4":
                    self.handle_comparison()
                elif choice == "5":
                    self.handle_trend_visualization()
                elif choice == "6":
                    self.handle_data_management()
                elif choice == "7":
                    print("\n感谢使用，再见！")
                    self.running = False
                else:
                    print("\n错误：无效的选项，请输入1-7之间的数字")
                    logger.warning(f"用户输入无效选项: {choice}")

            except KeyboardInterrupt:
                print("\n\n检测到中断信号，正在退出...")
                self.running = False
            except Exception as e:
                logger.exception(f"主循环发生未预期的错误: {e}")
                print(f"\n错误：发生未预期的错误 - {e}")
                print("请查看日志文件获取详细信息")

        # 清理资源
        self.database.close()
        logger.info("命令行界面已退出")

    def _validate_menu_choice(
        self, choice: str, min_val: int, max_val: int
    ) -> Optional[int]:
        """
        验证菜单选项输入

        Args:
            choice: 用户输入的选项
            min_val: 最小有效值
            max_val: 最大有效值

        Returns:
            有效的整数选项，如果无效则返回None
        """
        try:
            choice_int = int(choice)
            if min_val <= choice_int <= max_val:
                return choice_int
            else:
                print(f"错误：请输入{min_val}-{max_val}之间的数字")
                return None
        except ValueError:
            print("错误：请输入有效的数字")
            return None

    def _validate_yes_no(self, input_str: str) -> Optional[bool]:
        """
        验证是/否输入

        Args:
            input_str: 用户输入

        Returns:
            True表示是，False表示否，None表示无效输入
        """
        input_lower = input_str.strip().lower()
        if input_lower in ["y", "yes", "是"]:
            return True
        elif input_lower in ["n", "no", "否"]:
            return False
        else:
            print("错误：请输入 y 或 n")
            return None

    def _safe_float_input(self, prompt: str) -> Optional[float]:
        """
        安全地获取浮点数输入

        Args:
            prompt: 提示信息

        Returns:
            浮点数值，如果输入无效则返回None
        """
        try:
            value = float(input(prompt).strip())
            return value
        except ValueError:
            print("错误：请输入有效的数值")
            return None

    def show_main_menu(self) -> None:
        """显示主菜单"""
        # 获取当前设备信息
        current_device = self.device_manager.get_device_by_id(self.current_device_id)
        device_name = current_device["device_name"] if current_device else "未知设备"
        
        print("\n" + "-" * 60)
        print("主菜单")
        print(f"当前设备: {device_name} (ID: {self.current_device_id})")
        print("-" * 60)
        print("1. 设备管理")
        print("2. 系统设置")
        print("3. 录入数据")
        print("4. 两月对比")
        print("5. 绘制趋势")
        print("6. 数据管理")
        print("7. 退出")
        print("-" * 60)

    def handle_device_management(self) -> None:
        """处理设备管理流程"""
        logger.info("进入设备管理流程")

        while True:
            print("\n" + "=" * 60)
            print("设备管理")
            print("=" * 60)
            print("1. 查看所有设备")
            print("2. 添加新设备")
            print("3. 切换当前设备")
            print("4. 编辑设备信息")
            print("5. 删除设备")
            print("6. 返回主菜单")
            print("-" * 60)

            choice = input("\n请选择操作 (1-6): ").strip()

            if choice == "1":
                self._list_all_devices()
            elif choice == "2":
                self._add_new_device()
            elif choice == "3":
                self._switch_device()
            elif choice == "4":
                self._edit_device()
            elif choice == "5":
                self._delete_device()
            elif choice == "6":
                print("返回主菜单")
                break
            else:
                print("错误：无效的选项，请输入1-6之间的数字")

    def _list_all_devices(self) -> None:
        """列出所有设备"""
        devices = self.device_manager.get_all_devices()
        
        if not devices:
            print("\n当前没有设备")
            return
        
        print("\n所有设备列表：")
        print("=" * 80)
        for device in devices:
            current_mark = " [当前]" if device["id"] == self.current_device_id else ""
            print(f"ID: {device['id']}{current_mark}")
            print(f"  名称: {device['device_name']}")
            print(f"  编号: {device['device_code']}")
            print(f"  描述: {device['description']}")
            print(f"  创建时间: {device['create_time']}")
            
            # 获取设备数据统计
            stats = self.device_manager.get_device_data_stats(device["id"])
            print(f"  数据记录: {stats['total_records']} 条")
            print(f"  月份数: {stats['month_count']} 个")
            print("-" * 80)

    def _add_new_device(self) -> None:
        """添加新设备"""
        print("\n添加新设备")
        print("-" * 60)
        
        device_name = input("请输入设备名称: ").strip()
        if not device_name:
            print("错误：设备名称不能为空")
            return
        
        device_code = input("请输入设备编号（可选）: ").strip()
        description = input("请输入设备描述（可选）: ").strip()
        
        try:
            device_id = self.device_manager.add_device(
                device_name=device_name,
                device_code=device_code if device_code else None,
                description=description if description else None
            )
            print(f"\n成功添加设备，ID: {device_id}")
            logger.info(f"添加新设备: {device_name}, ID: {device_id}")
            
            # 询问是否切换到新设备
            switch = input("\n是否切换到新设备？(y/n): ").strip().lower()
            if switch == "y":
                self.current_device_id = device_id
                self.settings_manager.set_current_device_id(device_id)
                print(f"已切换到设备: {device_name}")
        
        except DatabaseError as e:
            logger.error(f"添加设备失败: {e}")
            print(f"\n错误：添加设备失败 - {e}")

    def _switch_device(self) -> None:
        """切换当前设备"""
        devices = self.device_manager.get_all_devices()
        
        if not devices:
            print("\n当前没有设备")
            return
        
        print("\n可用设备列表：")
        print("-" * 60)
        for idx, device in enumerate(devices, start=1):
            current_mark = " [当前]" if device["id"] == self.current_device_id else ""
            print(f"{idx}. {device['device_name']} (ID: {device['id']}){current_mark}")
        print("-" * 60)
        
        choice = input("\n请选择设备（输入序号或输入'q'返回）: ").strip()
        
        if choice.lower() == "q":
            return
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(devices):
                device = devices[idx - 1]
                self.current_device_id = device["id"]
                self.settings_manager.set_current_device_id(device["id"])
                print(f"\n已切换到设备: {device['device_name']}")
                logger.info(f"切换到设备: {device['device_name']}, ID: {device['id']}")
            else:
                print(f"错误：请输入1-{len(devices)}之间的数字")
        except ValueError:
            print("错误：请输入有效的数字")

    def _edit_device(self) -> None:
        """编辑设备信息"""
        devices = self.device_manager.get_all_devices()
        
        if not devices:
            print("\n当前没有设备")
            return
        
        print("\n选择要编辑的设备：")
        print("-" * 60)
        for idx, device in enumerate(devices, start=1):
            print(f"{idx}. {device['device_name']} (ID: {device['id']})")
        print("-" * 60)
        
        choice = input("\n请选择设备（输入序号或输入'q'返回）: ").strip()
        
        if choice.lower() == "q":
            return
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(devices):
                device = devices[idx - 1]
                
                print(f"\n编辑设备: {device['device_name']}")
                print("（留空表示不修改）")
                
                new_name = input(f"新名称 [{device['device_name']}]: ").strip()
                new_code = input(f"新编号 [{device['device_code']}]: ").strip()
                new_desc = input(f"新描述 [{device['description']}]: ").strip()
                
                self.device_manager.update_device(
                    device_id=device["id"],
                    device_name=new_name if new_name else device['device_name'],
                    device_code=new_code if new_code else device['device_code'],
                    description=new_desc if new_desc else device['description']
                )
                
                print("\n设备信息已更新")
                logger.info(f"更新设备信息: ID {device['id']}")
            else:
                print(f"错误：请输入1-{len(devices)}之间的数字")
        except ValueError:
            print("错误：请输入有效的数字")
        except DatabaseError as e:
            logger.error(f"更新设备失败: {e}")
            print(f"\n错误：更新设备失败 - {e}")

    def _delete_device(self) -> None:
        """删除设备"""
        devices = self.device_manager.get_all_devices()
        
        if not devices:
            print("\n当前没有设备")
            return
        
        if len(devices) == 1:
            print("\n错误：不能删除最后一个设备")
            return
        
        print("\n选择要删除的设备：")
        print("-" * 60)
        for idx, device in enumerate(devices, start=1):
            print(f"{idx}. {device['device_name']} (ID: {device['id']})")
        print("-" * 60)
        
        choice = input("\n请选择设备（输入序号或输入'q'返回）: ").strip()
        
        if choice.lower() == "q":
            return
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(devices):
                device = devices[idx - 1]
                
                # 获取设备数据统计
                stats = self.device_manager.get_device_data_stats(device["id"])
                
                print(f"\n警告：即将删除设备 '{device['device_name']}'")
                print(f"该设备有 {stats['total_records']} 条数据记录")
                print("删除设备将同时删除其所有数据，此操作不可恢复！")
                
                confirm = input("\n确认删除？请输入设备名称以确认: ").strip()
                
                if confirm == device['device_name']:
                    deleted_count = self.device_manager.delete_device(device["id"], confirm=True)
                    print(f"\n已删除设备及其 {deleted_count} 条数据记录")
                    logger.info(f"删除设备: {device['device_name']}, ID: {device['id']}")
                    
                    # 如果删除的是当前设备，切换到第一个可用设备
                    if device["id"] == self.current_device_id:
                        remaining_devices = self.device_manager.get_all_devices()
                        if remaining_devices:
                            self.current_device_id = remaining_devices[0]["id"]
                            self.settings_manager.set_current_device_id(self.current_device_id)
                            print(f"已自动切换到设备: {remaining_devices[0]['device_name']}")
                else:
                    print("设备名称不匹配，取消删除")
            else:
                print(f"错误：请输入1-{len(devices)}之间的数字")
        except ValueError:
            print("错误：请输入有效的数字")
        except DatabaseError as e:
            logger.error(f"删除设备失败: {e}")
            print(f"\n错误：删除设备失败 - {e}")

    def handle_system_settings(self) -> None:
        """处理系统设置流程"""
        logger.info("进入系统设置流程")

        while True:
            print("\n" + "=" * 60)
            print("系统设置")
            print("=" * 60)
            
            # 显示当前设置
            threshold = self.settings_manager.get_sensitivity_threshold()
            print(f"当前灵敏度阈值: {threshold}%")
            print("-" * 60)
            print("1. 设置灵敏度阈值")
            print("2. 查看所有设置")
            print("3. 返回主菜单")
            print("-" * 60)

            choice = input("\n请选择操作 (1-3): ").strip()

            if choice == "1":
                self._set_sensitivity_threshold()
            elif choice == "2":
                self._view_all_settings()
            elif choice == "3":
                print("返回主菜单")
                break
            else:
                print("错误：无效的选项，请输入1-3之间的数字")

    def _set_sensitivity_threshold(self) -> None:
        """设置灵敏度阈值"""
        current_threshold = self.settings_manager.get_sensitivity_threshold()
        print(f"\n当前灵敏度阈值: {current_threshold}%")
        print("说明：只有变化超过此阈值的数据项才会被标记为显著变化")
        
        try:
            new_threshold = float(input("\n请输入新的阈值（百分比，如10表示10%）: ").strip())
            
            if new_threshold < 0:
                print("错误：阈值不能为负数")
                return
            
            if new_threshold > 100:
                print("警告：阈值大于100%，这可能会导致很少有变化被标记")
            
            self.settings_manager.set_sensitivity_threshold(new_threshold)
            print(f"\n灵敏度阈值已设置为: {new_threshold}%")
            logger.info(f"灵敏度阈值已更新: {new_threshold}%")
        
        except ValueError:
            print("错误：请输入有效的数值")

    def _view_all_settings(self) -> None:
        """查看所有设置"""
        all_settings = self.settings_manager.get_all_settings()
        
        print("\n所有系统设置：")
        print("=" * 80)
        for key, value in all_settings.items():
            print(f"{key}: {value}")
        print("=" * 80)

    def handle_data_entry(self) -> None:
        """
        处理数据录入流程

        提示用户输入截图路径和月份，然后执行数据提取和存储流程
        """
        logger.info("进入数据录入流程")

        # 检查OCR提取器是否可用
        if self.ocr_extractor is None:
            print("\n错误：OCR提取器不可用，无法录入数据")
            print("请确保Tesseract-OCR已正确安装")
            return

        print("\n" + "=" * 60)
        print("数据录入")
        # 显示当前设备
        current_device = self.device_manager.get_device_by_id(self.current_device_id)
        device_name = current_device["device_name"] if current_device else "未知设备"
        print(f"当前设备: {device_name}")
        print("=" * 60)

        # 获取截图文件路径
        while True:
            image_path_str = input("\n请输入截图文件路径（或输入'q'返回主菜单）: ").strip()

            if image_path_str.lower() == "q":
                print("返回主菜单")
                return

            image_path = Path(image_path_str)

            # 验证文件存在
            if not image_path.exists():
                print(f"错误：文件不存在 - {image_path}")
                continue

            # 验证文件格式
            if not Config.is_supported_image(image_path):
                print(f"错误：不支持的图像格式 - {image_path.suffix}")
                print(f"支持的格式: {', '.join(Config.SUPPORTED_IMAGE_FORMATS)}")
                continue

            break

        # 获取月份
        while True:
            month = input("\n请输入月份（格式：YYYY-MM，如2026-01）: ").strip()

            # 验证月份格式
            if not self.database._validate_month_format(month):
                print("错误：月份格式不正确，应为YYYY-MM格式")
                continue

            break

        # 检查是否已存在该月份的数据
        existing_data = self.database.query_by_month(month, device_id=self.current_device_id)
        overwrite = False

        if not existing_data.empty:
            print(f"\n警告：月份 {month} 已存在 {len(existing_data)} 条数据")
            while True:
                choice = input("是否覆盖现有数据？(y/n): ").strip().lower()
                if choice == "y":
                    overwrite = True
                    break
                elif choice == "n":
                    print("取消录入，返回主菜单")
                    return
                else:
                    print("请输入 y 或 n")

        # 执行OCR提取
        print(f"\n正在提取图像数据...")
        try:
            extracted_data = self.ocr_extractor.extract_from_image(image_path)

            if extracted_data.empty:
                print("警告：未能从图像中提取到任何数据")
                print("请检查图像质量或尝试其他图像")
                return

            print(f"成功提取 {len(extracted_data)} 条数据")

            # 显示提取结果摘要
            print("\n提取结果摘要：")
            print("-" * 60)
            for idx, row in extracted_data.iterrows():
                print(f"  {row['item_name']}: {row['value']} {row['unit']}")
            print("-" * 60)

            # 确认是否保存
            while True:
                choice = input("\n是否保存这些数据到数据库？(y/n): ").strip().lower()
                if choice == "y":
                    break
                elif choice == "n":
                    print("取消保存，返回主菜单")
                    return
                else:
                    print("请输入 y 或 n")

            # 保存到数据库
            self.database.insert_monthly_data(
                month, extracted_data, overwrite=overwrite, device_id=self.current_device_id
            )
            print(f"\n成功保存 {len(extracted_data)} 条数据到月份 {month}")
            logger.info(f"成功录入月份 {month} 的数据，共 {len(extracted_data)} 条")

        except OCRError as e:
            logger.error(f"OCR提取失败: {e}")
            print(f"\n错误：OCR提取失败 - {e}")
        except DatabaseError as e:
            logger.error(f"数据库保存失败: {e}")
            print(f"\n错误：数据库保存失败 - {e}")
        except Exception as e:
            logger.exception(f"数据录入过程发生错误: {e}")
            print(f"\n错误：数据录入失败 - {e}")

    def handle_comparison(self) -> None:
        """
        处理两月对比流程

        显示可用月份列表，提示用户选择两个月份，然后生成对比报告
        """
        logger.info("进入两月对比流程")

        print("\n" + "=" * 60)
        print("两月对比")
        # 显示当前设备
        current_device = self.device_manager.get_device_by_id(self.current_device_id)
        device_name = current_device["device_name"] if current_device else "未知设备"
        print(f"当前设备: {device_name}")
        print("=" * 60)

        # 获取可用月份列表
        try:
            available_months = self.database.get_available_months(device_id=self.current_device_id)
        except DatabaseError as e:
            logger.error(f"获取可用月份失败: {e}")
            print(f"\n错误：无法获取可用月份 - {e}")
            return

        if len(available_months) < 2:
            print("\n错误：数据库中至少需要两个月份的数据才能进行对比")
            print(f"当前可用月份数: {len(available_months)}")
            return

        # 显示可用月份
        print("\n可用月份列表：")
        print("-" * 60)
        for idx, month in enumerate(available_months, start=1):
            print(f"  {idx}. {month}")
        print("-" * 60)

        # 选择第一个月份
        while True:
            choice1 = input("\n请选择第一个月份（输入序号或输入'q'返回）: ").strip()

            if choice1.lower() == "q":
                print("返回主菜单")
                return

            try:
                idx1 = int(choice1)
                if 1 <= idx1 <= len(available_months):
                    month1 = available_months[idx1 - 1]
                    break
                else:
                    print(f"错误：请输入1-{len(available_months)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")

        # 选择第二个月份
        while True:
            choice2 = input(f"请选择第二个月份（输入序号，不能与第一个月份相同）: ").strip()

            try:
                idx2 = int(choice2)
                if 1 <= idx2 <= len(available_months):
                    if idx2 == idx1:
                        print("错误：不能选择相同的月份")
                        continue
                    month2 = available_months[idx2 - 1]
                    break
                else:
                    print(f"错误：请输入1-{len(available_months)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")

        # 确保month1是较早的月份
        if month1 > month2:
            month1, month2 = month2, month1

        # 获取灵敏度阈值
        sensitivity_threshold = self.settings_manager.get_sensitivity_threshold()
        print(f"\n使用灵敏度阈值: {sensitivity_threshold}%")
        print(f"正在对比月份 {month1} 和 {month2}...")

        try:
            # 执行对比（使用灵敏度阈值）
            comparison_result = self.analyzer.compare_two_months(
                month1, month2, 
                device_id=self.current_device_id,
                sensitivity_threshold=sensitivity_threshold
            )

            # 显示对比结果
            print("\n对比结果：")
            print("=" * 80)

            # 统计显著变化
            if 'significant_change' in comparison_result.columns:
                significant_count = comparison_result['significant_change'].sum()
                print(f"显著变化（>{sensitivity_threshold}%）: {significant_count} 项")
                print("=" * 80)

            # 分类显示结果
            increased = comparison_result[
                comparison_result["change_status"] == "increase"
            ]
            decreased = comparison_result[
                comparison_result["change_status"] == "decrease"
            ]
            no_change = comparison_result[
                comparison_result["change_status"] == "no_change"
            ]
            missing = comparison_result[comparison_result["change_status"] == "missing"]

            if not increased.empty:
                print(f"\n增长项 ({len(increased)} 项)：")
                print("-" * 80)
                for _, row in increased.iterrows():
                    # 标记显著变化
                    significant_mark = " ⚠️ [显著]" if row.get('significant_change', False) else ""
                    print(
                        f"  {row['item_name']}: {row['value_month1']:.2f} → {row['value_month2']:.2f} "
                        f"({row['absolute_change']:+.2f}, {row['relative_change']:+.1f}%){significant_mark}"
                    )

            if not decreased.empty:
                print(f"\n下降项 ({len(decreased)} 项)：")
                print("-" * 80)
                for _, row in decreased.iterrows():
                    # 标记显著变化
                    significant_mark = " ⚠️ [显著]" if row.get('significant_change', False) else ""
                    print(
                        f"  {row['item_name']}: {row['value_month1']:.2f} → {row['value_month2']:.2f} "
                        f"({row['absolute_change']:+.2f}, {row['relative_change']:+.1f}%){significant_mark}"
                    )

            if not no_change.empty:
                print(f"\n无变化项 ({len(no_change)} 项)：")
                print("-" * 80)
                for _, row in no_change.iterrows():
                    print(f"  {row['item_name']}: {row['value_month1']:.2f}")

            if not missing.empty:
                print(f"\n缺失项 ({len(missing)} 项)：")
                print("-" * 80)
                for _, row in missing.iterrows():
                    missing_in = row["missing_in"]
                    print(f"  {row['item_name']}: 在 {missing_in} 中缺失")

            print("=" * 80)

            # 询问是否导出或生成图表
            print("\n后续操作：")
            print("1. 导出对比报告（Excel）")
            print("2. 生成对比图表（PNG）")
            print("3. 两者都生成")
            print("4. 返回主菜单")

            while True:
                choice = input("\n请选择操作 (1-4): ").strip()

                if choice == "1":
                    self._export_comparison_report(comparison_result, month1, month2)
                    break
                elif choice == "2":
                    self._generate_comparison_chart(comparison_result, month1, month2)
                    break
                elif choice == "3":
                    self._export_comparison_report(comparison_result, month1, month2)
                    self._generate_comparison_chart(comparison_result, month1, month2)
                    break
                elif choice == "4":
                    print("返回主菜单")
                    break
                else:
                    print("错误：请输入1-4之间的数字")

        except DataValidationError as e:
            logger.error(f"数据验证失败: {e}")
            print(f"\n错误：{e}")
        except Exception as e:
            logger.exception(f"对比过程发生错误: {e}")
            print(f"\n错误：对比失败 - {e}")

    def _export_comparison_report(
        self, comparison_df, month1: str, month2: str
    ) -> None:
        """导出对比报告"""
        try:
            # 生成默认文件名
            default_filename = f"comparison_{month1}_vs_{month2}.xlsx"
            output_path_str = input(f"\n请输入输出文件路径（默认：{default_filename}）: ").strip()

            if not output_path_str:
                output_path = Path(default_filename)
            else:
                output_path = Path(output_path_str)

            # 确保文件扩展名为.xlsx
            if output_path.suffix.lower() != ".xlsx":
                output_path = output_path.with_suffix(".xlsx")

            self.exporter.export_comparison_report(comparison_df, output_path)
            print(f"对比报告已导出到: {output_path.absolute()}")
            logger.info(f"对比报告已导出: {output_path}")

        except FileError as e:
            logger.error(f"导出报告失败: {e}")
            print(f"错误：导出失败 - {e}")

    def _generate_comparison_chart(
        self, comparison_df, month1: str, month2: str
    ) -> None:
        """生成对比图表"""
        try:
            # 生成默认文件名
            default_filename = f"comparison_{month1}_vs_{month2}.png"
            output_path_str = input(f"\n请输入输出文件路径（默认：{default_filename}）: ").strip()

            if not output_path_str:
                output_path = Path(default_filename)
            else:
                output_path = Path(output_path_str)

            # 确保文件扩展名为.png
            if output_path.suffix.lower() not in [".png", ".pdf", ".jpg"]:
                output_path = output_path.with_suffix(".png")

            self.visualizer.plot_comparison_chart(comparison_df, output_path)
            print(f"对比图表已生成: {output_path.absolute()}")
            logger.info(f"对比图表已生成: {output_path}")

        except (DataValidationError, FileError) as e:
            logger.error(f"生成图表失败: {e}")
            print(f"错误：生成图表失败 - {e}")

    def handle_trend_visualization(self) -> None:
        """
        处理趋势可视化流程

        显示可用数据项列表，提示用户选择数据项和时间范围，然后生成趋势图表
        """
        logger.info("进入趋势可视化流程")

        print("\n" + "=" * 60)
        print("趋势可视化")
        # 显示当前设备
        current_device = self.device_manager.get_device_by_id(self.current_device_id)
        device_name = current_device["device_name"] if current_device else "未知设备"
        print(f"当前设备: {device_name}")
        print("=" * 60)

        # 获取所有数据项
        all_items = self.database.get_all_items(device_id=self.current_device_id)

        if not all_items:
            print("\n错误：数据库中没有数据项")
            return

        # 显示可用数据项
        print("\n可用数据项列表：")
        print("-" * 60)
        for idx, item in enumerate(all_items, start=1):
            print(f"  {idx}. {item}")
        print("-" * 60)

        # 选择数据项（支持多选）
        print("\n提示：可以选择多个数据项（用逗号分隔，如：1,3,5）")
        while True:
            choice_str = input("请选择数据项（输入序号或输入'q'返回）: ").strip()

            if choice_str.lower() == "q":
                print("返回主菜单")
                return

            try:
                # 解析选择
                choices = [int(c.strip()) for c in choice_str.split(",")]

                # 验证所有选择都有效
                if all(1 <= c <= len(all_items) for c in choices):
                    selected_items = [all_items[c - 1] for c in choices]
                    break
                else:
                    print(f"错误：请输入1-{len(all_items)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字（用逗号分隔）")

        print(f"\n已选择 {len(selected_items)} 个数据项")

        # 获取可用月份（用于时间范围选择）
        available_months = self.database.get_available_months(device_id=self.current_device_id)

        if not available_months:
            print("\n错误：数据库中没有月份数据")
            return

        print(f"\n可用月份范围: {available_months[0]} 至 {available_months[-1]}")

        # 选择时间范围（可选）
        start_month = None
        end_month = None

        use_range = input("\n是否指定时间范围？(y/n，默认n): ").strip().lower()

        if use_range == "y":
            # 选择起始月份
            while True:
                start_input = input(f"请输入起始月份（格式：YYYY-MM，留空表示从最早开始）: ").strip()

                if not start_input:
                    start_month = None
                    break

                if self.database._validate_month_format(start_input):
                    if start_input in available_months:
                        start_month = start_input
                        break
                    else:
                        print(f"警告：月份 {start_input} 不在可用范围内，将使用该月份作为起始")
                        start_month = start_input
                        break
                else:
                    print("错误：月份格式不正确，应为YYYY-MM格式")

            # 选择结束月份
            while True:
                end_input = input(f"请输入结束月份（格式：YYYY-MM，留空表示到最晚结束）: ").strip()

                if not end_input:
                    end_month = None
                    break

                if self.database._validate_month_format(end_input):
                    if end_input in available_months:
                        end_month = end_input
                        break
                    else:
                        print(f"警告：月份 {end_input} 不在可用范围内，将使用该月份作为结束")
                        end_month = end_input
                        break
                else:
                    print("错误：月份格式不正确，应为YYYY-MM格式")

        # 询问是否设置阈值线
        threshold = None
        use_threshold = input("\n是否设置阈值线？(y/n，默认n): ").strip().lower()

        if use_threshold == "y":
            while True:
                threshold_input = input("请输入阈值（数值）: ").strip()
                try:
                    threshold = float(threshold_input)
                    break
                except ValueError:
                    print("错误：请输入有效的数值")

        # 生成趋势图
        print("\n正在生成趋势图...")

        try:
            # 生成默认文件名
            item_names_str = "_".join(selected_items[:3])  # 最多使用前3个项目名
            if len(item_names_str) > 30:
                item_names_str = item_names_str[:30]
            default_filename = f"trend_{item_names_str}.png"

            output_path_str = input(f"\n请输入输出文件路径（默认：{default_filename}）: ").strip()

            if not output_path_str:
                output_path = Path(default_filename)
            else:
                output_path = Path(output_path_str)

            # 确保文件扩展名
            if output_path.suffix.lower() not in [".png", ".pdf", ".jpg", ".html"]:
                output_path = output_path.with_suffix(".png")

            # 询问是否使用交互式图表
            interactive = False
            if output_path.suffix.lower() == ".html":
                interactive = True
            else:
                use_interactive = (
                    input("\n是否生成交互式图表（需要plotly）？(y/n，默认n): ").strip().lower()
                )
                if use_interactive == "y":
                    interactive = True

            self.visualizer.plot_trend_chart(
                item_names=selected_items,
                start_month=start_month,
                end_month=end_month,
                threshold=threshold,
                output_path=output_path,
                interactive=interactive,
            )

            print(f"趋势图表已生成: {output_path.absolute()}")
            logger.info(f"趋势图表已生成: {output_path}")

        except (DataValidationError, FileError) as e:
            logger.error(f"生成趋势图失败: {e}")
            print(f"错误：生成趋势图失败 - {e}")
        except Exception as e:
            logger.exception(f"趋势可视化过程发生错误: {e}")
            print(f"错误：趋势可视化失败 - {e}")

    def handle_data_management(self) -> None:
        """
        处理数据管理流程

        实现数据管理子菜单，包含查询、删除、导出功能
        """
        logger.info("进入数据管理流程")

        while True:
            print("\n" + "=" * 60)
            print("数据管理")
            print("=" * 60)
            print("1. 查询月度数据")
            print("2. 查询数据项历史")
            print("3. 删除月度数据")
            print("4. 导出数据")
            print("5. 返回主菜单")
            print("-" * 60)

            choice = input("\n请选择操作 (1-5): ").strip()

            if choice == "1":
                self._query_monthly_data()
            elif choice == "2":
                self._query_item_history()
            elif choice == "3":
                self._delete_monthly_data()
            elif choice == "4":
                self._export_data()
            elif choice == "5":
                print("返回主菜单")
                break
            else:
                print("错误：无效的选项，请输入1-5之间的数字")
                logger.warning(f"用户输入无效选项: {choice}")

    def _query_monthly_data(self) -> None:
        """查询月度数据"""
        print("\n" + "-" * 60)
        print("查询月度数据")
        print("-" * 60)

        # 获取可用月份
        available_months = self.database.get_available_months()

        if not available_months:
            print("\n数据库中没有数据")
            return

        print("\n可用月份列表：")
        for idx, month in enumerate(available_months, start=1):
            print(f"  {idx}. {month}")

        # 选择月份
        while True:
            choice = input("\n请选择月份（输入序号或输入'q'返回）: ").strip()

            if choice.lower() == "q":
                return

            try:
                idx = int(choice)
                if 1 <= idx <= len(available_months):
                    month = available_months[idx - 1]
                    break
                else:
                    print(f"错误：请输入1-{len(available_months)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")

        # 查询数据
        try:
            data = self.database.query_by_month(month, device_id=self.current_device_id)

            if data.empty:
                print(f"\n月份 {month} 没有数据")
                return

            print(f"\n月份 {month} 的数据（共 {len(data)} 条）：")
            print("=" * 80)
            for _, row in data.iterrows():
                print(f"  {row['item_name']}: {row['value']} {row['unit']}")
            print("=" * 80)

        except DatabaseError as e:
            logger.error(f"查询失败: {e}")
            print(f"错误：查询失败 - {e}")

    def _query_item_history(self) -> None:
        """查询数据项历史"""
        print("\n" + "-" * 60)
        print("查询数据项历史")
        print("-" * 60)

        # 获取所有数据项
        all_items = self.database.get_all_items(device_id=self.current_device_id)

        if not all_items:
            print("\n数据库中没有数据项")
            return

        print("\n可用数据项列表：")
        for idx, item in enumerate(all_items, start=1):
            print(f"  {idx}. {item}")

        # 选择数据项
        while True:
            choice = input("\n请选择数据项（输入序号或输入'q'返回）: ").strip()

            if choice.lower() == "q":
                return

            try:
                idx = int(choice)
                if 1 <= idx <= len(all_items):
                    item_name = all_items[idx - 1]
                    break
                else:
                    print(f"错误：请输入1-{len(all_items)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")

        # 查询历史数据
        try:
            data = self.database.query_by_item(item_name, device_id=self.current_device_id)

            if data.empty:
                print(f"\n数据项 {item_name} 没有历史记录")
                return

            print(f"\n数据项 {item_name} 的历史记录（共 {len(data)} 条）：")
            print("=" * 80)
            for _, row in data.iterrows():
                print(f"  {row['month']}: {row['value']} {row['unit']}")
            print("=" * 80)

            # 显示统计信息
            try:
                stats = self.analyzer.calculate_statistics(item_name, device_id=self.current_device_id)
                print(f"\n统计信息：")
                print(f"  平均值: {stats['mean']:.2f}")
                print(f"  标准差: {stats['std']:.2f}")
                print(f"  最小值: {stats['min']:.2f}")
                print(f"  最大值: {stats['max']:.2f}")
                print(f"  中位数: {stats['median']:.2f}")
            except Exception as e:
                logger.warning(f"计算统计信息失败: {e}")

        except DatabaseError as e:
            logger.error(f"查询失败: {e}")
            print(f"错误：查询失败 - {e}")

    def _delete_monthly_data(self) -> None:
        """删除月度数据"""
        print("\n" + "-" * 60)
        print("删除月度数据")
        print("-" * 60)

        # 获取可用月份
        available_months = self.database.get_available_months()

        if not available_months:
            print("\n数据库中没有数据")
            return

        print("\n可用月份列表：")
        for idx, month in enumerate(available_months, start=1):
            print(f"  {idx}. {month}")

        # 选择月份
        while True:
            choice = input("\n请选择要删除的月份（输入序号或输入'q'返回）: ").strip()

            if choice.lower() == "q":
                return

            try:
                idx = int(choice)
                if 1 <= idx <= len(available_months):
                    month = available_months[idx - 1]
                    break
                else:
                    print(f"错误：请输入1-{len(available_months)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")

        # 确认删除
        print(f"\n警告：即将删除月份 {month} 的所有数据")
        while True:
            confirm = input("确认删除？(y/n): ").strip().lower()
            if confirm == "y":
                break
            elif confirm == "n":
                print("取消删除")
                return
            else:
                print("请输入 y 或 n")

        # 执行删除
        try:
            deleted_count = self.database.delete_month(month, device_id=self.current_device_id)
            print(f"\n成功删除月份 {month} 的 {deleted_count} 条数据")
            logger.info(f"删除月份 {month} 的数据，共 {deleted_count} 条")

        except DatabaseError as e:
            logger.error(f"删除失败: {e}")
            print(f"错误：删除失败 - {e}")

    def _export_data(self) -> None:
        """导出数据"""
        print("\n" + "-" * 60)
        print("导出数据")
        print("-" * 60)
        print("1. 导出指定月份数据")
        print("2. 导出所有数据")
        print("3. 返回")

        choice = input("\n请选择操作 (1-3): ").strip()

        if choice == "1":
            self._export_monthly_data()
        elif choice == "2":
            self._export_all_data()
        elif choice == "3":
            return
        else:
            print("错误：无效的选项")

    def _export_monthly_data(self) -> None:
        """导出指定月份数据"""
        # 获取可用月份
        available_months = self.database.get_available_months()

        if not available_months:
            print("\n数据库中没有数据")
            return

        print("\n可用月份列表：")
        for idx, month in enumerate(available_months, start=1):
            print(f"  {idx}. {month}")

        # 选择月份
        while True:
            choice = input("\n请选择月份（输入序号或输入'q'返回）: ").strip()

            if choice.lower() == "q":
                return

            try:
                idx = int(choice)
                if 1 <= idx <= len(available_months):
                    month = available_months[idx - 1]
                    break
                else:
                    print(f"错误：请输入1-{len(available_months)}之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")

        # 查询数据
        try:
            data = self.database.query_by_month(month, device_id=self.current_device_id)

            if data.empty:
                print(f"\n月份 {month} 没有数据")
                return

            # 选择导出格式
            print("\n导出格式：")
            print("1. Excel (.xlsx)")
            print("2. CSV (.csv)")

            while True:
                format_choice = input("请选择格式 (1-2): ").strip()
                if format_choice in ["1", "2"]:
                    break
                print("错误：请输入1或2")

            # 生成默认文件名
            if format_choice == "1":
                default_filename = f"data_{month}.xlsx"
                extension = ".xlsx"
            else:
                default_filename = f"data_{month}.csv"
                extension = ".csv"

            output_path_str = input(f"\n请输入输出文件路径（默认：{default_filename}）: ").strip()

            if not output_path_str:
                output_path = Path(default_filename)
            else:
                output_path = Path(output_path_str)

            # 确保文件扩展名正确
            if output_path.suffix.lower() != extension:
                output_path = output_path.with_suffix(extension)

            # 导出数据
            if format_choice == "1":
                self.exporter.export_to_excel(data, output_path)
            else:
                self.exporter.export_to_csv(data, output_path)

            print(f"数据已导出到: {output_path.absolute()}")
            logger.info(f"月份 {month} 的数据已导出: {output_path}")

        except (DatabaseError, FileError) as e:
            logger.error(f"导出失败: {e}")
            print(f"错误：导出失败 - {e}")

    def _export_all_data(self) -> None:
        """导出所有数据"""
        try:
            # 获取所有月份
            available_months = self.database.get_available_months(device_id=self.current_device_id)

            if not available_months:
                print("\n数据库中没有数据")
                return

            # 查询所有数据
            all_data = []
            for month in available_months:
                month_data = self.database.query_by_month(month, device_id=self.current_device_id)
                all_data.append(month_data)

            import pandas as pd

            combined_data = pd.concat(all_data, ignore_index=True)

            # 选择导出格式
            print("\n导出格式：")
            print("1. Excel (.xlsx)")
            print("2. CSV (.csv)")

            while True:
                format_choice = input("请选择格式 (1-2): ").strip()
                if format_choice in ["1", "2"]:
                    break
                print("错误：请输入1或2")

            # 生成默认文件名
            if format_choice == "1":
                default_filename = "all_data.xlsx"
                extension = ".xlsx"
            else:
                default_filename = "all_data.csv"
                extension = ".csv"

            output_path_str = input(f"\n请输入输出文件路径（默认：{default_filename}）: ").strip()

            if not output_path_str:
                output_path = Path(default_filename)
            else:
                output_path = Path(output_path_str)

            # 确保文件扩展名正确
            if output_path.suffix.lower() != extension:
                output_path = output_path.with_suffix(extension)

            # 导出数据
            if format_choice == "1":
                self.exporter.export_to_excel(combined_data, output_path)
            else:
                self.exporter.export_to_csv(combined_data, output_path)

            print(f"所有数据已导出到: {output_path.absolute()}")
            logger.info(f"所有数据已导出: {output_path}")

        except (DatabaseError, FileError) as e:
            logger.error(f"导出失败: {e}")
            print(f"错误：导出失败 - {e}")
