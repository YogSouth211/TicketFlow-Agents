# SupportPilot 启动说明

1. 安装 Python 3.10 或更新版本。
2. 在项目根目录创建并激活虚拟环境。
3. 运行 `pip install -r requirements.txt`。
4. 将 `.env.example` 复制为 `.env`，配置模型 API Key、Base URL 和模型名。
5. 运行 `python app.py`，打开 http://localhost:7860。

阿里云百炼配置示例：

```env
DASHSCOPE_API_KEY=你的阿里云百炼 API Key
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
```

首次启动会创建本地 SQLite 数据库 `supportpilot.db`。可用演示账号：`acme-001`、`northstar-002`。可查询工单：`SP-1001`、`SP-1002`。

页面有三个入口：

1. **智能协作**：依次试产品咨询、故障排查、创建工单，查看执行过程。
2. **工单工作台**：刷新列表查看新工单，选择工单后填写处理记录并更新状态；也可以人工创建工单。
3. **知识库**：新增一条带关键词的指南，再回到智能协作提问；同名标题会更新原知识。

第一次读代码建议按 [学习指南与面试准备](learning-guide.md) 的五步顺序进行。
