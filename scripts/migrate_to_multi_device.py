"""
数据库迁移脚本：添加多设备支持

使用方法:
    python scripts/migrate_to_multi_device.py
"""
import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def migrate_database(db_path: Path):
    """迁移数据库到多设备架构"""

    if not db_path.exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 备份数据库
        backup_path = (
            db_path.parent
            / f"{db_path.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        )
        backup_conn = sqlite3.connect(str(backup_path))
        conn.backup(backup_conn)
        backup_conn.close()
        logger.info(f"✅ 数据库已备份到: {backup_path}")

        # 1. 创建devices表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL UNIQUE,
                device_code TEXT,
                description TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ devices表创建成功")

        # 2. 创建settings表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                description TEXT,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ settings表创建成功")

        # 3. 检查是否已有设备
        cursor.execute("SELECT COUNT(*) as count FROM devices")
        device_count = cursor.fetchone()["count"]

        if device_count == 0:
            # 创建默认设备
            cursor.execute(
                """
                INSERT INTO devices (device_name, device_code, description)
                VALUES (?, ?, ?)
            """,
                ("默认设备", "DEFAULT-001", "系统默认设备（迁移自旧数据）"),
            )
            default_device_id = cursor.lastrowid
            logger.info(f"✅ 默认设备创建成功，ID: {default_device_id}")
        else:
            cursor.execute("SELECT id FROM devices ORDER BY id LIMIT 1")
            default_device_id = cursor.fetchone()["id"]
            logger.info(f"✅ 使用现有设备，ID: {default_device_id}")

        # 4. 检查transmitter_data表是否已有device_id列
        cursor.execute("PRAGMA table_info(transmitter_data)")
        columns = [col[1] for col in cursor.fetchall()]

        if "device_id" not in columns:
            logger.info("开始迁移transmitter_data表结构...")

            # 创建新表
            cursor.execute("""
                CREATE TABLE transmitter_data_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(device_id, month, item_name)
                )
            """)

            # 复制数据
            cursor.execute(
                f"""
                INSERT INTO transmitter_data_new 
                (id, device_id, month, item_name, value, unit, create_time)
                SELECT id, {default_device_id}, month, item_name, value, unit, create_time
                FROM transmitter_data
            """
            )
            rows_migrated = cursor.rowcount
            logger.info(f"✅ 已迁移 {rows_migrated} 条记录")

            # 删除旧表
            cursor.execute("DROP TABLE transmitter_data")

            # 重命名新表
            cursor.execute("ALTER TABLE transmitter_data_new RENAME TO transmitter_data")

            # 重建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_device_month 
                ON transmitter_data(device_id, month)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_device_item 
                ON transmitter_data(device_id, item_name)
            """)
            logger.info("✅ 表结构重建成功，索引创建成功")
        else:
            logger.info("✅ device_id列已存在，跳过表结构迁移")

        # 5. 插入默认设置
        cursor.execute(
            """
            INSERT OR IGNORE INTO settings (setting_key, setting_value, description)
            VALUES (?, ?, ?)
        """,
            ("sensitivity_threshold", "5.0", "变化灵敏度阈值（百分比）"),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO settings (setting_key, setting_value, description)
            VALUES (?, ?, ?)
        """,
            ("current_device_id", str(default_device_id), "当前选择的设备ID"),
        )

        logger.info("✅ 默认设置创建成功")

        conn.commit()
        logger.info("=" * 60)
        logger.info("🎉 数据库迁移完成！")
        logger.info("=" * 60)

        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ 数据库迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("发射机数据分析器 - 数据库迁移工具")
    print("多设备支持 + 灵敏度设置")
    print("=" * 60)
    print()

    db_path = Config.get_default_db_path()
    print(f"数据库路径: {db_path}")
    print()

    if not db_path.exists():
        print("⚠️  数据库文件不存在，将在首次使用时自动创建")
        print("无需运行迁移脚本")
        sys.exit(0)

    response = input("是否继续迁移？这将备份现有数据库。(y/n): ")
    if response.lower() not in ["y", "yes", "是"]:
        print("迁移已取消")
        sys.exit(0)

    print()
    print("开始迁移...")
    print()

    if migrate_database(db_path):
        print()
        print("✅ 迁移成功！")
        print()
        print("下一步:")
        print("1. 重启应用程序")
        print("2. 在主菜单选择'设备管理'添加新设备")
        print("3. 在'系统设置'中调整灵敏度阈值")
    else:
        print()
        print("❌ 迁移失败！请查看错误信息")
        sys.exit(1)
