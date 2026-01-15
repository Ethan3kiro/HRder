"""
数据库管理模块

提供发射机数据的持久化存储和查询功能
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import pandas as pd
import re

from src.exceptions import DatabaseError, DataValidationError
from src.config import Config

logger = logging.getLogger(__name__)


class TransmitterDatabase:
    """发射机数据库管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径（可选，使用默认路径）
        """
        self.db_path = db_path if db_path else Config.get_default_db_path()
        self.connection: Optional[sqlite3.Connection] = None

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 建立连接
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row

            # 性能优化配置
            self.connection.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            self.connection.execute(
                "PRAGMA synchronous=NORMAL"
            )  # 平衡性能和安全性
            self.connection.execute("PRAGMA cache_size=-64000")  # 64MB缓存
            self.connection.execute("PRAGMA temp_store=MEMORY")  # 临时表存储在内存

            logger.info(f"数据库连接成功: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise DatabaseError(f"无法连接到数据库: {str(e)}")

    def initialize_database(self) -> None:
        """创建数据库表结构（多设备架构）"""
        try:
            cursor = self.connection.cursor()

            # 创建设备表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL UNIQUE,
                    device_code TEXT,
                    description TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建设置表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建主数据表（多设备架构）
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transmitter_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(device_id, month, item_name),
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            """
            )

            # 创建索引
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_device_month 
                ON transmitter_data(device_id, month)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_device_item 
                ON transmitter_data(device_id, item_name)
            """
            )

            self.connection.commit()
            logger.info("数据库表结构初始化成功（多设备架构）")

        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise DatabaseError(f"无法初始化数据库: {str(e)}")

    def _validate_month_format(self, month: str) -> bool:
        """
        验证月份格式是否为YYYY-MM

        Args:
            month: 月份字符串

        Returns:
            是否符合格式
        """
        pattern = r"^\d{4}-\d{2}$"
        return bool(re.match(pattern, month))

    def insert_monthly_data(
        self,
        month: str,
        data: pd.DataFrame,
        overwrite: bool = False,
        device_id: int = 1,
    ) -> None:
        """
        插入月度数据

        Args:
            month: 月份字符串（YYYY-MM格式）
            data: 包含item_name、value、unit的DataFrame
            overwrite: 是否覆盖已存在的数据
            device_id: 设备ID（默认为1）

        Raises:
            ValueError: 月份格式错误
            DataValidationError: 数据完整性验证失败
            DatabaseError: 数据已存在且overwrite=False
        """
        # 验证月份格式
        if not self._validate_month_format(month):
            raise ValueError(f"月份格式错误，应为YYYY-MM格式: {month}")

        # 验证数据完整性
        required_columns = {"item_name", "value", "unit"}
        if not required_columns.issubset(data.columns):
            missing = required_columns - set(data.columns)
            raise DataValidationError(f"数据缺少必需字段: {missing}")

        # 检查是否有空值
        if data[["item_name", "value"]].isnull().any().any():
            raise DataValidationError("数据项名称和数值不能为空")

        # 检查是否已存在该月份的数据
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM transmitter_data WHERE device_id = ? AND month = ?",
            (device_id, month),
        )
        existing_count = cursor.fetchone()["count"]

        if existing_count > 0 and not overwrite:
            raise DatabaseError(
                f"设备 {device_id} 的月份 {month} 数据已存在，请使用overwrite=True覆盖"
            )

        try:
            # 如果需要覆盖，先删除旧数据
            if existing_count > 0 and overwrite:
                cursor.execute(
                    "DELETE FROM transmitter_data WHERE device_id = ? AND month = ?",
                    (device_id, month),
                )
                logger.info(f"已删除设备 {device_id} 月份 {month} 的旧数据")

            # 插入新数据
            insert_data = []
            for _, row in data.iterrows():
                insert_data.append(
                    (
                        device_id,
                        month,
                        row["item_name"],
                        float(row["value"]),
                        str(row["unit"]) if pd.notna(row["unit"]) else "",
                    )
                )

            cursor.executemany(
                """
                INSERT INTO transmitter_data (device_id, month, item_name, value, unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                insert_data,
            )

            self.connection.commit()
            logger.info(
                f"成功插入 {len(insert_data)} 条数据到设备 {device_id} 月份 {month}"
            )

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"数据插入失败: {e}")
            raise DatabaseError(f"无法插入数据: {str(e)}")

    def query_by_month(self, month: str, device_id: int = 1) -> pd.DataFrame:
        """
        查询指定设备和月份的所有数据

        Args:
            month: 月份字符串（YYYY-MM格式）
            device_id: 设备ID（默认为1）

        Returns:
            包含完整数据的DataFrame
        """
        try:
            query = """
                SELECT id, device_id, month, item_name, value, unit, create_time
                FROM transmitter_data
                WHERE device_id = ? AND month = ?
                ORDER BY item_name
            """
            df = pd.read_sql_query(query, self.connection, params=(device_id, month))
            logger.info(f"查询设备 {device_id} 月份 {month} 返回 {len(df)} 条记录")
            return df

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}")
            raise DatabaseError(f"无法查询数据: {str(e)}")

    def query_by_item(self, item_name: str, device_id: int = 1) -> pd.DataFrame:
        """
        查询指定设备和数据项的历史记录

        Args:
            item_name: 数据项名称
            device_id: 设备ID（默认为1）

        Returns:
            包含该数据项所有月份记录的DataFrame
        """
        try:
            query = """
                SELECT id, device_id, month, item_name, value, unit, create_time
                FROM transmitter_data
                WHERE device_id = ? AND item_name = ?
                ORDER BY month
            """
            df = pd.read_sql_query(
                query, self.connection, params=(device_id, item_name)
            )
            logger.info(
                f"查询设备 {device_id} 数据项 {item_name} 返回 {len(df)} 条记录"
            )
            return df

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}")
            raise DatabaseError(f"无法查询数据: {str(e)}")

    def get_available_months(self, device_id: int = None) -> List[str]:
        """
        获取数据库中所有可用月份

        Args:
            device_id: 设备ID（可选，如果指定则只返回该设备的月份）

        Returns:
            月份列表（按时间排序）
        """
        try:
            cursor = self.connection.cursor()

            if device_id is not None:
                cursor.execute(
                    """
                    SELECT DISTINCT month
                    FROM transmitter_data
                    WHERE device_id = ?
                    ORDER BY month
                """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT DISTINCT month
                    FROM transmitter_data
                    ORDER BY month
                """
                )

            months = [row["month"] for row in cursor.fetchall()]
            logger.info(f"找到 {len(months)} 个可用月份")
            return months

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}")
            raise DatabaseError(f"无法获取可用月份: {str(e)}")

    def get_all_items(self, device_id: int = None) -> List[str]:
        """
        获取所有数据项名称

        Args:
            device_id: 设备ID（可选，如果指定则只返回该设备的数据项）

        Returns:
            数据项名称列表
        """
        try:
            cursor = self.connection.cursor()

            if device_id is not None:
                cursor.execute(
                    """
                    SELECT DISTINCT item_name
                    FROM transmitter_data
                    WHERE device_id = ?
                    ORDER BY item_name
                """,
                    (device_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT DISTINCT item_name
                    FROM transmitter_data
                    ORDER BY item_name
                """
                )

            items = [row["item_name"] for row in cursor.fetchall()]
            logger.info(f"找到 {len(items)} 个数据项")
            return items

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}")
            raise DatabaseError(f"无法获取数据项列表: {str(e)}")

    def delete_month(self, month: str, device_id: int = None) -> int:
        """
        删除指定月份的数据

        Args:
            month: 月份字符串
            device_id: 设备ID（可选，如果指定则只删除该设备的数据）

        Returns:
            删除的记录数
        """
        try:
            cursor = self.connection.cursor()

            if device_id is not None:
                cursor.execute(
                    "DELETE FROM transmitter_data WHERE device_id = ? AND month = ?",
                    (device_id, month),
                )
            else:
                cursor.execute(
                    "DELETE FROM transmitter_data WHERE month = ?", (month,)
                )

            deleted_count = cursor.rowcount
            self.connection.commit()
            logger.info(f"删除月份 {month} 的 {deleted_count} 条记录")
            return deleted_count

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"删除失败: {e}")
            raise DatabaseError(f"无法删除数据: {str(e)}")

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
