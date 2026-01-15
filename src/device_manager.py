"""
设备管理模块

提供多设备管理功能
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DeviceManager:
    """设备管理器"""

    def __init__(self, database):
        """
        初始化设备管理器

        Args:
            database: TransmitterDatabase实例
        """
        self.database = database
        logger.info("设备管理器初始化成功")

    def add_device(
        self, device_name: str, device_code: str = None, description: str = None
    ) -> int:
        """
        添加设备

        Args:
            device_name: 设备名称
            device_code: 设备编号（可选）
            description: 设备描述（可选）

        Returns:
            新设备的ID

        Raises:
            DatabaseError: 设备名称已存在或数据库错误
        """
        cursor = self.database.connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO devices (device_name, device_code, description)
                VALUES (?, ?, ?)
            """,
                (device_name, device_code, description),
            )

            device_id = cursor.lastrowid
            self.database.connection.commit()

            logger.info(f"设备添加成功: {device_name} (ID: {device_id})")
            return device_id

        except Exception as e:
            self.database.connection.rollback()
            logger.error(f"设备添加失败: {e}")
            raise DatabaseError(f"无法添加设备，名称可能已存在: {device_name}")

    def get_all_devices(self) -> List[Dict]:
        """
        获取所有设备

        Returns:
            设备列表，每个设备是一个字典
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            SELECT id, device_name, device_code, description, 
                   create_time, last_update
            FROM devices
            ORDER BY id
        """
        )

        devices = []
        for row in cursor.fetchall():
            devices.append(
                {
                    "id": row["id"],
                    "device_name": row["device_name"],
                    "device_code": row["device_code"],
                    "description": row["description"],
                    "create_time": row["create_time"],
                    "last_update": row["last_update"],
                }
            )

        logger.info(f"查询到 {len(devices)} 个设备")
        return devices

    def get_device_by_id(self, device_id: int) -> Optional[Dict]:
        """
        根据ID获取设备

        Args:
            device_id: 设备ID

        Returns:
            设备信息字典，如果不存在返回None
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            SELECT id, device_name, device_code, description,
                   create_time, last_update
            FROM devices
            WHERE id = ?
        """,
            (device_id,),
        )

        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "device_name": row["device_name"],
                "device_code": row["device_code"],
                "description": row["description"],
                "create_time": row["create_time"],
                "last_update": row["last_update"],
            }
        return None

    def update_device(
        self,
        device_id: int,
        device_name: str = None,
        device_code: str = None,
        description: str = None,
    ) -> None:
        """
        更新设备信息

        Args:
            device_id: 设备ID
            device_name: 新设备名称（可选）
            device_code: 新设备编号（可选）
            description: 新描述（可选）

        Raises:
            DatabaseError: 设备不存在或更新失败
        """
        # 检查设备是否存在
        if not self.get_device_by_id(device_id):
            raise DatabaseError(f"设备不存在: {device_id}")

        updates = []
        params = []

        if device_name is not None:
            updates.append("device_name = ?")
            params.append(device_name)

        if device_code is not None:
            updates.append("device_code = ?")
            params.append(device_code)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return

        updates.append("last_update = CURRENT_TIMESTAMP")
        params.append(device_id)

        cursor = self.database.connection.cursor()
        try:
            cursor.execute(
                f"""
                UPDATE devices
                SET {', '.join(updates)}
                WHERE id = ?
            """,
                params,
            )

            self.database.connection.commit()
            logger.info(f"设备 {device_id} 更新成功")

        except Exception as e:
            self.database.connection.rollback()
            logger.error(f"设备更新失败: {e}")
            raise DatabaseError(f"无法更新设备: {str(e)}")

    def delete_device(self, device_id: int, confirm: bool = False) -> int:
        """
        删除设备及其所有数据

        Args:
            device_id: 设备ID
            confirm: 确认删除（必须为True）

        Returns:
            删除的数据记录数

        Raises:
            DatabaseError: 未确认删除或设备不存在
        """
        if not confirm:
            raise DatabaseError("删除设备需要确认（confirm=True）")

        # 检查设备是否存在
        device = self.get_device_by_id(device_id)
        if not device:
            raise DatabaseError(f"设备不存在: {device_id}")

        cursor = self.database.connection.cursor()

        try:
            # 删除设备的所有数据
            cursor.execute(
                """
                DELETE FROM transmitter_data
                WHERE device_id = ?
            """,
                (device_id,),
            )
            data_count = cursor.rowcount

            # 删除设备
            cursor.execute(
                """
                DELETE FROM devices
                WHERE id = ?
            """,
                (device_id,),
            )

            self.database.connection.commit()
            logger.info(f"设备 {device_id} 及其 {data_count} 条数据已删除")

            return data_count

        except Exception as e:
            self.database.connection.rollback()
            logger.error(f"设备删除失败: {e}")
            raise DatabaseError(f"无法删除设备: {str(e)}")

    def get_device_data_count(self, device_id: int) -> int:
        """
        获取设备的数据记录数

        Args:
            device_id: 设备ID

        Returns:
            数据记录数
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM transmitter_data
            WHERE device_id = ?
        """,
            (device_id,),
        )

        return cursor.fetchone()["count"]

    def get_device_months(self, device_id: int) -> List[str]:
        """
        获取设备的所有月份

        Args:
            device_id: 设备ID

        Returns:
            月份列表
        """
        cursor = self.database.connection.cursor()
        cursor.execute(
            """
            SELECT DISTINCT month
            FROM transmitter_data
            WHERE device_id = ?
            ORDER BY month
        """,
            (device_id,),
        )

        return [row["month"] for row in cursor.fetchall()]
