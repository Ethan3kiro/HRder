# 智谱AI GLM-4V-Flash 配置指南

## 🎉 为什么选择智谱AI？

- **完全免费** - GLM-4V-Flash 模型永久免费使用
- **视觉识别能力强** - 支持图文理解，识别准确率高
- **国内服务** - 访问速度快，稳定性好
- **无需信用卡** - 注册即可使用，无需绑定支付方式

## 📝 获取 API Key

### 1. 注册智谱AI账号

访问：https://open.bigmodel.cn/

点击右上角"注册/登录"，使用手机号或微信注册。

### 2. 创建 API Key

1. 登录后，点击右上角头像
2. 选择"API Keys"
3. 点击"创建新的 API Key"
4. 复制生成的 API Key（格式类似：`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx`）

⚠️ **重要**：API Key 只显示一次，请妥善保存！

## ⚙️ 配置方法

### 方法 1：通过设置页面配置（推荐）

1. 启动 HarrisReader
2. 进入"系统设置"页面
3. 在"API 识别设置"部分：
   - **API Key**：粘贴你的智谱AI API Key
   - **API URL**：`https://open.bigmodel.cn/api/paas/v4/chat/completions`
   - **模型名称**：`glm-4v-flash`
4. 点击"保存 API 配置"
5. 点击"测试 API 连接"验证配置
6. 重启程序使配置生效

### 方法 2：手动编辑配置文件

编辑 `config/api_config.json`：

```json
{
  "provider": "zhipu",
  "api_key": "你的智谱AI API密钥",
  "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
  "extra_params": {
    "model": "glm-4v-flash",
    ...
  }
}
```

## 🧪 测试 API

运行测试脚本：

```bash
python test_zhipu_api.py
```

如果看到 "✅ API 调用成功！"，说明配置正确。

## 💡 使用说明

配置完成后：

1. 进入"数据录入"页面
2. 选择截图文件
3. 点击"🌐 API 识别"按钮
4. 等待 10-30 秒，识别结果会自动填充到表格中

## 📊 模型对比

| 特性 | GLM-4V-Flash | 阿里百炼 qwen-vl-max |
|------|--------------|---------------------|
| 费用 | **完全免费** | 收费（已停止服务） |
| 速度 | 快 | 中等 |
| 准确率 | 高 | 高 |
| 稳定性 | 好 | 已停止 |
| 注册难度 | 简单 | 中等 |

## ❓ 常见问题

### Q1: API Key 在哪里找？

A: 登录 https://open.bigmodel.cn/ → 点击头像 → API Keys → 创建新的 API Key

### Q2: 提示"API 连接失败"怎么办？

A: 检查以下几点：
1. API Key 是否正确（包含完整的 `.` 后缀）
2. 网络连接是否正常
3. API URL 是否正确：`https://open.bigmodel.cn/api/paas/v4/chat/completions`

### Q3: 识别速度慢怎么办？

A: GLM-4V-Flash 通常在 10-30 秒内完成识别。如果超过 1 分钟，可能是网络问题，建议重试。

### Q4: 识别准确率如何？

A: 根据测试，GLM-4V-Flash 对清晰的截图识别准确率可达 95%+。建议：
- 使用高清截图
- 确保文字清晰可见
- 避免截图过暗或过亮

### Q5: 有使用限制吗？

A: GLM-4V-Flash 完全免费，但可能有以下限制：
- 每分钟请求次数限制（通常足够个人使用）
- 单次图片大小限制（程序会自动压缩）

### Q6: 可以同时使用多个 API 吗？

A: 目前程序只支持配置一个 API。如需切换，修改配置文件后重启程序即可。

## 🔗 相关链接

- 智谱AI 开放平台：https://open.bigmodel.cn/
- GLM-4V 文档：https://docs.z.ai/
- 定价说明：https://docs.z.ai/guides/overview/pricing

## 📞 技术支持

如有问题，请在 GitHub Issues 中反馈：
https://github.com/Ethan915025/HarrisReader/issues

---

**祝使用愉快！** 🎉
