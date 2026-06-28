# Job Companion

求职作战中心 v1。pnpm monorepo：`apps/web`（Next.js 15）+ `apps/api`（FastAPI）。

完整文档见 `docs/superpowers/`（specs / plans / design）。

## Dev

```bash
pnpm install
docker compose -f infra/docker-compose.yml up -d   # postgres + redis
pnpm --filter api dev    # http://localhost:8000
pnpm --filter web dev    # http://localhost:3000
```

## 工具链版本说明（本机偏离记录）

Plan 文档锁定 Node 20 / Python 3.11，本机环境更新，采用以下适配：

- **pnpm**：经 `npm install -g pnpm@9.12.0`（本机 Node 未自带 corepack）。
- **Node**：本机 v26，Next.js 15 可正常运行（`.nvmrc` 仍声明 20 作为目标意图）。
- **Python**：本机 3.14。`apps/api` 依赖采用兼容 3.14 的最新版本（pydantic≥2.10、psycopg、litellm、cryptography 等取最新，保持大版本一致）。若需严格复现文档 pin，请改用 Python 3.11。
- **venv 激活**：Windows 用 `apps/api/.venv/Scripts/activate`。
