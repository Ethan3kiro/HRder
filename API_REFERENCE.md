# API 参考文档

## 概述

本文档列出了发射机数据分析器中常用的 API 方法和字段名称，帮助开发者正确使用这些 API。

---

## DeviceManager API

### 获取所有设备
```python
devices = device_manager.get_all_devices()
# 返回: List[Dict]
# 每个设备字典包含: id, device_name, device_code, description, create_time, last_update
```

### 根据 ID 获取设备
```python
device = device_manager.get_device_by_id(device_id)
# 参数: device_id (int)
# 返回: Dict 或 None
# 字段: id, device_name, device_code, description, create_time, last_update
```

### 添加设备
```python
device_id = device_manager.add_device(
    device_name="发射机1",
    device_code="TX001",  # 可选
    description="描述"     # 可选
)
# 返回: int (新设备的 ID)
```

### 更新设备
```python
device_manager.update_device(
    device_id=1,
    device_name="新名称",  # 可选
    device_code="新编号",  # 可选
    description="新描述"   # 可选
)
```

### 删除设备
```python
deleted_count = device_manager.delete_device(
    device_id=1,
    confirm=True  # 必须为 True
)
# 返回: int (删除的数据记录数)
```

### 获取设备数据记录数
```python
count = device_manager.get_device_data_count(device_id=1)
# 返回: int
```

### 获取设备的所有月份
```python
months = device_manager.get_device_months(device_id=1)
# 返回: List[str] (如 ['2026-01', '2026-02'])
```

---

## SettingsManager API

### 获取当前设备 ID
```python
device_id = settings_manager.get_current_device_id()
# 返回: int 或 None
```

### 设置当前设备 ID
```python
settings_manager.set_current_device_id(device_id=1)
```

### 获取灵敏度阈值
```python
threshold = settings_manager.get_sensitivity_threshold()
# 返回: float (默认 5.0)
```

### 设置灵敏度阈值
```python
settings_manager.set_sensitivity_threshold(threshold=10.0)
# 参数: threshold (float, 0-100)
```

---

## TransmitterDatabase API

### 获取可用月份
```python
months = database.get_available_months(device_id=1)
# 参数: device_id (int, 可选)
# 返回: List[str] (如 ['2026-01', '2026-02'])
```

### 获取所有数据项
```python
items = database.get_all_items(device_id=1)
# 参数: device_id (int, 可选)
# 返回: List[str] (数据项名称列表)
```

### 查询指定月份的数据
```python
df = database.query_by_month(month="2026-01", device_id=1)
# 参数: month (str, YYYY-MM 格式), device_id (int, 默认 1)
# 返回: pandas.DataFrame
# 列: id, device_id, month, item_name, value, unit, create_time
```

### 查询指定数据项的历史
```python
df = database.query_by_item(item_name="功率", device_id=1)
# 参数: item_name (str), device_id (int, 默认 1)
# 返回: pandas.DataFrame
# 列: id, device_id, month, item_name, value, unit, create_time
```

### 插入月度数据
```python
database.insert_monthly_data(
    month="2026-01",
    data=df,  # pandas.DataFrame，包含 item_name, value, unit 列
    overwrite=False,  # 是否覆盖已存在的数据
    device_id=1
)
```

### 删除月份数据
```python
deleted_count = database.delete_month(month="2026-01", device_id=1)
# 返回: int (删除的记录数)
```

---

## 字段名称参考

### Device 字典字段
```python
device = {
    'id': 1,                          # 设备 ID
    'device_name': '发射机1',          # 设备名称 ⚠️ 注意不是 'name'
    'device_code': 'TX001',           # 设备编号
    'description': '描述信息',         # 设备描述
    'create_time': '2026-01-11 ...',  # 创建时间
    'last_update': '2026-01-11 ...'   # 最后更新时间
}
```

### 数据记录字段
```python
# DataFrame 列名
columns = [
    'id',           # 记录 ID
    'device_id',    # 设备 ID
    'month',        # 月份 (YYYY-MM)
    'item_name',    # 数据项名称
    'value',        # 数值
    'unit',         # 单位
    'create_time'   # 创建时间
]
```

---

## 常见使用模式

### 模式 1: 获取当前设备信息
```python
# ✅ 正确方式
device_id = self.settings_manager.get_current_device_id()
if not device_id:
    # 处理无设备的情况
    return

device = self.device_manager.get_device_by_id(device_id)
if not device:
    # 处理设备不存在的情况
    return

# 使用设备信息
device_name = device['device_name']  # ⚠️ 注意字段名

# ❌ 错误方式
device = self.device_manager.get_current_device()  # 此方法不存在！
```

### 模式 2: 获取设备的月份列表
```python
# ✅ 正确方式
device_id = self.settings_manager.get_current_device_id()
months = self.database.get_available_months(device_id=device_id)

# ❌ 错误方式
months = self.database.get_all_months(device_id=device_id)  # 此方法不存在！
```

### 模式 3: 获取设备的数据项列表
```python
# ✅ 正确方式
device_id = self.settings_manager.get_current_device_id()
items = self.database.get_all_items(device_id=device_id)

# 这个方法名是正确的！
```

### 模式 4: 组件初始化（需要访问当前设备）
```python
# ✅ 正确方式
class MyWidget(QWidget):
    def __init__(self, database, device_manager, settings_manager):
        super().__init__()
        self.database = database
        self.device_manager = device_manager
        self.settings_manager = settings_manager  # ⚠️ 必须包含
        
        self.init_ui()

# ❌ 错误方式
class MyWidget(QWidget):
    def __init__(self, database, device_manager):  # 缺少 settings_manager
        super().__init__()
        self.database = database
        self.device_manager = device_manager
        
        self.init_ui()
```

---

## 常见错误和解决方案

### 错误 1: 'DeviceManager' object has no attribute 'get_current_device'
**原因**: 使用了不存在的方法

**解决方案**:
```python
# 改为
device_id = self.settings_manager.get_current_device_id()
device = self.device_manager.get_device_by_id(device_id)
```

### 错误 2: 'TransmitterDatabase' object has no attribute 'get_all_months'
**原因**: 方法名称错误

**解决方案**:
```python
# 改为
months = self.database.get_available_months(device_id=device_id)
```

### 错误 3: KeyError: 'name'
**原因**: 字段名称错误

**解决方案**:
```python
# 改为
device_name = device['device_name']  # 不是 device['name']
```

### 错误 4: 组件缺少 settings_manager 参数
**原因**: 构造函数缺少必需的参数

**解决方案**:
```python
# 在 __init__ 中添加 settings_manager 参数
def __init__(self, database, device_manager, settings_manager):
    self.settings_manager = settings_manager
```

---

## 方法名称对照表

### 正确 vs 错误

| 功能 | ❌ 错误用法 | ✅ 正确用法 |
|------|-----------|-----------|
| 获取当前设备 | `device_manager.get_current_device()` | `settings_manager.get_current_device_id()` + `device_manager.get_device_by_id()` |
| 获取月份列表 | `database.get_all_months()` | `database.get_available_months()` |
| 设备名称字段 | `device['name']` | `device['device_name']` |
| 设备编号字段 | `device['code']` | `device['device_code']` |

---

## 最佳实践

### 1. 始终检查返回值
```python
device_id = self.settings_manager.get_current_device_id()
if not device_id:
    # 处理无设备的情况
    QMessageBox.warning(self, "提示", "请先选择设备")
    return

device = self.device_manager.get_device_by_id(device_id)
if not device:
    # 处理设备不存在的情况
    QMessageBox.warning(self, "错误", "设备不存在")
    return
```

### 2. 使用正确的字段名称
```python
# 使用常量或明确的字段名
DEVICE_NAME_FIELD = 'device_name'
device_name = device[DEVICE_NAME_FIELD]
```

### 3. 传递所有必需的参数
```python
# 在 main_window.py 中初始化组件时
self.my_widget = MyWidget(
    self.database,
    self.device_manager,
    self.settings_manager  # 不要忘记这个！
)
```

### 4. 使用类型提示
```python
from typing import Optional, List, Dict

def get_device_info(self, device_id: int) -> Optional[Dict]:
    """获取设备信息"""
    return self.device_manager.get_device_by_id(device_id)
```

---

## 参考资源

- `src/device_manager.py` - DeviceManager 实现
- `src/settings_manager.py` - SettingsManager 实现
- `src/database.py` - TransmitterDatabase 实现
- `BUG_FIX_REPORT.md` - 常见错误和修复方法

---

**文档版本**: 1.0  
**最后更新**: 2026-01-11  
**维护者**: Kiro AI Assistant
