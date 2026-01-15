"""
设置管理模块

提供系统设置管理功能
"""
import logging
from typing import Optional, Dict

from src.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class SettingsManager:
    """设置管理器"""

    def __init__(self, database):
        """
        初始化设置管理器

        Args:
            database: TransmitterDatabase实例
        """
        self.database = database
        logger.info("设置管理器初始化成功")

    def get_sensitivity_threshold(self) -> float:
        """
        获取灵敏度阈值

        Returns:
            灵敏度阈值（百分比）
        """
        value = self.get_setting("sensitivity_threshold")
        return float(value) if value else 5.0

    def set_sensitivity_threshold(self, threshold: float) -> None:
        """
        设置灵敏度阈值

        Args:
            threshold: 灵敏度阈值（百分比）

        Raises:
            DataValidationError: 阈值无效
        """
        if threshold < 0 or threshold > 100:
            raise DataValidationError("灵敏度阈值必须在0-100之间")

        self.set_setting(
            "sensitivity_threshold",
            str(threshold),
            "变化灵敏度阈值（百分比）",
        )
        logger.info(f"灵敏度阈值已设置为: {threshold}%")

    def get_current_device_id(self) -> Optional[int]:
        """
        获取当前选择的设备ID

        Returns:
            设备ID，如果未设置返回None
        """
        value = self.get_setting("current_device_id")
        return int(value) if value else None

    def set_current_device_id(self, device_id: int) -> None:
        """
        设置当前选择的设备ID

        Args:
            device_id: 设备ID
        """
        self.set_setting("current_device_id", str(device_id), "当前选择的设备ID")
        logger.info(f"当前设备已设置为: {device_id}")

    def get_setting(self, key: str) -> Optional[str]:
        """
        获取设置值

        Args:
            key: 设置键

        Returns:
            设置值，如果不存在返回None
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            SELECT setting_value
            FROM settings
            WHERE setting_key = ?
        """,
            (key,),
        )

        row = cursor.fetchone()
        return row["setting_value"] if row else None

    def set_setting(
        self, key: str, value: str, description: str = None
    ) -> None:
        """
        设置值

        Args:
            key: 设置键
            value: 设置值
            description: 设置描述（可选）
        """
        cursor = self.database.connection.cursor()

        if description:
            cursor.execute(
                """
                INSERT OR REPLACE INTO settings 
                (setting_key, setting_value, description, update_time)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (key, value, description),
            )
        else:
            cursor.execute(
                """
                INSERT OR REPLACE INTO settings 
                (setting_key, setting_value, update_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (key, value),
            )

        self.database.connection.commit()
        logger.info(f"设置已更新: {key} = {value}")

    def get_all_settings(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有设置

        Returns:
            设置字典，格式: {key: {'value': value, 'description': description}}
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            SELECT setting_key, setting_value, description
            FROM settings
        """
        )

        settings = {}
        for row in cursor.fetchall():
            settings[row["setting_key"]] = {
                "value": row["setting_value"],
                "description": row["description"],
            }

        return settings

    def delete_setting(self, key: str) -> None:
        """
        删除设置

        Args:
            key: 设置键
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            DELETE FROM settings
            WHERE setting_key = ?
        """,
            (key,),
        )

        self.database.connection.commit()
        logger.info(f"设置已删除: {key}")
