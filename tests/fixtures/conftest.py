"""
pytest配置和共享fixtures
"""
import pytest
from pathlib import Path
from hypothesis import settings, HealthCheck


# Hypothesis全局配置
settings.register_profile(
    "default",
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("default")


@pytest.fixture
def temp_db_path(tmp_path):
    """提供临时数据库路径"""
    return tmp_path / "test_transmitter.db"


@pytest.fixture
def sample_data_dir():
    """提供示例数据目录路径"""
    return Path(__file__).parent / "sample_images"


@pytest.fixture
def mock_extracted_data():
    """提供模拟的OCR提取数据"""
    import pandas as pd

    return pd.DataFrame(
        {
            "item_name": ["Forward Power", "Reflected Power", "PA Voltage"],
            "value": [100.5, 2.3, 12.5],
            "unit": ["W", "W", "V"],
        }
    )


@pytest.fixture
def sample_months():
    """提供示例月份列表"""
    return ["2026-01", "2026-02", "2026-03"]
