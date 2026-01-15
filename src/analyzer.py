"""
数据分析模块

提供月度数据对比和统计分析功能
"""
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.database import TransmitterDatabase
from src.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器"""

    def __init__(self, database: TransmitterDatabase):
        """
        初始化分析器

        Args:
            database: 数据库管理器实例
        """
        self.database = database
        logger.info("数据分析器初始化成功")

    def _calculate_absolute_change(self, value1: float, value2: float) -> float:
        """
        计算绝对变化量

        Args:
            value1: 第一个值（较早）
            value2: 第二个值（较晚）

        Returns:
            绝对变化量（value2 - value1）
        """
        return value2 - value1

    def _calculate_relative_change(self, value1: float, value2: float) -> float:
        """
        计算相对变化率（百分比）

        Args:
            value1: 第一个值（较早）
            value2: 第二个值（较晚）

        Returns:
            相对变化率（百分比）
        """
        if value1 == 0:
            # 避免除以零，如果原值为0，返回特殊值
            return (
                float("inf") if value2 > 0 else (float("-inf") if value2 < 0 else 0.0)
            )

        return ((value2 - value1) / value1) * 100.0

    def _determine_change_status(
        self, absolute_change: float, threshold: float = 0.01
    ) -> str:
        """
        确定变化状态

        Args:
            absolute_change: 绝对变化量
            threshold: 判断阈值（默认0.01）

        Returns:
            变化状态：'increase'（增长）、'decrease'（下降）、'no_change'（无变化）
        """
        if absolute_change > threshold:
            return "increase"
        elif absolute_change < -threshold:
            return "decrease"
        else:
            return "no_change"

    def compare_two_months(
        self,
        month1: str,
        month2: str,
        device_id: int = 1,
        sensitivity_threshold: float = None,
    ) -> pd.DataFrame:
        """
        对比两个月的数据

        Args:
            month1: 第一个月份（较早）
            month2: 第二个月份（较晚）
            device_id: 设备ID（默认为1）
            sensitivity_threshold: 灵敏度阈值（百分比），只标记超过此阈值的变化

        Returns:
            包含以下列的DataFrame：
            - item_name: 数据项名称
            - value_month1: 第一个月的数值
            - value_month2: 第二个月的数值
            - unit: 单位
            - absolute_change: 绝对变化量（month2 - month1）
            - relative_change: 相对变化率（百分比）
            - change_status: 变化状态（'increase', 'decrease', 'no_change'）
            - significant_change: 是否为显著变化（如果设置了灵敏度阈值）
            - missing_in: 缺失信息（如果数据项只在一个月存在）
        """
        logger.info(f"开始对比设备 {device_id} 的月份 {month1} 和 {month2}")

        # 查询两个月的数据
        df1 = self.database.query_by_month(month1, device_id)
        df2 = self.database.query_by_month(month2, device_id)

        if df1.empty:
            raise DataValidationError(f"月份 {month1} 没有数据")
        if df2.empty:
            raise DataValidationError(f"月份 {month2} 没有数据")

        # 准备数据用于合并
        df1_clean = df1[["item_name", "value", "unit"]].copy()
        df2_clean = df2[["item_name", "value", "unit"]].copy()

        # 重命名列以便区分
        df1_clean = df1_clean.rename(columns={"value": "value_month1"})
        df2_clean = df2_clean.rename(columns={"value": "value_month2"})

        # 外连接以识别缺失项
        merged = pd.merge(
            df1_clean,
            df2_clean[["item_name", "value_month2"]],
            on="item_name",
            how="outer",
        )

        # 初始化结果列
        merged["absolute_change"] = pd.NA
        merged["relative_change"] = pd.NA
        merged["change_status"] = None
        merged["missing_in"] = None

        # 向量化处理：识别缺失项
        missing_in_month1 = merged["value_month1"].isna()
        missing_in_month2 = merged["value_month2"].isna()

        merged.loc[missing_in_month1, "missing_in"] = month1
        merged.loc[missing_in_month2, "missing_in"] = month2
        merged.loc[missing_in_month1 | missing_in_month2, "change_status"] = "missing"

        # 向量化处理：计算变化量（仅对非缺失项）
        valid_rows = ~(missing_in_month1 | missing_in_month2)

        if valid_rows.any():
            # 计算绝对变化量
            merged.loc[valid_rows, "absolute_change"] = (
                merged.loc[valid_rows, "value_month2"]
                - merged.loc[valid_rows, "value_month1"]
            )

            # 计算相对变化率
            # 处理除以零的情况
            val1_nonzero = merged.loc[valid_rows, "value_month1"] != 0
            valid_nonzero_idx = merged.index[valid_rows][val1_nonzero]

            if len(valid_nonzero_idx) > 0:
                merged.loc[valid_nonzero_idx, "relative_change"] = (
                    (
                        merged.loc[valid_nonzero_idx, "value_month2"]
                        - merged.loc[valid_nonzero_idx, "value_month1"]
                    )
                    / merged.loc[valid_nonzero_idx, "value_month1"]
                    * 100.0
                )

            # 处理除以零的特殊情况
            val1_zero = valid_rows & (merged["value_month1"] == 0)
            if val1_zero.any():
                merged.loc[
                    val1_zero & (merged["value_month2"] > 0), "relative_change"
                ] = float("inf")
                merged.loc[
                    val1_zero & (merged["value_month2"] < 0), "relative_change"
                ] = float("-inf")
                merged.loc[
                    val1_zero & (merged["value_month2"] == 0), "relative_change"
                ] = 0.0

            # 向量化确定变化状态
            abs_change = merged.loc[valid_rows, "absolute_change"]
            merged.loc[valid_rows, "change_status"] = "no_change"
            merged.loc[valid_rows & (abs_change > 0.01), "change_status"] = "increase"
            merged.loc[valid_rows & (abs_change < -0.01), "change_status"] = "decrease"

        # 应用灵敏度过滤（如果设置了阈值）
        if sensitivity_threshold is not None:
            merged["significant_change"] = False
            if valid_rows.any():
                merged.loc[valid_rows, "significant_change"] = (
                    abs(merged.loc[valid_rows, "relative_change"]) > sensitivity_threshold
                )
            logger.info(
                f"应用灵敏度阈值 {sensitivity_threshold}%，"
                f"发现 {merged['significant_change'].sum()} 个显著变化"
            )

        # 重新排序列
        result_columns = [
            "item_name",
            "value_month1",
            "value_month2",
            "unit",
            "absolute_change",
            "relative_change",
            "change_status",
            "missing_in",
        ]

        if sensitivity_threshold is not None:
            result_columns.append("significant_change")

        result = merged[result_columns]

        logger.info(f"对比完成，共 {len(result)} 个数据项")

        # 统计缺失项
        missing_count = result["missing_in"].notna().sum()
        if missing_count > 0:
            logger.warning(f"发现 {missing_count} 个缺失项")

        return result

    def calculate_statistics(
        self,
        item_name: str,
        device_id: int = 1,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        计算数据项的统计指标

        Args:
            item_name: 数据项名称
            device_id: 设备ID（默认为1）
            start_month: 起始月份（可选）
            end_month: 结束月份（可选）

        Returns:
            包含mean、std、min、max、median等统计指标的字典
        """
        logger.info(f"计算设备 {device_id} 数据项 {item_name} 的统计指标")

        # 查询数据项的历史记录
        df = self.database.query_by_item(item_name, device_id)

        if df.empty:
            raise DataValidationError(f"数据项 {item_name} 没有历史记录")

        # 过滤月份范围
        if start_month:
            df = df[df["month"] >= start_month]
        if end_month:
            df = df[df["month"] <= end_month]

        if df.empty:
            raise DataValidationError(f"指定月份范围内没有数据项 {item_name} 的记录")

        # 计算统计指标
        values = df["value"].values

        statistics = {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
        }

        logger.info(f"统计指标计算完成: {statistics}")
        return statistics

    def detect_anomalies(
        self, item_name: str, device_id: int = 1, threshold: float = 2.0
    ) -> List[Tuple[str, float]]:
        """
        检测异常值（基于标准差）

        Args:
            item_name: 数据项名称
            device_id: 设备ID（默认为1）
            threshold: 异常阈值（标准差倍数，默认2.0）

        Returns:
            异常值列表：[(月份, 数值), ...]
        """
        logger.info(
            f"检测设备 {device_id} 数据项 {item_name} 的异常值（阈值={threshold}σ）"
        )

        # 查询数据项的历史记录
        df = self.database.query_by_item(item_name, device_id)

        if df.empty:
            raise DataValidationError(f"数据项 {item_name} 没有历史记录")

        if len(df) < 3:
            logger.warning(f"数据项 {item_name} 的记录数少于3条，无法进行异常检测")
            return []

        # 计算均值和标准差
        values = df["value"].values
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            logger.warning(f"数据项 {item_name} 的标准差为0，无异常值")
            return []

        # 检测异常值
        anomalies = []
        for _, row in df.iterrows():
            z_score = abs((row["value"] - mean) / std)
            if z_score > threshold:
                anomalies.append((row["month"], row["value"]))

        logger.info(f"检测到 {len(anomalies)} 个异常值")
        return anomalies
