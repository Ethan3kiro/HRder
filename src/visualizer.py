"""
数据可视化模块

提供交互式和静态图表生成功能
"""
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # 使用非交互式后端

from src.database import TransmitterDatabase
from src.exceptions import DataValidationError, FileError

logger = logging.getLogger(__name__)


# 可视化样式配置
STYLE_CONFIG = {
    "figure_size": (12, 6),
    "dpi": 100,
    "font_family": "sans-serif",
    "title_size": 14,
    "label_size": 12,
    "tick_size": 10,
    "line_width": 2,
    "marker_size": 8,
    "color_increase": "#FF4444",  # 红色
    "color_decrease": "#44FF44",  # 绿色
    "color_no_change": "#CCCCCC",  # 灰色
    "color_threshold": "#FF8800",  # 橙色
    "grid_alpha": 0.3,
}


class DataVisualizer:
    """数据可视化器"""

    def __init__(self, database: TransmitterDatabase):
        """
        初始化可视化器

        Args:
            database: 数据库管理器实例
        """
        self.database = database
        logger.info("数据可视化器初始化成功")

    def plot_comparison_chart(
        self, comparison_df: pd.DataFrame, output_path: Optional[Path] = None
    ) -> None:
        """
        绘制两月对比柱状图

        Args:
            comparison_df: 对比数据DataFrame
            output_path: 输出文件路径（可选）

        图表特性：
        - 并排柱状图展示两月数值
        - 有变化的柱子标注变化量和变化率
        - 使用颜色区分变化状态（红色=增长，绿色=下降，灰色=无变化）

        Raises:
            DataValidationError: 数据格式错误
            FileError: 文件保存失败
        """
        logger.info("开始绘制对比图表")

        # 验证数据格式
        required_columns = {
            "item_name",
            "value_month1",
            "value_month2",
            "change_status",
        }
        if not required_columns.issubset(comparison_df.columns):
            missing = required_columns - set(comparison_df.columns)
            raise DataValidationError(f"对比数据缺少必需字段: {missing}")

        # 过滤掉缺失项（只显示两月都存在的数据项）
        valid_data = comparison_df[comparison_df["change_status"] != "missing"].copy()

        if valid_data.empty:
            logger.warning("没有可对比的数据项")
            return

        # 准备数据
        items = valid_data["item_name"].tolist()
        values1 = valid_data["value_month1"].tolist()
        values2 = valid_data["value_month2"].tolist()
        statuses = valid_data["change_status"].tolist()

        # 创建图表
        fig, ax = plt.subplots(
            figsize=STYLE_CONFIG["figure_size"], dpi=STYLE_CONFIG["dpi"]
        )

        # 设置柱状图位置
        x = np.arange(len(items))
        width = 0.35

        # 绘制柱状图
        bars1 = ax.bar(
            x - width / 2, values1, width, label="月份1", color="#6699CC", alpha=0.8
        )
        bars2 = ax.bar(
            x + width / 2, values2, width, label="月份2", color="#99CCFF", alpha=0.8
        )

        # 根据变化状态为第二个月的柱子添加边框颜色
        for i, (bar, status) in enumerate(zip(bars2, statuses)):
            if status == "increase":
                bar.set_edgecolor(STYLE_CONFIG["color_increase"])
                bar.set_linewidth(2)
            elif status == "decrease":
                bar.set_edgecolor(STYLE_CONFIG["color_decrease"])
                bar.set_linewidth(2)
            elif status == "no_change":
                bar.set_edgecolor(STYLE_CONFIG["color_no_change"])
                bar.set_linewidth(2)

        # 标注变化量和变化率
        for i, row in valid_data.iterrows():
            if row["change_status"] != "no_change":
                abs_change = row["absolute_change"]
                rel_change = row["relative_change"]

                # 计算标注位置
                idx = valid_data.index.get_loc(i)
                y_pos = max(row["value_month1"], row["value_month2"]) * 1.05

                # 格式化标注文本
                if abs(rel_change) < float("inf"):
                    label_text = f"{abs_change:+.1f}\n({rel_change:+.1f}%)"
                else:
                    label_text = f"{abs_change:+.1f}"

                # 添加标注
                ax.text(
                    idx,
                    y_pos,
                    label_text,
                    ha="center",
                    va="bottom",
                    fontsize=STYLE_CONFIG["tick_size"] - 1,
                    color="black",
                )

        # 设置图表属性
        ax.set_xlabel("数据项", fontsize=STYLE_CONFIG["label_size"])
        ax.set_ylabel("数值", fontsize=STYLE_CONFIG["label_size"])
        ax.set_title("月度数据对比", fontsize=STYLE_CONFIG["title_size"], fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(
            items, rotation=45, ha="right", fontsize=STYLE_CONFIG["tick_size"]
        )
        ax.tick_params(axis="y", labelsize=STYLE_CONFIG["tick_size"])
        ax.legend(fontsize=STYLE_CONFIG["label_size"])
        ax.grid(True, alpha=STYLE_CONFIG["grid_alpha"], axis="y")

        # 调整布局
        plt.tight_layout()

        # 保存或显示图表
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(output_path, dpi=STYLE_CONFIG["dpi"], bbox_inches="tight")
                logger.info(f"对比图表已保存到: {output_path}")
            except Exception as e:
                logger.error(f"保存图表失败: {e}")
                raise FileError(f"无法保存图表: {str(e)}")
            finally:
                plt.close(fig)
        else:
            plt.close(fig)
            logger.info("对比图表绘制完成")

    def plot_trend_chart(
        self,
        item_names: List[str],
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        threshold: Optional[float] = None,
        output_path: Optional[Path] = None,
        interactive: bool = True,
    ) -> None:
        """
        绘制月度趋势折线图

        Args:
            item_names: 数据项名称列表
            start_month: 起始月份（可选）
            end_month: 结束月份（可选）
            threshold: 阈值线（可选）
            output_path: 输出文件路径（可选）
            interactive: 是否使用plotly生成交互图表

        图表特性：
        - 每个数据项一条折线
        - 数据点标注"月份+数值"
        - 超过阈值的点标红
        - 支持交互式缩放和悬停

        Raises:
            DataValidationError: 数据项不存在
            FileError: 文件保存失败
        """
        logger.info(f"开始绘制趋势图表，数据项: {item_names}")

        if not item_names:
            raise DataValidationError("至少需要指定一个数据项")

        # 如果请求交互式图表，尝试使用plotly
        if interactive:
            try:
                import plotly.graph_objects as go

                self._plot_trend_chart_plotly(
                    item_names, start_month, end_month, threshold, output_path
                )
                return
            except ImportError:
                logger.warning("plotly未安装，使用matplotlib绘制静态图表")
                interactive = False

        # 使用matplotlib绘制静态图表
        self._plot_trend_chart_matplotlib(
            item_names, start_month, end_month, threshold, output_path
        )

    def _plot_trend_chart_matplotlib(
        self,
        item_names: List[str],
        start_month: Optional[str],
        end_month: Optional[str],
        threshold: Optional[float],
        output_path: Optional[Path],
    ) -> None:
        """使用matplotlib绘制静态趋势图"""
        # 创建图表
        fig, ax = plt.subplots(
            figsize=STYLE_CONFIG["figure_size"], dpi=STYLE_CONFIG["dpi"]
        )

        # 为每个数据项绘制折线
        colors = plt.cm.tab10(np.linspace(0, 1, len(item_names)))

        for idx, item_name in enumerate(item_names):
            # 查询数据
            df = self.database.query_by_item(item_name)

            if df.empty:
                logger.warning(f"数据项 {item_name} 没有历史记录")
                continue

            # 过滤月份范围
            if start_month:
                df = df[df["month"] >= start_month]
            if end_month:
                df = df[df["month"] <= end_month]

            if df.empty:
                logger.warning(f"数据项 {item_name} 在指定月份范围内没有数据")
                continue

            # 排序
            df = df.sort_values("month")

            months = df["month"].tolist()
            values = df["value"].tolist()

            # 绘制折线
            line = ax.plot(
                months,
                values,
                marker="o",
                markersize=STYLE_CONFIG["marker_size"],
                linewidth=STYLE_CONFIG["line_width"],
                label=item_name,
                color=colors[idx],
            )

            # 标注数据点
            for month, value in zip(months, values):
                # 检查是否超过阈值
                if threshold is not None and value > threshold:
                    color = STYLE_CONFIG["color_threshold"]
                    fontweight = "bold"
                else:
                    color = "black"
                    fontweight = "normal"

                ax.annotate(
                    f"{value:.1f}",
                    xy=(month, value),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center",
                    fontsize=STYLE_CONFIG["tick_size"] - 2,
                    color=color,
                    fontweight=fontweight,
                )

        # 绘制阈值线
        if threshold is not None:
            ax.axhline(
                y=threshold,
                color=STYLE_CONFIG["color_threshold"],
                linestyle="--",
                linewidth=2,
                label=f"阈值: {threshold}",
            )

        # 设置图表属性
        ax.set_xlabel("月份", fontsize=STYLE_CONFIG["label_size"])
        ax.set_ylabel("数值", fontsize=STYLE_CONFIG["label_size"])
        ax.set_title("月度趋势图", fontsize=STYLE_CONFIG["title_size"], fontweight="bold")
        ax.tick_params(axis="both", labelsize=STYLE_CONFIG["tick_size"])
        ax.legend(fontsize=STYLE_CONFIG["label_size"])
        ax.grid(True, alpha=STYLE_CONFIG["grid_alpha"])

        # 旋转x轴标签
        plt.xticks(rotation=45, ha="right")

        # 调整布局
        plt.tight_layout()

        # 保存或显示图表
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(output_path, dpi=STYLE_CONFIG["dpi"], bbox_inches="tight")
                logger.info(f"趋势图表已保存到: {output_path}")
            except Exception as e:
                logger.error(f"保存图表失败: {e}")
                raise FileError(f"无法保存图表: {str(e)}")
            finally:
                plt.close(fig)
        else:
            plt.close(fig)
            logger.info("趋势图表绘制完成")

    def _plot_trend_chart_plotly(
        self,
        item_names: List[str],
        start_month: Optional[str],
        end_month: Optional[str],
        threshold: Optional[float],
        output_path: Optional[Path],
    ) -> None:
        """使用plotly绘制交互式趋势图"""
        import plotly.graph_objects as go

        fig = go.Figure()

        # 为每个数据项添加折线
        for item_name in item_names:
            # 查询数据
            df = self.database.query_by_item(item_name)

            if df.empty:
                logger.warning(f"数据项 {item_name} 没有历史记录")
                continue

            # 过滤月份范围
            if start_month:
                df = df[df["month"] >= start_month]
            if end_month:
                df = df[df["month"] <= end_month]

            if df.empty:
                logger.warning(f"数据项 {item_name} 在指定月份范围内没有数据")
                continue

            # 排序
            df = df.sort_values("month")

            months = df["month"].tolist()
            values = df["value"].tolist()

            # 添加折线
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=values,
                    mode="lines+markers",
                    name=item_name,
                    text=[
                        f"{month}<br>{value:.1f}"
                        for month, value in zip(months, values)
                    ],
                    hovertemplate="%{text}<extra></extra>",
                    line=dict(width=STYLE_CONFIG["line_width"]),
                    marker=dict(size=STYLE_CONFIG["marker_size"]),
                )
            )

        # 添加阈值线
        if threshold is not None:
            fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color=STYLE_CONFIG["color_threshold"],
                annotation_text=f"阈值: {threshold}",
                annotation_position="right",
            )

        # 设置布局
        fig.update_layout(
            title="月度趋势图",
            xaxis_title="月份",
            yaxis_title="数值",
            hovermode="closest",
            template="plotly_white",
            font=dict(size=STYLE_CONFIG["label_size"]),
            width=STYLE_CONFIG["figure_size"][0] * 100,
            height=STYLE_CONFIG["figure_size"][1] * 100,
        )

        # 保存图表
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # 根据文件扩展名选择保存格式
                if output_path.suffix.lower() == ".html":
                    fig.write_html(str(output_path))
                else:
                    # 保存为静态图像（需要kaleido）
                    fig.write_image(str(output_path))

                logger.info(f"交互式趋势图表已保存到: {output_path}")
            except Exception as e:
                logger.error(f"保存图表失败: {e}")
                raise FileError(f"无法保存图表: {str(e)}")
        else:
            logger.info("交互式趋势图表绘制完成")

    def _categorize_item(self, item_name: str) -> str:
        """
        根据关键词分类数据项

        Args:
            item_name: 数据项名称

        Returns:
            类别名称：'power'、'temperature'、'voltage'、'current'、'other'
        """
        item_lower = item_name.lower()

        # 电流相关（优先检查，避免与power的'w'冲突）
        if any(keyword in item_lower for keyword in ["current", "amp"]):
            return "current"

        # 功率相关
        if any(keyword in item_lower for keyword in ["power", "watt"]):
            return "power"

        # 温度相关
        if any(
            keyword in item_lower
            for keyword in ["temp", "temperature", "°c", "celsius"]
        ):
            return "temperature"

        # 电压相关
        if any(keyword in item_lower for keyword in ["voltage", "volt"]):
            return "voltage"

        # 其他
        return "other"

    def plot_category_trends(
        self, category: str, output_path: Optional[Path] = None
    ) -> None:
        """
        按模块分类绘制趋势图

        Args:
            category: 模块类别（'power', 'temperature', 'voltage', 'current'）
            output_path: 输出文件路径（可选）

        实现：
        - 根据数据项名称关键词自动分类
        - 在同一图表中展示同类数据项

        Raises:
            DataValidationError: 类别无效或没有该类别的数据项
            FileError: 文件保存失败
        """
        logger.info(f"开始绘制类别 {category} 的趋势图")

        # 验证类别
        valid_categories = ["power", "temperature", "voltage", "current", "other"]
        if category not in valid_categories:
            raise DataValidationError(
                f"无效的类别: {category}，有效类别: {', '.join(valid_categories)}"
            )

        # 获取所有数据项
        all_items = self.database.get_all_items()

        if not all_items:
            raise DataValidationError("数据库中没有数据项")

        # 筛选该类别的数据项
        category_items = [
            item for item in all_items if self._categorize_item(item) == category
        ]

        if not category_items:
            raise DataValidationError(f"没有找到类别为 {category} 的数据项")

        logger.info(f"找到 {len(category_items)} 个 {category} 类别的数据项")

        # 使用plot_trend_chart绘制趋势图
        self.plot_trend_chart(
            item_names=category_items,
            output_path=output_path,
            interactive=False,  # 使用静态图表
        )
