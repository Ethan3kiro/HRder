"""
系统设置组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QSpinBox, QMessageBox, QGroupBox,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal
import json
from pathlib import Path


class SettingsWidget(QWidget):
    """系统设置组件"""
    
    # 信号
    theme_changed = pyqtSignal(str)
    
    def __init__(self, settings_manager, database):
        super().__init__()
        self.settings_manager = settings_manager
        self.database = database
        self.current_theme = "light"
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        title = QLabel("⚙️ 系统设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # API 识别设置
        api_group = QGroupBox("🌐 API 识别设置")
        api_layout = QFormLayout()
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入阿里百炼 API Key (sk-...)")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("API Key：", self.api_key_edit)
        
        # 显示/隐藏 API Key 按钮
        show_key_btn = QPushButton("👁️ 显示")
        show_key_btn.setMaximumWidth(80)
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        api_layout.addRow("", show_key_btn)
        
        # API URL
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        api_layout.addRow("API URL：", self.api_url_edit)
        
        # 模型名称
        self.api_model_edit = QLineEdit()
        self.api_model_edit.setPlaceholderText("qwen-vl-max")
        api_layout.addRow("模型名称：", self.api_model_edit)
        
        # Max Tokens
        self.api_max_tokens_spin = QSpinBox()
        self.api_max_tokens_spin.setRange(512, 8192)
        self.api_max_tokens_spin.setSingleStep(512)
        self.api_max_tokens_spin.setValue(4096)
        self.api_max_tokens_spin.setToolTip("最大输出token数，建议4096以上以确保完整输出所有数据")
        api_layout.addRow("Max Tokens：", self.api_max_tokens_spin)
        
        # 保存 API 配置按钮
        save_api_btn = QPushButton("💾 保存 API 配置")
        save_api_btn.clicked.connect(self.save_api_config)
        api_layout.addRow("", save_api_btn)
        
        # 测试 API 按钮
        test_api_btn = QPushButton("🧪 测试 API 连接")
        test_api_btn.clicked.connect(self.test_api_connection)
        api_layout.addRow("", test_api_btn)
        
        # API 状态显示
        self.api_status_label = QLabel()
        self.api_status_label.setWordWrap(True)
        api_layout.addRow("状态：", self.api_status_label)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 深度学习模型设置
        dl_group = QGroupBox("🤖 深度学习模型设置")
        dl_layout = QFormLayout()
        
        # 启用/禁用深度学习模型
        self.enable_dl_checkbox = QCheckBox("启用深度学习辅助识别")
        dl_layout.addRow("", self.enable_dl_checkbox)
        
        # 模型状态
        self.dl_status_label = QLabel()
        self.dl_status_label.setWordWrap(True)
        dl_layout.addRow("模型状态：", self.dl_status_label)
        
        # 模型路径
        self.dl_model_path_label = QLabel()
        self.dl_model_path_label.setWordWrap(True)
        dl_layout.addRow("模型文件：", self.dl_model_path_label)
        
        dl_group.setLayout(dl_layout)
        layout.addWidget(dl_group)
        
        # 灵敏度设置
        sensitivity_group = QGroupBox("📊 灵敏度阈值设置")
        sensitivity_layout = QFormLayout()
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setSuffix(" %")
        self.threshold_spin.setValue(
            int(self.settings_manager.get_sensitivity_threshold())
        )
        
        sensitivity_layout.addRow("变化阈值：", self.threshold_spin)
        
        save_btn = QPushButton("💾 保存设置")
        save_btn.clicked.connect(self.save_settings)
        sensitivity_layout.addRow("", save_btn)
        
        sensitivity_group.setLayout(sensitivity_layout)
        layout.addWidget(sensitivity_group)
        
        # 主题设置
        theme_group = QGroupBox("🎨 界面主题")
        theme_layout = QHBoxLayout()
        
        light_btn = QPushButton("☀️ 浅色主题")
        light_btn.clicked.connect(lambda: self.change_theme("light"))
        theme_layout.addWidget(light_btn)
        
        dark_btn = QPushButton("🌙 深色主题")
        dark_btn.clicked.connect(lambda: self.change_theme("dark"))
        theme_layout.addWidget(dark_btn)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 数据库信息
        db_group = QGroupBox("💾 数据库信息")
        db_layout = QFormLayout()
        
        db_path = str(self.database.db_path)
        db_path_label = QLabel(db_path)
        db_path_label.setWordWrap(True)
        db_layout.addRow("数据库路径：", db_path_label)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        layout.addStretch()
        
        # 设置滚动区域
        scroll.setWidget(content_widget)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # 加载当前配置
        self.load_current_config()
    
    def save_settings(self):
        """保存设置"""
        try:
            threshold = self.threshold_spin.value()
            self.settings_manager.set_sensitivity_threshold(threshold)
            
            QMessageBox.information(
                self, "成功", f"灵敏度阈值已设置为 {threshold}%"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"保存设置失败：\n{str(e)}"
            )
    
    def load_current_config(self):
        """加载当前配置"""
        # 加载 API 配置
        api_config_path = Path("config/api_config.json")
        if api_config_path.exists():
            try:
                with open(api_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key_edit.setText(config.get('api_key', ''))
                    self.api_url_edit.setText(config.get('api_url', ''))
                    
                    # 从 extra_params 中获取模型名称和 max_tokens
                    extra_params = config.get('extra_params', {})
                    model = extra_params.get('model', '')
                    self.api_model_edit.setText(model)
                    
                    # 从 payload_template 中获取 max_tokens
                    payload_template = extra_params.get('payload_template', {})
                    max_tokens = payload_template.get('max_tokens', 4096)
                    self.api_max_tokens_spin.setValue(max_tokens)
                    
                    # 更新状态
                    if config.get('api_key') and config['api_key'] not in ['', '输入阿里百炼API Key', '请在此处填入您的阿里百炼API密钥']:
                        self.api_status_label.setText("✅ API 已配置")
                        self.api_status_label.setStyleSheet("color: green;")
                    else:
                        self.api_status_label.setText("⚠️ 请配置 API Key")
                        self.api_status_label.setStyleSheet("color: orange;")
            except Exception as e:
                self.api_status_label.setText(f"❌ 配置文件读取失败：{str(e)}")
                self.api_status_label.setStyleSheet("color: red;")
        else:
            self.api_status_label.setText("⚠️ 配置文件不存在")
            self.api_status_label.setStyleSheet("color: orange;")
            # 设置默认值
            self.api_url_edit.setText("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
            self.api_model_edit.setText("qwen-vl-max")
        
        # 检查深度学习模型状态
        self.check_dl_model_status()
    
    def check_dl_model_status(self):
        """检查深度学习模型状态"""
        try:
            import torch
            torch_available = True
        except ImportError:
            torch_available = False
        
        model_path = Path("models/digit_ocr_model.pth")
        coordinates_path = Path("models/coordinates.json")
        
        if not torch_available:
            self.dl_status_label.setText("❌ PyTorch 未安装")
            self.dl_status_label.setStyleSheet("color: red;")
            self.enable_dl_checkbox.setEnabled(False)
            self.enable_dl_checkbox.setChecked(False)
            self.dl_model_path_label.setText("请安装: pip install torch torchvision")
        elif not model_path.exists():
            self.dl_status_label.setText("⚠️ 模型文件不存在")
            self.dl_status_label.setStyleSheet("color: orange;")
            self.enable_dl_checkbox.setEnabled(False)
            self.enable_dl_checkbox.setChecked(False)
            self.dl_model_path_label.setText(f"模型路径: {model_path}\n请先训练模型")
        elif not coordinates_path.exists():
            self.dl_status_label.setText("⚠️ 坐标文件不存在")
            self.dl_status_label.setStyleSheet("color: orange;")
            self.enable_dl_checkbox.setEnabled(False)
            self.enable_dl_checkbox.setChecked(False)
            self.dl_model_path_label.setText(f"坐标路径: {coordinates_path}\n请先提取坐标")
        else:
            self.dl_status_label.setText("✅ 模型可用")
            self.dl_status_label.setStyleSheet("color: green;")
            self.enable_dl_checkbox.setEnabled(True)
            self.enable_dl_checkbox.setChecked(True)
            self.dl_model_path_label.setText(f"模型路径: {model_path}")
    
    def toggle_api_key_visibility(self):
        """切换 API Key 显示/隐藏"""
        if self.api_key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText("🙈 隐藏")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText("👁️ 显示")
    
    def save_api_config(self):
        """保存 API 配置"""
        api_key = self.api_key_edit.text().strip()
        api_url = self.api_url_edit.text().strip()
        model = self.api_model_edit.text().strip()
        max_tokens = self.api_max_tokens_spin.value()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入 API Key")
            return
        
        if not api_url:
            QMessageBox.warning(self, "警告", "请输入 API URL")
            return
        
        if not model:
            QMessageBox.warning(self, "警告", "请输入模型名称")
            return
        
        # 构建配置
        config = {
            "provider": "custom",
            "api_key": api_key,
            "api_url": api_url,
            "extra_params": {
                "headers": {
                    "Content-Type": "application/json"
                },
                "auth_header": "Authorization",
                "auth_prefix": "Bearer",
                "model": model,
                "payload_template": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "识别图中COMBINER ISO TEMPERATURES(AZ,BZ,CZ,DZ,AB,CD,ABCD)和Z-Plane数据(A/B/C/D模块各8行)。\n\n⚠️重要:Z-Plane每行有Current、Temp、ISO Temp三列,请识别Current列和ISO Temp列(最右侧),不要识别Temp列。\n\n返回JSON格式:\n{\"data\":[{\"item_name\":\"AZ\",\"value\":30.0,\"unit\":\"°C\"},{\"item_name\":\"Z-Plane A-Current-1\",\"value\":7.2,\"unit\":\"A\"},{\"item_name\":\"Z-Plane A-ISO Temp-1\",\"value\":48.0,\"unit\":\"°C\"}]}\n\n要求:纯JSON,不用markdown,value为数字,Z-Plane必须读Current和ISO Temp列,按COMBINER->Z-Plane A->B->C->D顺序"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": "data:image/jpeg;base64,{{image}}"
                                    }
                                }
                            ]
                        }
                    ]
                },
                "data_path": "choices.0.message.content",
                "timeout": 120
            }
        }
        
        # 保存配置
        config_path = Path("config/api_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.api_status_label.setText("✅ API 配置已保存")
            self.api_status_label.setStyleSheet("color: green;")
            
            QMessageBox.information(
                self, "成功", 
                "API 配置已保存！\n\n"
                "请切换到其他页面再返回数据录入页面，\n"
                "或重启程序以使配置生效。"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"保存配置失败：\n{str(e)}"
            )
    
    def test_api_connection(self):
        """测试 API 连接"""
        api_key = self.api_key_edit.text().strip()
        api_url = self.api_url_edit.text().strip()
        model = self.api_model_edit.text().strip()
        
        if not api_key or not api_url or not model:
            QMessageBox.warning(self, "警告", "请先填写完整的 API 配置")
            return
        
        # 简单测试：发送一个最小的请求
        try:
            import requests
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "测试连接"
                    }
                ]
            }
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.api_status_label.setText("✅ API 连接测试成功")
                self.api_status_label.setStyleSheet("color: green;")
                QMessageBox.information(self, "成功", "API 连接测试成功！")
            else:
                self.api_status_label.setText(f"❌ API 返回错误：{response.status_code}")
                self.api_status_label.setStyleSheet("color: red;")
                QMessageBox.warning(
                    self, "失败", 
                    f"API 返回错误：\n状态码：{response.status_code}\n响应：{response.text[:200]}"
                )
                
        except Exception as e:
            self.api_status_label.setText(f"❌ 连接失败：{str(e)}")
            self.api_status_label.setStyleSheet("color: red;")
            QMessageBox.critical(
                self, "错误", f"API 连接测试失败：\n{str(e)}"
            )
    
    def change_theme(self, theme_name):
        """切换主题"""
        self.current_theme = theme_name
        self.theme_changed.emit(theme_name)
        
        QMessageBox.information(
            self, "提示", f"已切换到{theme_name}主题"
        )
    
    def refresh(self):
        """刷新数据"""
        self.threshold_spin.setValue(
            int(self.settings_manager.get_sensitivity_threshold())
        )
        # 重新加载配置
        self.load_current_config()
