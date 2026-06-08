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
        self.api_max_tokens_spin.setRange(512, 16384)
        self.api_max_tokens_spin.setSingleStep(512)
        self.api_max_tokens_spin.setValue(8000)
        self.api_max_tokens_spin.setToolTip("最大输出token数，建议8000以上以确保完整输出所有71项数据")
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
                    max_tokens = payload_template.get('max_tokens', 8000)
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
        
        # 检查深度学习模型状态已移除
    
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
                                    "text": "仔细识别图片中的所有数字。\n\n第一部分：COMBINER ISO TEMPERATURES（图片上方）\n识别7个温度：AZ,BZ,CZ,DZ,AB,CD,ABCD\n\n第二部分：Z-Plane数据（图片下方4个表格A/B/C/D）\n每个表格8行，每行读2个值：\n- Current列（第1列）：约7-8A\n- ISO Temp列（第4列最右侧）：约40-60°C\n跳过中间的Temp和ISO Gate列\n\n返回纯JSON（不要markdown）：\n{\"data\":[{\"item_name\":\"AZ\",\"value\":实际数字,\"unit\":\"°C\"},...全部71项]}\n\n重要：value必须是图片中实际看到的数字，不要猜测！必须识别全部71项。"
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
                timeout=60  # 增加到 60 秒
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
