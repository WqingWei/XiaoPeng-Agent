# 最终交付清单

**更新日期**：2026-08-07

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 根目录 README | ✅ 已完成 | 包含项目简介、三层架构图、技术栈、3 条本地命令、目录与配置 |
| 8 个场景文档 | ✅ 已完成 | `scenarios/` 下 8 个独立文档，含初始状态、测试对话、预期行为和安全规则 |
| 模拟数据说明 | ✅ 已完成 | `scenarios/README.md` 说明数据来源、工厂、重置语义、隐私与局限 |
| 本地生产环境 | ✅ 已验证 | Docker 双镜像、健康检查、REST / Socket.IO 与 8/8 场景联调已通过 |
| GitHub 仓库 | ⏳ 待推送 | 仓库已存在；步骤 15–17 的本地提交/改动需在用户指令后推送 |
| 可访问 Web 链接 | ⏳ 待授权 | 已有 `render.yaml` / `frontend/vercel.json`；尚无云平台凭据、项目链接和生产 URL |
| 8 个场景截图 | ⏳ 待补采 | 当前执行环境无可用浏览器；未用生成图或占位图冒充真实截图 |
| Demo 视频 | ➖ 不适用 | 用户明确指示本次不用录制 Demo 视频 |

## 上线后补验

1. 在 Render 配置 `OPENAI_API_KEY` 和 `CORS_ORIGINS`，获得后端 HTTPS URL。
2. 在 Vercel Production 配置 `NEXT_PUBLIC_API_URL` 和 `NEXT_PUBLIC_SOCKET_URL`。
3. 确认 `/health`、首页、REST 与 Socket.IO 在 HTTPS 下正常。
4. 在线运行 8 个标准场景，按 README 规格采集 8 张真实截图。

## 交付前复核命令

```bash
cd backend && PYTHONPYCACHEPREFIX=/tmp/xiaopeng_delivery .venv/bin/python -m pytest -q
cd frontend && pnpm lint && pnpm exec tsc --noEmit && pnpm build
docker compose config --quiet
```

