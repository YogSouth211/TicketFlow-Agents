# 路由检查怎么读

运行 `python -m eval.routing_eval`。脚本读取 `routing_cases.json` 的 6 条请求，用同一个 Qwen 模型运行 Supervisor 和三个 Agent；每条请求用不同 `thread_id`。SQLite 使用临时文件，结束后清理，不会改动页面的 `supportpilot.db`。

一条用例通过，表示 Agent 顺序与标注一致、标注的业务工具都被调用，而且“应建单/不应建单”的实际结果正确。`routing_results.json` 保存逐题路由和工具名。

当前一次运行通过 4/6：产品知识、故障排查、工单状态和直接建单通过；“先排查再建单”停在排查 Agent，无效账号请求没有调用预期的建单校验工具。模型有随机性，重复运行可能不同。

这个脚本只评估原始 Supervisor。Gradio 页面另有两层保护：建单前要求确认，Agent 建单工具入口拒绝未经确认的调用；确认过的请求若被 Supervisor 漏路由，页面会补一次工单 Agent 调用。因此路由分数和页面端到端完成情况要分开看。
