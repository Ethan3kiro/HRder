"""
GUI 组件模块
"""

from .dashboard_widget import DashboardWidget
from .device_widget import DeviceWidget
from .data_entry_widget import DataEntryWidget
from .comparison_widget import ComparisonWidget
from .trend_widget import TrendWidget
from .data_management_widget import DataManagementWidget
from .settings_widget import SettingsWidget

__all__ = [
    'DashboardWidget',
    'DeviceWidget',
    'DataEntryWidget',
    'ComparisonWidget',
    'TrendWidget',
    'DataManagementWidget',
    'SettingsWidget',
]
