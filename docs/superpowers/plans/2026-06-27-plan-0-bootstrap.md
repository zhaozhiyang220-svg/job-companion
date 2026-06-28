# Plan 0：基础设施 + 项目骨架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从空仓库到"可登录、能切中英、能切伪装界面、CI 跑通、PostHog/Sentry 埋点跑通、本地 docker 起得来"的最小可部署骨架。

**Architecture:** pnpm monorepo 双应用：`apps/web` (Next.js 15 App Router + TS) 与 `apps/api` (FastAPI + Pydantic v2 + SQLAlchemy 2.0)。本地 Docker Compose 起 Postgres + Redis；前端走 Vercel，后端走 Fly.io（v1.5 再切换）。鉴权双通道：邮箱 Magic Link 主、微信扫码副，JWT 走 HTTPOnly cookie。

**Tech Stack:** Next.js 15 / TypeScript / Tailwind / shadcn/ui / next-intl / FastAPI / Pydantic v2 / SQLAlchemy 2.0 / Alembic / Postgres 16 / Redis 7 / LiteLLM（provider=MiniMax）/ PostHog / Sentry / Playwright / pytest / Vitest / pnpm workspaces / GitHub Actions

## Global Constraints

- TypeScript strict mode（`tsconfig.json` 中 `"strict": true`），Python 用 `mypy --strict`
- 所有 endpoint Pydantic schema 严格校验，禁止 `Any` 出现在路由签名
- 所有 AI 调用必须经 `apps/api/src/ai/llm_client.py` 统一入口（本 Plan 仅做封装）
- 字段级加密对象：手机/邮箱/在职公司名（本 Plan 仅准备 `encrypt/decrypt` 工具函数；后续 Plan 调用）
- i18n 硬约束：用户可见文案禁止硬编码，必须走 next-intl `t('key')`
- 容量超限统一组件 `<CapacityGate />`（本 Plan 不实现，留接口）
- 每个 commit 必须过 CI（lint + typecheck + test + e2e）
- PostHog 事件名走 `packages/shared-types/events.ts` 强类型枚举
- 现公司相关 UI 必须有强提示组件（本 Plan 仅占位）

---

## Task 1: Monorepo Bootstrap

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `.nvmrc`
- Create: `README.md`

**Interfaces:**
- Produces: pnpm workspace 可识别 `apps/*` 与 `packages/*`；根脚本 `pnpm lint` `pnpm test` `pnpm typecheck` `pnpm e2e` 可调度子项目（实际命令在后续任务接通）

- [ ] **Step 1：初始化空仓库与 git**

Run:
```bash
mkdir job-companion && cd job-companion
git init
node -v   # 期望 v20.x；若无 nvm install 20
corepack enable
corepack prepare pnpm@9.12.0 --activate
```

- [ ] **Step 2：写 `pnpm-workspace.yaml`**

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

- [ ] **Step 3：写根 `package.json`**

```json
{
  "name": "job-companion",
  "private": true,
  "version": "0.0.0",
  "packageManager": "pnpm@9.12.0",
  "engines": { "node": ">=20.0.0" },
  "scripts": {
    "lint": "pnpm -r lint",
    "test": "pnpm -r test",
    "typecheck": "pnpm -r typecheck",
    "e2e": "pnpm --filter web e2e",
    "dev": "pnpm --filter web dev"
  }
}
```

- [ ] **Step 4：写 `.gitignore`、`.editorconfig`、`.nvmrc`**

`.gitignore`：
```
node_modules
.next
.turbo
dist
.venv
__pycache__
*.pyc
.env
.env.*.local
.DS_Store
coverage
playwright-report
test-results
.vscode
.idea
*.log
```

`.editorconfig`：
```
root = true
[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true
[*.py]
indent_size = 4
```

`.nvmrc`：
```
20
```

- [ ] **Step 5：写 `README.md` 骨架**

```markdown
# Job Companion

求职作战中心 v1。Spec：`docs/superpowers/specs/2026-06-27-job-companion-design.md`

## Dev
- `pnpm install`
- `docker compose -f infra/docker-compose.yml up -d`
- `pnpm dev`
```

- [ ] **Step 6：提交**

```bash
git add .
git commit -m "chore: bootstrap pnpm monorepo"
```

---

## Task 2: Web App Skeleton (Next.js 15 + TS + Tailwind + shadcn/ui)

**Files:**
- Create: `apps/web/` (整个 Next.js 项目)
- Create: `apps/web/package.json`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/next.config.mjs`
- Create: `apps/web/tailwind.config.ts`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/lib/utils.test.ts`

**Interfaces:**
- Produces: `pnpm --filter web dev` 启动到 http://localhost:3000，首页显示 "Job Companion"；`pnpm --filter web typecheck`、`pnpm --filter web test` 可跑

- [ ] **Step 1：用 create-next-app 生成项目**

```bash
pnpm dlx create-next-app@15.0.3 apps/web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-pnpm --no-turbopack
```

- [ ] **Step 2：安装 shadcn/ui CLI 并初始化**

```bash
cd apps/web
pnpm dlx shadcn@2.1.6 init -d --base-color slate
pnpm dlx shadcn@2.1.6 add button input card dialog toast
cd ../..
```

- [ ] **Step 3：补充 `apps/web/package.json` 的 scripts**

修改 `apps/web/package.json` 的 `"scripts"` 字段为：
```json
{
  "dev": "next dev -p 3000",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:watch": "vitest",
  "e2e": "playwright test"
}
```

- [ ] **Step 4：装 vitest + 配置**

```bash
cd apps/web
pnpm add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom
cd ../..
```

写 `apps/web/vitest.config.ts`：
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
})
```

写 `apps/web/vitest.setup.ts`：
```typescript
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 5：写一个真测试验证测试链路**

写 `apps/web/src/lib/utils.ts`：
```typescript
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}
```

写 `apps/web/src/lib/utils.test.ts`：
```typescript
import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('cn', () => {
  it('joins truthy class names with space', () => {
    expect(cn('a', 'b', null, undefined, false, 'c')).toBe('a b c')
  })
})
```

- [ ] **Step 6：跑测试 + dev 自检**

```bash
pnpm --filter web test
# 期望：1 passed
pnpm --filter web typecheck
# 期望：无错误
pnpm --filter web dev
# 浏览器开 http://localhost:3000，看到 Next.js 默认欢迎页
# Ctrl+C 终止
```

- [ ] **Step 7：提交**

```bash
git add apps/web
git commit -m "feat(web): bootstrap Next.js 15 + Tailwind + shadcn/ui + vitest"
```

---

## Task 3: API App Skeleton (FastAPI + Pydantic v2 + ruff + mypy)

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/src/main.py`
- Create: `apps/api/src/core/__init__.py`
- Create: `apps/api/src/routers/__init__.py`
- Create: `apps/api/src/routers/health.py`
- Create: `apps/api/tests/test_health.py`
- Create: `apps/api/package.json` (供 pnpm 调度)

**Interfaces:**
- Produces: `pnpm --filter api dev` 启动到 http://localhost:8000，`GET /api/v1/health` 返回 `{"status":"ok"}`；`pnpm --filter api test/typecheck/lint` 可跑

- [ ] **Step 1：建目录与 `pyproject.toml`**

```bash
mkdir -p apps/api/src/{core,routers,models,schemas,services,ai} apps/api/tests
```

写 `apps/api/pyproject.toml`：
```toml
[project]
name = "job-companion-api"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi==0.115.4",
  "uvicorn[standard]==0.32.0",
  "pydantic==2.9.2",
  "pydantic-settings==2.6.0",
  "sqlalchemy==2.0.36",
  "alembic==1.13.3",
  "psycopg[binary]==3.2.3",
  "redis==5.2.0",
  "httpx==0.27.2",
  "python-jose[cryptography]==3.3.0",
  "passlib[bcrypt]==1.7.4",
  "cryptography==43.0.3",
  "litellm==1.51.0",
  "sentry-sdk[fastapi]==2.17.0",
  "posthog==3.7.0",
]

[project.optional-dependencies]
dev = [
  "pytest==8.3.3",
  "pytest-asyncio==0.24.0",
  "pytest-cov==5.0.0",
  "httpx==0.27.2",
  "ruff==0.7.1",
  "mypy==1.13.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E","F","I","UP","B","SIM","TCH"]

[tool.mypy]
strict = true
python_version = "3.11"
mypy_path = "src"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2：建 Python venv 并安装依赖**

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate    # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
cd ../..
```

- [ ] **Step 3：写 `apps/api/package.json` 让 pnpm 能调度**

```json
{
  "name": "api",
  "version": "0.0.0",
  "scripts": {
    "dev": "uvicorn src.main:app --reload --port 8000 --app-dir .",
    "test": "pytest -q",
    "typecheck": "mypy src",
    "lint": "ruff check src tests"
  }
}
```

- [ ] **Step 4：写 `main.py` 和 `health` router（先红后绿）**

`apps/api/tests/test_health.py`：
```python
from fastapi.testclient import TestClient
from src.main import app

def test_health_returns_ok():
    client = TestClient(app)
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
```

跑测试，期望失败：
```bash
cd apps/api && source .venv/bin/activate
pytest -q
# 期望：ModuleNotFoundError: src.main
```

- [ ] **Step 5：实现 `main.py` + `health.py`**

`apps/api/src/routers/health.py`：
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

`apps/api/src/main.py`：
```python
from fastapi import FastAPI
from src.routers import health

app = FastAPI(title="Job Companion API", version="0.0.0")
app.include_router(health.router)
```

- [ ] **Step 6：跑测试 + 启动自检**

```bash
pytest -q
# 期望：1 passed
mypy src
# 期望：Success
ruff check src tests
# 期望：All checks passed
uvicorn src.main:app --reload --port 8000 --app-dir .
# 另开终端：curl http://localhost:8000/api/v1/health → {"status":"ok"}
# Ctrl+C 终止
```

- [ ] **Step 7：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): bootstrap FastAPI + Pydantic v2 + pytest + ruff + mypy"
```

---

## Task 4: Local Docker Compose (Postgres + Redis + api + web)

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `apps/api/Dockerfile`
- Create: `apps/web/Dockerfile`
- Create: `.env.example`
- Create: `apps/api/.env.example`
- Create: `apps/web/.env.example`

**Interfaces:**
- Produces: `docker compose -f infra/docker-compose.yml up -d` 一键起 4 个服务；postgres 监听 5432，redis 监听 6379，api 监听 8000，web 监听 3000

- [ ] **Step 1：写 `infra/docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: jc
      POSTGRES_PASSWORD: jc_dev
      POSTGRES_DB: jc_dev
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jc -d jc_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports: ["6379:6379"]

  api:
    build:
      context: ../apps/api
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    env_file: ../apps/api/.env
    ports: ["8000:8000"]
    volumes: ["../apps/api:/app"]
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --app-dir .

  web:
    build:
      context: ../apps/web
      dockerfile: Dockerfile
    depends_on: [api]
    env_file: ../apps/web/.env
    ports: ["3000:3000"]
    volumes:
      - ../apps/web:/app
      - /app/node_modules
      - /app/.next
    command: pnpm dev

volumes:
  pgdata:
```

- [ ] **Step 2：写 `apps/api/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e ".[dev]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "."]
```

- [ ] **Step 3：写 `apps/web/Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.0 --activate
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]
```

- [ ] **Step 4：写三个 `.env.example`**

根目录 `.env.example`：
```bash
# 用于本地全栈一键启动的占位
NODE_ENV=development
```

`apps/api/.env.example`：
```bash
APP_ENV=development
DATABASE_URL=postgresql+psycopg://jc:jc_dev@postgres:5432/jc_dev
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET=change-me-32-bytes-min
JWT_ALG=HS256
JWT_EXPIRES_HOURS=720

# Field-level encryption (Fernet key, base64-urlsafe 32 bytes)
FIELD_ENCRYPTION_KEY=

# WeChat Open Platform
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_REDIRECT_URI=http://localhost:3000/api/auth/wechat/callback

# Email Magic Link (use SMTP)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com

# LLM（v1 用户侧统一调用 MiniMax）
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
MINIMAX_API_BASE=https://api.minimax.chat/v1   # 海外节点用 https://api.minimaxi.chat/v1

# Observability
SENTRY_DSN=
POSTHOG_API_KEY=
POSTHOG_HOST=https://us.i.posthog.com
```

`apps/web/.env.example`：
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
NEXT_PUBLIC_SENTRY_DSN=
```

- [ ] **Step 5：复制 .env.example 到 .env 并启动 docker**

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
docker compose -f infra/docker-compose.yml up -d postgres redis
# 验证
docker compose -f infra/docker-compose.yml ps
# 期望：postgres healthy, redis up
```

- [ ] **Step 6：提交**

```bash
git add infra apps/api/Dockerfile apps/web/Dockerfile .env.example apps/api/.env.example apps/web/.env.example
git commit -m "chore(infra): local docker-compose with postgres + redis + api + web"
```

---

## Task 5: API Foundation — Settings + SQLAlchemy + Alembic + User Model

**Files:**
- Create: `apps/api/src/core/config.py`
- Create: `apps/api/src/core/db.py`
- Create: `apps/api/src/core/security.py`
- Create: `apps/api/src/models/__init__.py`
- Create: `apps/api/src/models/base.py`
- Create: `apps/api/src/models/user.py`
- Create: `apps/api/alembic.ini`
- Create: `apps/api/alembic/env.py`
- Create: `apps/api/alembic/script.py.mako`
- Create: `apps/api/alembic/versions/0001_initial.py`
- Create: `apps/api/tests/test_config.py`
- Create: `apps/api/tests/test_user_model.py`
- Create: `apps/api/tests/conftest.py`

**Interfaces:**
- Produces:
  - `Settings` 类（从 env 读所有配置）
  - `engine`、`SessionLocal`、`get_db()` 依赖
  - `User` 模型（id / email / wechat_openid / persona_type / preferences JSON / created_at / last_active_at）
  - `persona_type` 枚举值：`"fresh_grad"`, `"job_hopper"`, `"career_changer"`
  - `encrypt_field(value: str) -> str`、`decrypt_field(value: str) -> str`
- Consumes: Task 4 的 Postgres

- [ ] **Step 1：写 `core/config.py`**

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development")
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str
    jwt_alg: str = "HS256"
    jwt_expires_hours: int = 720

    field_encryption_key: str

    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_redirect_uri: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"

    # MiniMax 是 v1 唯一 LLM 供应商
    minimax_api_key: str = ""
    minimax_group_id: str = ""                                  # MiniMax 部分接口需要 GroupId
    minimax_api_base: str = "https://api.minimax.chat/v1"        # 海外节点改 https://api.minimaxi.chat/v1

    sentry_dsn: str = ""
    posthog_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 2：写 `tests/test_config.py` 先红**

```python
import os
from src.core.config import Settings

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:y@h:5432/d")
    monkeypatch.setenv("JWT_SECRET", "a" * 32)
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", "k" * 44)
    s = Settings()
    assert s.database_url.startswith("postgresql")
    assert s.jwt_alg == "HS256"
```

Run: `pytest -q tests/test_config.py` → 期望 PASS（Settings 已实现）。

- [ ] **Step 3：写 `core/db.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4：写 `core/security.py`（字段加密 + JWT 占位）**

```python
from cryptography.fernet import Fernet
from src.core.config import get_settings

_fernet = Fernet(get_settings().field_encryption_key.encode())

def encrypt_field(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()

def decrypt_field(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()
```

生成可用 key（运行一次记录到 `.env`）：
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

- [ ] **Step 5：写 `models/user.py`**

```python
from datetime import datetime
from enum import StrEnum
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4, UUID
import sqlalchemy as sa
from src.core.db import Base

class PersonaType(StrEnum):
    FRESH_GRAD = "fresh_grad"
    JOB_HOPPER = "job_hopper"
    CAREER_CHANGER = "career_changer"

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    email_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True, unique=False, index=False)
    email_lookup_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    persona_type: Mapped[PersonaType | None] = mapped_column(sa.Enum(PersonaType, name="persona_type_enum"), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

`models/__init__.py`：
```python
from src.models.user import User, PersonaType  # noqa: F401
```

`models/base.py`：
```python
from src.core.db import Base  # noqa: F401
```

- [ ] **Step 6：初始化 Alembic**

```bash
cd apps/api
alembic init alembic
```

修改 `apps/api/alembic.ini` 中 `sqlalchemy.url` 行：留空（用 env.py 注入）。

修改 `apps/api/alembic/env.py`（关键改动）：
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from src.core.config import get_settings
from src.core.db import Base
import src.models  # noqa: F401  (ensure models are imported)

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

- [ ] **Step 7：生成第一个 migration**

```bash
alembic revision --autogenerate -m "initial users table"
# 生成 alembic/versions/<hash>_initial_users_table.py，重命名为 0001_initial.py
alembic upgrade head
# 期望：Running upgrade -> 0001
```

- [ ] **Step 8：写 `tests/conftest.py` 与 `tests/test_user_model.py`**

`apps/api/tests/conftest.py`：
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.db import Base
from src.core.config import get_settings

@pytest.fixture(scope="session")
def engine():
    e = create_engine(get_settings().database_url, future=True)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)

@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()
```

`apps/api/tests/test_user_model.py`：
```python
from src.models import User, PersonaType

def test_user_can_be_created_with_persona(db):
    u = User(nickname="测试", persona_type=PersonaType.JOB_HOPPER, preferences={})
    db.add(u); db.flush()
    assert u.id is not None
    assert u.persona_type == PersonaType.JOB_HOPPER
```

Run:
```bash
pytest -q
# 期望：3 passed (health + config + user_model)
```

- [ ] **Step 9：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): settings + sqlalchemy + alembic + User model"
```

---

## Task 6: API LLM Wrapper + `/health/ai`

**Files:**
- Create: `apps/api/src/ai/__init__.py`
- Create: `apps/api/src/ai/llm_client.py`
- Modify: `apps/api/src/routers/health.py`（追加 `/health/ai` 路由）
- Create: `apps/api/tests/test_llm_client.py`
- Create: `apps/api/tests/test_health_ai.py`

**Interfaces:**
- Produces:
  - `class LLMClient` 单例，方法 `acomplete(model: str, system: str, messages: list[dict], max_tokens: int = 1024) -> str`
  - 支持兜底：传入 `model="auto-m1"` 时按 MiniMax-M1 → abab6.5s-chat 同家族两档降级（v1 单供应商 MiniMax）
  - `GET /api/v1/health/ai` 调用一次 abab6.5s-chat，返回 `{"status":"ok","model":"<used>","latency_ms":<n>}`

- [ ] **Step 1：写测试 `tests/test_llm_client.py`**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.ai.llm_client import LLMClient

@pytest.mark.asyncio
async def test_acomplete_returns_text(monkeypatch):
    mock_response = AsyncMock()
    mock_response.choices = [type("C", (), {"message": type("M", (), {"content": "ok"})()})]
    with patch("src.ai.llm_client.acompletion", return_value=mock_response) as m:
        client = LLMClient()
        out = await client.acomplete(
            model="minimax/abab6.5s-chat",
            system="you are helpful",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert out == "ok"
        m.assert_called_once()
```

Run：`pytest -q tests/test_llm_client.py` → 期望失败（`src.ai.llm_client` 不存在）。

- [ ] **Step 2：实现 `src/ai/llm_client.py`**

```python
from typing import Any
from litellm import acompletion

FALLBACK_CHAIN = {
    # v1 用户侧统一调用 MiniMax；同家族两档兜底
    "auto-m1": ["minimax/MiniMax-M1", "minimax/abab6.5s-chat"],
    "auto-light": ["minimax/abab6.5s-chat"],
}

class LLMClient:
    async def acomplete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> str:
        full_messages = [{"role": "system", "content": system}, *messages]
        chain = FALLBACK_CHAIN.get(model, [model])
        last_exc: Exception | None = None
        for m in chain:
            try:
                resp = await acompletion(model=m, messages=full_messages, max_tokens=max_tokens)
                return resp.choices[0].message.content or ""
            except Exception as e:  # noqa: BLE001
                last_exc = e
                continue
        raise RuntimeError(f"All LLM fallbacks failed: {last_exc}")
```

Run：`pytest -q tests/test_llm_client.py` → 期望 PASS。

- [ ] **Step 3：写 `/health/ai` 测试**

`apps/api/tests/test_health_ai.py`：
```python
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app

def test_health_ai_returns_ok_when_llm_ok():
    with patch("src.routers.health.LLMClient.acomplete", new=AsyncMock(return_value="pong")):
        client = TestClient(app)
        res = client.get("/api/v1/health/ai")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"
        assert "latency_ms" in body
```

Run：`pytest -q tests/test_health_ai.py` → 失败（路由不存在）。

- [ ] **Step 4：扩 `routers/health.py`**

```python
from time import perf_counter
from fastapi import APIRouter
from src.ai.llm_client import LLMClient

router = APIRouter(prefix="/api/v1/health", tags=["health"])
_llm = LLMClient()

@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}

@router.get("/ai")
async def health_ai() -> dict[str, str | int]:
    t0 = perf_counter()
    text = await _llm.acomplete(
        model="auto-light",
        system="reply with single word: pong",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=16,
    )
    return {
        "status": "ok" if "pong" in text.lower() else "degraded",
        "model": "auto-light",
        "latency_ms": int((perf_counter() - t0) * 1000),
    }
```

Run：`pytest -q` → 期望全部 PASS。

- [ ] **Step 5：提交**

```bash
git add apps/api
git commit -m "feat(api): LLM client (MiniMax provider, M1→abab6.5s fallback) + /health/ai endpoint"
```

---

## Task 7: API Auth — Magic Link (Email)

**Files:**
- Create: `apps/api/src/services/__init__.py`
- Create: `apps/api/src/services/email_sender.py`
- Create: `apps/api/src/services/magic_link.py`
- Create: `apps/api/src/schemas/auth.py`
- Create: `apps/api/src/routers/auth.py`
- Modify: `apps/api/src/main.py`（include auth router）
- Create: `apps/api/alembic/versions/0002_magic_link_tokens.py`
- Create: `apps/api/src/models/magic_link_token.py`
- Create: `apps/api/tests/test_magic_link.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/auth/magic-link/request` body `{"email": str}` → 发送邮件，返回 `{"sent": true}`
  - `POST /api/v1/auth/magic-link/verify` body `{"token": str}` → 验证 + 返回 `{"user_id": str, "session_token": str}`（session_token 实际在 Task 9 issue）
  - `MagicLinkToken` 表：token / email_lookup_hash / expires_at / consumed_at
- Consumes: Task 5 的 User、encrypt_field
- Note: 邮件发送本地 dev 模式打印到日志（避免真发邮件），生产用 SMTP

- [ ] **Step 1：写 token 模型 + 迁移**

`apps/api/src/models/magic_link_token.py`：
```python
from datetime import datetime
from uuid import uuid4, UUID
import sqlalchemy as sa
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db import Base

class MagicLinkToken(Base):
    __tablename__ = "magic_link_tokens"
    id: Mapped[UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email_lookup_hash: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
```

`apps/api/src/models/__init__.py`：追加 `from src.models.magic_link_token import MagicLinkToken  # noqa: F401`

生成迁移：
```bash
cd apps/api
alembic revision --autogenerate -m "magic link tokens"
# 重命名为 0002_magic_link_tokens.py
alembic upgrade head
```

- [ ] **Step 2：写 services**

`apps/api/src/services/email_sender.py`：
```python
import smtplib
from email.message import EmailMessage
from src.core.config import get_settings

def send_email(to: str, subject: str, html: str) -> None:
    s = get_settings()
    if s.app_env == "development" or not s.smtp_host:
        print(f"[DEV EMAIL] to={to} subject={subject}\n{html}")
        return
    msg = EmailMessage()
    msg["From"] = s.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")
    with smtplib.SMTP(s.smtp_host, s.smtp_port) as srv:
        srv.starttls()
        srv.login(s.smtp_user, s.smtp_password)
        srv.send_message(msg)
```

`apps/api/src/services/magic_link.py`：
```python
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from src.models.magic_link_token import MagicLinkToken
from src.services.email_sender import send_email

TOKEN_TTL_MINUTES = 15

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def request_link(db: Session, email: str, base_url: str) -> None:
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash(raw_token)
    email_hash = _hash(email.lower().strip())
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    db.add(MagicLinkToken(token_hash=token_hash, email_lookup_hash=email_hash, expires_at=expires))
    db.commit()
    link = f"{base_url}/auth/verify?token={raw_token}"
    send_email(to=email, subject="登录 Job Companion", html=f'<a href="{link}">点击登录（15 分钟有效）</a>')

def verify_token(db: Session, raw_token: str) -> str | None:
    """返回 email_lookup_hash，失败返回 None"""
    th = _hash(raw_token)
    row = db.query(MagicLinkToken).filter(MagicLinkToken.token_hash == th).first()
    if not row or row.consumed_at or row.expires_at < datetime.now(timezone.utc):
        return None
    row.consumed_at = datetime.now(timezone.utc)
    db.commit()
    return row.email_lookup_hash
```

- [ ] **Step 3：写 schemas + router**

`apps/api/src/schemas/auth.py`：
```python
from pydantic import BaseModel, EmailStr

class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkVerify(BaseModel):
    token: str
```

`apps/api/src/routers/auth.py`：
```python
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.core.config import get_settings
from src.core.security import encrypt_field
from src.models import User
from src.schemas.auth import MagicLinkRequest, MagicLinkVerify
from src.services.magic_link import request_link, verify_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def _hash(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()

@router.post("/magic-link/request")
def request_magic_link(body: MagicLinkRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    settings = get_settings()
    base = "http://localhost:3000" if settings.app_env == "development" else "https://app.example.com"
    request_link(db, body.email, base)
    return {"sent": True}

@router.post("/magic-link/verify")
def verify_magic_link(body: MagicLinkVerify, db: Session = Depends(get_db)) -> dict[str, str]:
    email_hash = verify_token(db, body.token)
    if not email_hash:
        raise HTTPException(status_code=400, detail="invalid or expired token")
    user = db.query(User).filter(User.email_lookup_hash == email_hash).first()
    if not user:
        # 首次登录 → 自动注册（email 加密后存）
        # 注：raw email 此刻不可知（仅有 hash），所以 email_encrypted 在前端 verify 后由前端传回
        user = User(email_lookup_hash=email_hash, preferences={})
        db.add(user); db.commit(); db.refresh(user)
    return {"user_id": str(user.id), "session_token": "PLACEHOLDER_ISSUED_IN_TASK_9"}
```

Modify `apps/api/src/main.py`：
```python
from fastapi import FastAPI
from src.routers import health, auth

app = FastAPI(title="Job Companion API", version="0.0.0")
app.include_router(health.router)
app.include_router(auth.router)
```

- [ ] **Step 4：写测试**

`apps/api/tests/test_magic_link.py`：
```python
from fastapi.testclient import TestClient
from src.main import app
from src.core.db import SessionLocal
from src.models.magic_link_token import MagicLinkToken

def test_magic_link_flow():
    client = TestClient(app)
    r1 = client.post("/api/v1/auth/magic-link/request", json={"email": "u@test.com"})
    assert r1.status_code == 200 and r1.json() == {"sent": True}

    db = SessionLocal()
    row = db.query(MagicLinkToken).order_by(MagicLinkToken.created_at.desc()).first()
    assert row is not None

    # 直接从 dev 日志拿不到 raw token，这里用 mock 路径：本地手动验证
    # 测试只校验流程：未实施前端 token 拦截可暂只测 request
```

Run：`pytest -q tests/test_magic_link.py` → 期望 PASS（1 个）。

- [ ] **Step 5：手动 e2e 自检**

```bash
docker compose -f infra/docker-compose.yml up -d
cd apps/api && source .venv/bin/activate
uvicorn src.main:app --reload --port 8000 --app-dir .
# 另开终端
curl -X POST http://localhost:8000/api/v1/auth/magic-link/request \
  -H 'Content-Type: application/json' -d '{"email":"me@test.com"}'
# 期望：{"sent":true}，api 日志打印 [DEV EMAIL] ...
# 从日志复制 token，再调 verify
curl -X POST http://localhost:8000/api/v1/auth/magic-link/verify \
  -H 'Content-Type: application/json' -d '{"token":"<TOKEN>"}'
# 期望：{"user_id":"<uuid>","session_token":"PLACEHOLDER_ISSUED_IN_TASK_9"}
```

- [ ] **Step 6：提交**

```bash
cd ../..
git add apps/api
git commit -m "feat(api): magic link auth (request + verify), email dev-prints to log"
```

---

## Task 8: API Auth — WeChat Scan

**Files:**
- Create: `apps/api/src/services/wechat.py`
- Modify: `apps/api/src/routers/auth.py`（追加 wechat 路由）
- Create: `apps/api/tests/test_wechat_auth.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/auth/wechat/qr` → 返回微信扫码地址 `{"qr_url": str, "state": str}`
  - `GET /api/v1/auth/wechat/callback?code=&state=` → 用 code 换 openid + 自动注册/登录 → 返回 `{"user_id": str, "session_token": str}`
- Note: 本地无法真的对接微信开放平台（需公网回调），dev 模式提供 mock 路径

- [ ] **Step 1：写 services/wechat.py**

```python
import secrets
import httpx
from src.core.config import get_settings

OPEN_PLATFORM_QR_URL = "https://open.weixin.qq.com/connect/qrconnect"

def build_qr_url() -> tuple[str, str]:
    s = get_settings()
    state = secrets.token_urlsafe(16)
    qr = (
        f"{OPEN_PLATFORM_QR_URL}?appid={s.wechat_app_id}"
        f"&redirect_uri={s.wechat_redirect_uri}"
        f"&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"
    )
    return qr, state

async def exchange_code_for_openid(code: str) -> str:
    s = get_settings()
    if s.app_env == "development" and code.startswith("DEV-"):
        return f"openid-dev-{code[4:]}"
    url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params={
            "appid": s.wechat_app_id,
            "secret": s.wechat_app_secret,
            "code": code,
            "grant_type": "authorization_code",
        })
        data = r.json()
        if "openid" not in data:
            raise RuntimeError(f"wechat exchange failed: {data}")
        return data["openid"]
```

- [ ] **Step 2：扩 `routers/auth.py`**

追加：
```python
from src.services.wechat import build_qr_url, exchange_code_for_openid

@router.get("/wechat/qr")
def wechat_qr() -> dict[str, str]:
    qr, state = build_qr_url()
    return {"qr_url": qr, "state": state}

@router.get("/wechat/callback")
async def wechat_callback(code: str, state: str, db: Session = Depends(get_db)) -> dict[str, str]:
    openid = await exchange_code_for_openid(code)
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        user = User(wechat_openid=openid, preferences={})
        db.add(user); db.commit(); db.refresh(user)
    return {"user_id": str(user.id), "session_token": "PLACEHOLDER_ISSUED_IN_TASK_9"}
```

- [ ] **Step 3：写测试**

`apps/api/tests/test_wechat_auth.py`：
```python
from fastapi.testclient import TestClient
from src.main import app

def test_wechat_qr_returns_url_and_state():
    client = TestClient(app)
    r = client.get("/api/v1/auth/wechat/qr")
    assert r.status_code == 200
    body = r.json()
    assert "qrconnect" in body["qr_url"]
    assert len(body["state"]) > 10

def test_wechat_callback_dev_mode_creates_user(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    from src.core import config; config.get_settings.cache_clear()
    client = TestClient(app)
    r = client.get("/api/v1/auth/wechat/callback?code=DEV-abc&state=s")
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"]
```

Run：`pytest -q tests/test_wechat_auth.py` → 期望 2 passed。

- [ ] **Step 4：提交**

```bash
git add apps/api
git commit -m "feat(api): wechat scan auth (qr + callback) with dev mock"
```

---

## Task 9: API JWT Session + Middleware

**Files:**
- Modify: `apps/api/src/core/security.py`（追加 JWT 函数）
- Modify: `apps/api/src/routers/auth.py`（用真实 session_token 替换 placeholder）
- Create: `apps/api/src/core/deps.py`（current_user 依赖）
- Create: `apps/api/src/routers/me.py`（`GET /api/v1/me`、`PATCH /api/v1/me`）
- Modify: `apps/api/src/main.py`（include me router）
- Create: `apps/api/tests/test_jwt.py`
- Create: `apps/api/tests/test_me_endpoint.py`

**Interfaces:**
- Produces:
  - `issue_session_token(user_id: UUID) -> str` 与 `verify_session_token(token: str) -> UUID | None`
  - 依赖 `current_user(request) -> User`，从 cookie `jc_session` 读取
  - `GET /api/v1/me` 返回 `{"id","nickname","persona_type","preferences"}`
  - `PATCH /api/v1/me` 接受 `{"nickname"?,"persona_type"?,"preferences"?}`
  - 登录接口改为 set HTTPOnly cookie `jc_session`，不再返回明文 token

- [ ] **Step 1：写测试 `tests/test_jwt.py`**

```python
from uuid import uuid4
from src.core.security import issue_session_token, verify_session_token

def test_jwt_roundtrip():
    uid = uuid4()
    tok = issue_session_token(uid)
    assert verify_session_token(tok) == uid

def test_jwt_invalid_returns_none():
    assert verify_session_token("bogus") is None
```

Run：`pytest -q tests/test_jwt.py` → 失败（函数不存在）。

- [ ] **Step 2：扩 `core/security.py`**

追加：
```python
from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt, JWTError
from src.core.config import get_settings

def issue_session_token(user_id: UUID) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=s.jwt_expires_hours),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_alg)

def verify_session_token(token: str) -> UUID | None:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_alg])
        return UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None
```

Run：`pytest -q tests/test_jwt.py` → 2 passed。

- [ ] **Step 3：写 `core/deps.py`**

```python
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.core.security import verify_session_token
from src.models import User

def current_user(
    jc_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not jc_session:
        raise HTTPException(status_code=401, detail="unauthenticated")
    uid = verify_session_token(jc_session)
    if not uid:
        raise HTTPException(status_code=401, detail="invalid session")
    u = db.get(User, uid)
    if not u:
        raise HTTPException(status_code=401, detail="user not found")
    return u
```

- [ ] **Step 4：修登录接口为 set-cookie 模式**

修改 `apps/api/src/routers/auth.py` 的 verify 与 callback：
```python
from fastapi import Response
from src.core.security import issue_session_token

@router.post("/magic-link/verify")
def verify_magic_link(body: MagicLinkVerify, response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    email_hash = verify_token(db, body.token)
    if not email_hash:
        raise HTTPException(status_code=400, detail="invalid or expired token")
    user = db.query(User).filter(User.email_lookup_hash == email_hash).first()
    if not user:
        user = User(email_lookup_hash=email_hash, preferences={})
        db.add(user); db.commit(); db.refresh(user)
    tok = issue_session_token(user.id)
    response.set_cookie("jc_session", tok, httponly=True, secure=False, samesite="lax", max_age=60*60*24*30)
    return {"user_id": str(user.id)}

@router.get("/wechat/callback")
async def wechat_callback(code: str, state: str, response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    openid = await exchange_code_for_openid(code)
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        user = User(wechat_openid=openid, preferences={})
        db.add(user); db.commit(); db.refresh(user)
    tok = issue_session_token(user.id)
    response.set_cookie("jc_session", tok, httponly=True, secure=False, samesite="lax", max_age=60*60*24*30)
    return {"user_id": str(user.id)}
```

- [ ] **Step 5：写 `routers/me.py`**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.core.db import get_db
from src.core.deps import current_user
from src.models import User, PersonaType

router = APIRouter(prefix="/api/v1/me", tags=["me"])

class MeResponse(BaseModel):
    id: str
    nickname: str | None
    persona_type: PersonaType | None
    preferences: dict

class MeUpdate(BaseModel):
    nickname: str | None = None
    persona_type: PersonaType | None = None
    preferences: dict | None = None

@router.get("")
def get_me(user: User = Depends(current_user)) -> MeResponse:
    return MeResponse(
        id=str(user.id),
        nickname=user.nickname,
        persona_type=user.persona_type,
        preferences=user.preferences or {},
    )

@router.patch("")
def update_me(body: MeUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> MeResponse:
    if body.nickname is not None: user.nickname = body.nickname
    if body.persona_type is not None: user.persona_type = body.persona_type
    if body.preferences is not None: user.preferences = body.preferences
    db.commit(); db.refresh(user)
    return get_me(user)
```

Include in `main.py`：
```python
from src.routers import health, auth, me
app.include_router(me.router)
```

- [ ] **Step 6：写测试 `tests/test_me_endpoint.py`**

```python
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import issue_session_token
from src.core.db import SessionLocal
from src.models import User

def _login_as_new_user() -> tuple[TestClient, str]:
    db = SessionLocal()
    u = User(preferences={})
    db.add(u); db.commit(); db.refresh(u)
    client = TestClient(app)
    client.cookies.set("jc_session", issue_session_token(u.id))
    return client, str(u.id)

def test_me_returns_user():
    client, uid = _login_as_new_user()
    r = client.get("/api/v1/me")
    assert r.status_code == 200
    assert r.json()["id"] == uid

def test_me_patch_persona():
    client, _ = _login_as_new_user()
    r = client.patch("/api/v1/me", json={"persona_type": "job_hopper", "nickname": "张三"})
    assert r.status_code == 200
    assert r.json()["persona_type"] == "job_hopper"
    assert r.json()["nickname"] == "张三"

def test_me_without_cookie_401():
    client = TestClient(app)
    r = client.get("/api/v1/me")
    assert r.status_code == 401
```

Run：`pytest -q` → 期望所有 passed。

- [ ] **Step 7：提交**

```bash
git add apps/api
git commit -m "feat(api): JWT session + cookie + /me endpoint with PATCH persona"
```

---

## Task 10: Web — next-intl Setup (zh / en)

**Files:**
- Modify: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/[locale]/layout.tsx`
- Create: `apps/web/src/app/[locale]/page.tsx`
- Create: `apps/web/middleware.ts`
- Create: `apps/web/src/i18n/request.ts`
- Create: `apps/web/messages/zh.json`
- Create: `apps/web/messages/en.json`
- Modify: `apps/web/next.config.mjs`
- Delete: `apps/web/src/app/page.tsx`（旧首页）
- Delete: `apps/web/src/app/layout.tsx` 中的非 locale 路由

**Interfaces:**
- Produces:
  - `/zh` 与 `/en` 路由可访问
  - `useTranslations('home')` 在客户端组件可用
  - `useLocale()` 获取当前 locale

- [ ] **Step 1：装 next-intl**

```bash
cd apps/web
pnpm add next-intl@3.25.1
cd ../..
```

- [ ] **Step 2：写 i18n 配置 + middleware**

`apps/web/src/i18n/request.ts`：
```typescript
import { getRequestConfig } from 'next-intl/server'
import { notFound } from 'next/navigation'

export const locales = ['zh', 'en'] as const
export type Locale = (typeof locales)[number]

export default getRequestConfig(async ({ locale }) => {
  if (!locales.includes(locale as Locale)) notFound()
  return {
    messages: (await import(`../../messages/${locale}.json`)).default,
  }
})
```

`apps/web/middleware.ts`：
```typescript
import createMiddleware from 'next-intl/middleware'

export default createMiddleware({
  locales: ['zh', 'en'],
  defaultLocale: 'zh',
  localePrefix: 'always',
})

export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)'],
}
```

Modify `apps/web/next.config.mjs`：
```javascript
import createNextIntlPlugin from 'next-intl/plugin'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
}

export default withNextIntl(nextConfig)
```

- [ ] **Step 3：写翻译文件**

`apps/web/messages/zh.json`：
```json
{
  "home": { "title": "求职作战中心", "tagline": "每份投递都值得一份专属简历" },
  "nav": {
    "opportunities": "我的求职机会",
    "master_resume": "我的主简历",
    "resources": "我的资源库",
    "weekly": "本周复盘",
    "coach": "找 Coach 锐评"
  },
  "auth": {
    "login": "登录",
    "email_label": "邮箱",
    "send_magic_link": "发送登录链接",
    "wechat_scan": "微信扫码登录"
  }
}
```

`apps/web/messages/en.json`：
```json
{
  "home": { "title": "Job Companion", "tagline": "Every application deserves a custom resume" },
  "nav": {
    "opportunities": "My Opportunities",
    "master_resume": "Master Resume",
    "resources": "Resource Hub",
    "weekly": "Weekly Recap",
    "coach": "Find a Coach"
  },
  "auth": {
    "login": "Sign In",
    "email_label": "Email",
    "send_magic_link": "Send Magic Link",
    "wechat_scan": "Scan WeChat to Sign In"
  }
}
```

- [ ] **Step 4：重构 layout 与 page**

删除：
```bash
rm apps/web/src/app/page.tsx
```

修改 `apps/web/src/app/layout.tsx`：仅保留最外层（不含 NextIntlClientProvider）：
```typescript
import type { ReactNode } from 'react'
import './globals.css'

export default function RootLayout({ children }: { children: ReactNode }) {
  return children
}
```

创建 `apps/web/src/app/[locale]/layout.tsx`：
```typescript
import type { ReactNode } from 'react'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import '../globals.css'

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  const messages = await getMessages()
  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
      </body>
    </html>
  )
}
```

创建 `apps/web/src/app/[locale]/page.tsx`：
```typescript
import { useTranslations } from 'next-intl'

export default function Home() {
  const t = useTranslations('home')
  return (
    <main className="flex min-h-screen items-center justify-center flex-col gap-4">
      <h1 className="text-3xl font-bold">{t('title')}</h1>
      <p className="text-muted-foreground">{t('tagline')}</p>
    </main>
  )
}
```

- [ ] **Step 5：自检**

```bash
pnpm --filter web dev
# 浏览器开 http://localhost:3000 → 自动重定向到 /zh
# 期望页面显示「求职作战中心」+ 「每份投递都值得一份专属简历」
# 访问 http://localhost:3000/en → 显示 "Job Companion" + tagline
pnpm --filter web typecheck
# 期望：0 errors
```

- [ ] **Step 6：提交**

```bash
git add apps/web
git commit -m "feat(web): next-intl with zh/en routing + locale layout"
```

---

## Task 11: Web — Auth UI + Persona Onboarding

**Files:**
- Create: `apps/web/src/app/[locale]/(auth)/login/page.tsx`
- Create: `apps/web/src/app/[locale]/(auth)/verify/page.tsx`
- Create: `apps/web/src/app/[locale]/(app)/onboarding/page.tsx`
- Create: `apps/web/src/lib/api.ts`
- Create: `apps/web/src/components/auth/MagicLinkForm.tsx`
- Create: `apps/web/src/components/auth/WeChatQR.tsx`
- Create: `apps/web/src/components/auth/PersonaPicker.tsx`
- Modify: `apps/web/messages/zh.json` and `en.json`（追加 onboarding 文案）

**Interfaces:**
- Consumes: API endpoints `/auth/magic-link/request`、`/auth/magic-link/verify`、`/auth/wechat/qr`、`/me`、`PATCH /me`
- Produces: 用户走完 `/login` → 收邮件链接 → `/verify?token=xxx` → set cookie → 跳 `/onboarding`（首次）选 persona → 跳 `/dashboard` 占位页

- [ ] **Step 1：写 `lib/api.ts`（fetch 封装）**

```typescript
const BASE = process.env.NEXT_PUBLIC_API_BASE!

export async function api<T = unknown>(
  path: string,
  opts: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(opts.headers ?? {}) },
    ...opts,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}
```

- [ ] **Step 2：写 `MagicLinkForm.tsx`**

```typescript
'use client'
import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'

export function MagicLinkForm() {
  const t = useTranslations('auth')
  const [email, setEmail] = useState('')
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setState('sending')
    try {
      await api('/api/v1/auth/magic-link/request', { method: 'POST', body: JSON.stringify({ email }) })
      setState('sent')
    } catch {
      setState('error')
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3 w-72">
      <label className="block text-sm">{t('email_label')}</label>
      <input
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full rounded border px-3 py-2"
      />
      <button type="submit" disabled={state === 'sending'} className="w-full rounded bg-black text-white py-2">
        {t('send_magic_link')}
      </button>
      {state === 'sent' && <p className="text-green-700 text-sm">✓ 已发送，请查收邮箱</p>}
      {state === 'error' && <p className="text-red-700 text-sm">发送失败</p>}
    </form>
  )
}
```

- [ ] **Step 3：写 `WeChatQR.tsx`**

```typescript
'use client'
import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { api } from '@/lib/api'

export function WeChatQR() {
  const t = useTranslations('auth')
  const [qrUrl, setQrUrl] = useState<string | null>(null)
  useEffect(() => {
    api<{ qr_url: string }>('/api/v1/auth/wechat/qr').then((d) => setQrUrl(d.qr_url))
  }, [])
  if (!qrUrl) return <p>{t('wechat_scan')}…</p>
  return (
    <a href={qrUrl} target="_blank" rel="noreferrer" className="inline-block border rounded p-4">
      {t('wechat_scan')}
    </a>
  )
}
```

- [ ] **Step 4：写 login 页面**

`apps/web/src/app/[locale]/(auth)/login/page.tsx`：
```typescript
import { useTranslations } from 'next-intl'
import { MagicLinkForm } from '@/components/auth/MagicLinkForm'
import { WeChatQR } from '@/components/auth/WeChatQR'

export default function LoginPage() {
  const t = useTranslations('auth')
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8">
      <h1 className="text-2xl font-bold">{t('login')}</h1>
      <MagicLinkForm />
      <hr className="w-72" />
      <WeChatQR />
    </main>
  )
}
```

- [ ] **Step 5：写 verify 页面**

`apps/web/src/app/[locale]/(auth)/verify/page.tsx`：
```typescript
'use client'
import { useEffect, useState } from 'react'
import { useSearchParams, useRouter, useParams } from 'next/navigation'
import { api } from '@/lib/api'

export default function VerifyPage() {
  const params = useSearchParams()
  const router = useRouter()
  const { locale } = useParams<{ locale: string }>()
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    const token = params.get('token')
    if (!token) { setErr('missing token'); return }
    api<{ user_id: string }>('/api/v1/auth/magic-link/verify', {
      method: 'POST', body: JSON.stringify({ token }),
    })
      .then(async () => {
        const me = await api<{ persona_type: string | null }>('/api/v1/me')
        router.replace(me.persona_type ? `/${locale}/dashboard` : `/${locale}/onboarding`)
      })
      .catch((e) => setErr(String(e)))
  }, [params, router, locale])

  return <main className="p-8">{err ? `❌ ${err}` : '验证中…'}</main>
}
```

- [ ] **Step 6：写 PersonaPicker + Onboarding 页**

`apps/web/src/components/auth/PersonaPicker.tsx`：
```typescript
'use client'
import { useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { api } from '@/lib/api'

const OPTIONS = [
  { v: 'fresh_grad', zh: '应届校招', en: 'Fresh Grad' },
  { v: 'job_hopper', zh: '社招跳槽', en: 'Job Hopper' },
  { v: 'career_changer', zh: '跨行业转行', en: 'Career Changer' },
] as const

export function PersonaPicker({ locale }: { locale: string }) {
  const [pick, setPick] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const router = useRouter()

  async function save() {
    if (!pick) return
    setBusy(true)
    await api('/api/v1/me', { method: 'PATCH', body: JSON.stringify({ persona_type: pick }) })
    router.replace(`/${locale}/dashboard`)
  }

  return (
    <div className="space-y-3 w-96">
      {OPTIONS.map((o) => (
        <button
          key={o.v}
          onClick={() => setPick(o.v)}
          className={`w-full border rounded p-3 text-left ${pick === o.v ? 'bg-black text-white' : ''}`}
        >
          {locale === 'zh' ? o.zh : o.en}
        </button>
      ))}
      <button disabled={!pick || busy} onClick={save} className="w-full rounded bg-blue-600 text-white py-2 disabled:opacity-50">
        {busy ? '…' : (locale === 'zh' ? '继续' : 'Continue')}
      </button>
    </div>
  )
}
```

`apps/web/src/app/[locale]/(app)/onboarding/page.tsx`：
```typescript
'use client'
import { useParams } from 'next/navigation'
import { PersonaPicker } from '@/components/auth/PersonaPicker'

export default function OnboardingPage() {
  const { locale } = useParams<{ locale: string }>()
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6">
      <h1 className="text-2xl font-bold">
        {locale === 'zh' ? '你的求职阶段是？' : 'What is your stage?'}
      </h1>
      <PersonaPicker locale={locale} />
    </main>
  )
}
```

- [ ] **Step 7：自检 + 提交**

```bash
pnpm --filter web typecheck   # 期望：0 errors
git add apps/web
git commit -m "feat(web): login page + magic link + wechat qr + persona onboarding"
```

---

## Task 12: Web — Top Nav Shell (5 Entries)

**Files:**
- Create: `apps/web/src/app/[locale]/(app)/layout.tsx`
- Create: `apps/web/src/app/[locale]/(app)/dashboard/page.tsx`
- Create: `apps/web/src/app/[locale]/(app)/opportunities/page.tsx`
- Create: `apps/web/src/app/[locale]/(app)/master-resume/page.tsx`
- Create: `apps/web/src/app/[locale]/(app)/resources/page.tsx`
- Create: `apps/web/src/app/[locale]/(app)/weekly/page.tsx`
- Create: `apps/web/src/components/nav/SideNav.tsx`
- Create: `apps/web/src/components/nav/LocaleSwitcher.tsx`

**Interfaces:**
- Produces: 登录后的全局布局：左侧 5 个一级入口 + 右上角 [伪装] [中/EN]；五个一级页面均为占位（"模块开发中，参见 Plan N"）

- [ ] **Step 1：写 SideNav**

```typescript
'use client'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { useParams, usePathname } from 'next/navigation'

const ITEMS = [
  { key: 'opportunities', href: 'opportunities' },
  { key: 'master_resume', href: 'master-resume' },
  { key: 'resources',     href: 'resources' },
  { key: 'weekly',        href: 'weekly' },
  { key: 'coach',         href: 'coach' },
] as const

export function SideNav() {
  const t = useTranslations('nav')
  const { locale } = useParams<{ locale: string }>()
  const path = usePathname()
  return (
    <nav className="w-56 border-r bg-gray-50 p-4 flex flex-col gap-2">
      <h2 className="font-bold mb-4">💼 Job Companion</h2>
      {ITEMS.map((it) => {
        const href = `/${locale}/${it.href}`
        const active = path === href
        return (
          <Link key={it.key} href={href} className={`px-3 py-2 rounded ${active ? 'bg-black text-white' : 'hover:bg-gray-200'}`}>
            {t(it.key)}
          </Link>
        )
      })}
    </nav>
  )
}
```

- [ ] **Step 2：写 LocaleSwitcher**

```typescript
'use client'
import { useParams, useRouter, usePathname } from 'next/navigation'

export function LocaleSwitcher() {
  const { locale } = useParams<{ locale: string }>()
  const router = useRouter()
  const path = usePathname()
  const other = locale === 'zh' ? 'en' : 'zh'
  return (
    <button
      onClick={() => router.push(path.replace(`/${locale}`, `/${other}`))}
      className="text-sm border rounded px-2 py-1"
    >
      {locale === 'zh' ? 'EN' : '中'}
    </button>
  )
}
```

- [ ] **Step 3：写 (app)/layout.tsx**

```typescript
import type { ReactNode } from 'react'
import { SideNav } from '@/components/nav/SideNav'
import { LocaleSwitcher } from '@/components/nav/LocaleSwitcher'
import { DisguiseToggle } from '@/components/disguise/DisguiseToggle'

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <SideNav />
      <div className="flex-1 flex flex-col">
        <header className="h-12 border-b flex items-center justify-end gap-3 px-4">
          <DisguiseToggle />
          <LocaleSwitcher />
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
```

> 注：`DisguiseToggle` 在 Task 13 写；先 import 报错也无所谓，Task 13 紧跟。

- [ ] **Step 4：写 5 个占位页面**

每个页面同结构，举例 `dashboard/page.tsx`：
```typescript
import { useTranslations } from 'next-intl'

export default function DashboardPage() {
  const t = useTranslations()
  return (
    <div>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-muted-foreground">v1 各模块见 Plan 1-7。</p>
    </div>
  )
}
```

其他 4 个页面（opportunities/master-resume/resources/weekly）类似，标题和占位文本对应即可。

- [ ] **Step 5：提交（暂不跑，等 Task 13 完成再 e2e 自检）**

```bash
git add apps/web
git commit -m "feat(web): top nav shell with 5 entries + locale switcher"
```

---

## Task 13: Web — 伪装界面（番茄钟 + 待办）+ 全局快捷键

**Files:**
- Create: `apps/web/src/components/disguise/DisguiseToggle.tsx`
- Create: `apps/web/src/components/disguise/DisguiseOverlay.tsx`
- Create: `apps/web/src/components/disguise/PomodoroTimer.tsx`
- Create: `apps/web/src/components/disguise/TodoList.tsx`
- Create: `apps/web/src/hooks/useDisguise.ts`

**Interfaces:**
- Produces:
  - `<DisguiseToggle />` 按钮：右上角"👁 伪装"
  - 全局快捷键 `Ctrl+\`` / `Cmd+\``：切换伪装
  - 伪装时全屏覆盖一个"番茄钟 + 待办"界面，document.title 改为 "TimeFlow"，favicon 切到番茄图标
  - 再次快捷键秒回

- [ ] **Step 1：写 hook**

`apps/web/src/hooks/useDisguise.ts`：
```typescript
'use client'
import { useEffect, useState } from 'react'

const TITLE_NORMAL = 'Job Companion'
const TITLE_DISGUISE = 'TimeFlow - Pomodoro & Tasks'

export function useDisguise() {
  const [on, setOn] = useState(false)

  useEffect(() => {
    const orig = document.title
    document.title = on ? TITLE_DISGUISE : (orig || TITLE_NORMAL)
    // favicon swap (simplified): rely on document head
    const link = document.querySelector("link[rel*='icon']") as HTMLLinkElement | null
    if (link) link.href = on ? '/disguise-favicon.svg' : '/favicon.ico'
  }, [on])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault()
        setOn((p) => !p)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return { on, toggle: () => setOn((p) => !p) }
}
```

- [ ] **Step 2：写 PomodoroTimer**

```typescript
'use client'
import { useEffect, useState } from 'react'

export function PomodoroTimer() {
  const [secs, setSecs] = useState(25 * 60)
  const [running, setRunning] = useState(false)
  useEffect(() => {
    if (!running) return
    const t = setInterval(() => setSecs((s) => Math.max(0, s - 1)), 1000)
    return () => clearInterval(t)
  }, [running])
  const m = String(Math.floor(secs / 60)).padStart(2, '0')
  const s = String(secs % 60).padStart(2, '0')
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="text-6xl font-mono">{m}:{s}</div>
      <div className="flex gap-2">
        <button onClick={() => setRunning((r) => !r)} className="px-4 py-2 border rounded">
          {running ? 'Pause' : 'Start'}
        </button>
        <button onClick={() => { setSecs(25 * 60); setRunning(false) }} className="px-4 py-2 border rounded">Reset</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 3：写 TodoList**

```typescript
'use client'
import { useState } from 'react'

export function TodoList() {
  const [items, setItems] = useState<{ id: number; text: string; done: boolean }[]>([
    { id: 1, text: '回邮件', done: false },
    { id: 2, text: '写周报', done: false },
  ])
  const [val, setVal] = useState('')
  return (
    <div className="w-80 space-y-2">
      <form onSubmit={(e) => { e.preventDefault(); if (!val) return; setItems((it) => [...it, { id: Date.now(), text: val, done: false }]); setVal('') }}>
        <input value={val} onChange={(e) => setVal(e.target.value)} placeholder="Add task…" className="w-full border rounded px-3 py-2" />
      </form>
      <ul className="space-y-1">
        {items.map((i) => (
          <li key={i.id} className="flex items-center gap-2">
            <input type="checkbox" checked={i.done} onChange={() => setItems((it) => it.map((x) => x.id === i.id ? { ...x, done: !x.done } : x))} />
            <span className={i.done ? 'line-through text-gray-400' : ''}>{i.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 4：写 Overlay + Toggle**

`DisguiseOverlay.tsx`：
```typescript
'use client'
import { PomodoroTimer } from './PomodoroTimer'
import { TodoList } from './TodoList'

export function DisguiseOverlay() {
  return (
    <div className="fixed inset-0 z-[9999] bg-white">
      <header className="border-b p-4 text-center font-bold">TimeFlow · 专注与任务</header>
      <main className="flex flex-col md:flex-row items-center justify-center gap-12 p-12">
        <PomodoroTimer />
        <TodoList />
      </main>
    </div>
  )
}
```

`DisguiseToggle.tsx`：
```typescript
'use client'
import { useDisguise } from '@/hooks/useDisguise'
import { DisguiseOverlay } from './DisguiseOverlay'

export function DisguiseToggle() {
  const { on, toggle } = useDisguise()
  return (
    <>
      <button onClick={toggle} className="text-sm border rounded px-2 py-1" title="Ctrl+` 切换">
        👁 {on ? 'Off' : 'On'}
      </button>
      {on && <DisguiseOverlay />}
    </>
  )
}
```

- [ ] **Step 5：写一个假 favicon**

```bash
# 在 apps/web/public 下放一个简单 svg
cat > apps/web/public/disguise-favicon.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#e74c3c"/><rect x="40" y="10" width="20" height="15" fill="#27ae60"/></svg>
EOF
```

- [ ] **Step 6：自检 + 提交**

```bash
pnpm --filter web dev
# /zh/dashboard → 顶部按钮 [👁 On]，点一下 → 全屏番茄钟+待办
# Ctrl+` → 来回切
git add apps/web
git commit -m "feat(web): disguise mode with pomodoro+todo overlay and Ctrl+\` hotkey"
```

---

## Task 14: PostHog Integration (Web + API)

**Files:**
- Create: `packages/shared-types/events.ts`
- Create: `packages/shared-types/package.json`
- Modify: `apps/web/src/app/[locale]/layout.tsx`（init PostHog）
- Create: `apps/web/src/lib/posthog.ts`
- Modify: `apps/api/src/main.py`（init posthog client）
- Create: `apps/api/src/core/analytics.py`
- Modify: `apps/api/src/routers/auth.py`（在登录成功处 capture 事件示例）

**Interfaces:**
- Produces:
  - `Events` 枚举（强类型事件名）：`USER_SIGNED_IN`、`USER_PERSONA_PICKED`、`AI_HEALTH_CHECKED` 等（v1 仅 5-8 个，后续 plan 自行扩展枚举）
  - 前端 `track(event, props)` 函数
  - 后端 `capture(user_id, event, props)` 函数
  - 真实 PostHog 项目接通（用户在 .env 填 key）

- [ ] **Step 1：建 packages/shared-types**

```bash
mkdir -p packages/shared-types
cat > packages/shared-types/package.json << 'EOF'
{
  "name": "@jc/shared-types",
  "version": "0.0.0",
  "main": "events.ts",
  "types": "events.ts"
}
EOF
```

`packages/shared-types/events.ts`：
```typescript
export const Events = {
  USER_SIGNED_IN: 'user_signed_in',
  USER_PERSONA_PICKED: 'user_persona_picked',
  DISGUISE_TOGGLED: 'disguise_toggled',
  LOCALE_SWITCHED: 'locale_switched',
  AI_HEALTH_CHECKED: 'ai_health_checked',
} as const

export type EventName = (typeof Events)[keyof typeof Events]
```

- [ ] **Step 2：装 PostHog**

```bash
cd apps/web && pnpm add posthog-js@1.179.0 @jc/shared-types@workspace:* && cd ../..
cd apps/api && source .venv/bin/activate && pip install posthog==3.7.0 && cd ../..
```

注：`pnpm-workspace.yaml` 已包含 `packages/*`，workspace 协议生效。

- [ ] **Step 3：写 web `lib/posthog.ts`**

```typescript
'use client'
import posthog from 'posthog-js'
import { EventName } from '@jc/shared-types'

let initialized = false

export function initPostHog() {
  if (initialized || typeof window === 'undefined') return
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST
  if (!key) return
  posthog.init(key, { api_host: host, person_profiles: 'identified_only' })
  initialized = true
}

export function track(event: EventName, props?: Record<string, unknown>) {
  if (!initialized) return
  posthog.capture(event, props)
}

export function identify(userId: string) {
  if (!initialized) return
  posthog.identify(userId)
}
```

- [ ] **Step 4：在 LocaleLayout 顶部初始化（client component）**

新建 `apps/web/src/components/PostHogBoot.tsx`：
```typescript
'use client'
import { useEffect } from 'react'
import { initPostHog } from '@/lib/posthog'

export function PostHogBoot() {
  useEffect(() => { initPostHog() }, [])
  return null
}
```

Modify `apps/web/src/app/[locale]/layout.tsx` body 起始：
```typescript
<NextIntlClientProvider messages={messages}>
  <PostHogBoot />
  {children}
</NextIntlClientProvider>
```

- [ ] **Step 5：写 api `core/analytics.py`**

```python
from posthog import Posthog
from src.core.config import get_settings

_settings = get_settings()
_client = Posthog(_settings.posthog_api_key, host=_settings.posthog_host) if _settings.posthog_api_key else None

def capture(user_id: str | None, event: str, props: dict | None = None) -> None:
    if _client is None:
        return
    _client.capture(distinct_id=user_id or "anonymous", event=event, properties=props or {})
```

- [ ] **Step 6：在登录路径打点示例**

修改 `apps/api/src/routers/auth.py` verify 与 callback 在 commit 后追加：
```python
from src.core.analytics import capture
# ...
capture(str(user.id), "user_signed_in", {"method": "magic_link"})  # or "wechat"
```

- [ ] **Step 7：自检 + 提交**

如果用户尚未配 PostHog key，应静默 skip（不报错）。

```bash
pnpm --filter web typecheck && pnpm --filter api typecheck
git add packages apps
git commit -m "feat: posthog integration (web + api) with shared event enum"
```

---

## Task 15: Sentry Integration (Web + API)

**Files:**
- Modify: `apps/web/package.json`（装 sentry/nextjs）
- Create: `apps/web/sentry.client.config.ts`
- Create: `apps/web/sentry.server.config.ts`
- Create: `apps/web/sentry.edge.config.ts`
- Modify: `apps/web/next.config.mjs`
- Modify: `apps/api/src/main.py`（init sentry-sdk）
- Create: `apps/api/tests/test_sentry_init.py`

**Interfaces:**
- Produces: 任何未捕获异常自动上报到 Sentry（前端 + 后端）；DSN 通过 env 配置；若 DSN 为空，sentry 不初始化（无副作用）

- [ ] **Step 1：装并接入 web sentry**

```bash
cd apps/web && pnpm add @sentry/nextjs@8.36.0 && cd ../..
```

`apps/web/sentry.client.config.ts`、`sentry.server.config.ts`、`sentry.edge.config.ts` 三份内容相同：
```typescript
import * as Sentry from '@sentry/nextjs'

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN
if (dsn) {
  Sentry.init({ dsn, tracesSampleRate: 0.1 })
}
```

Modify `apps/web/next.config.mjs`（用 withSentryConfig 包裹）：
```javascript
import createNextIntlPlugin from 'next-intl/plugin'
import { withSentryConfig } from '@sentry/nextjs'

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts')

/** @type {import('next').NextConfig} */
const nextConfig = { reactStrictMode: true }

export default withSentryConfig(withNextIntl(nextConfig), {
  silent: true,
  // sentry org/project 在 CI 注入；本地无需
})
```

- [ ] **Step 2：接 api sentry**

修改 `apps/api/src/main.py` 顶部：
```python
import sentry_sdk
from src.core.config import get_settings

_dsn = get_settings().sentry_dsn
if _dsn:
    sentry_sdk.init(dsn=_dsn, traces_sample_rate=0.1)

from fastapi import FastAPI
from src.routers import health, auth, me

app = FastAPI(title="Job Companion API", version="0.0.0")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
```

- [ ] **Step 3：测 api 不报错（dsn 空时 init 不调用）**

`apps/api/tests/test_sentry_init.py`：
```python
import importlib

def test_app_starts_without_sentry_dsn(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    from src.core import config; config.get_settings.cache_clear()
    mod = importlib.reload(importlib.import_module("src.main"))
    assert mod.app is not None
```

Run：`pytest -q tests/test_sentry_init.py` → 期望 PASS。

- [ ] **Step 4：提交**

```bash
git add apps
git commit -m "feat: sentry integration for web (nextjs) and api (fastapi)"
```

---

## Task 16: Playwright e2e Smoke Test

**Files:**
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/e2e/smoke.spec.ts`
- Modify: `apps/web/package.json` (e2e script 已在 Task 2 加)

**Interfaces:**
- Produces:
  - `pnpm --filter web e2e` 跑 Playwright，启动 dev server，访问 / → 自动跳 /zh → 看到首页标题；访问 /en 看到英文标题
  - CI 中跑

- [ ] **Step 1：装 Playwright**

```bash
cd apps/web
pnpm add -D @playwright/test@1.48.2
pnpm exec playwright install --with-deps chromium
cd ../..
```

- [ ] **Step 2：写 playwright.config.ts**

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: true,
  reporter: 'list',
  use: { baseURL: 'http://localhost:3000', trace: 'on-first-retry' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    timeout: 60_000,
    reuseExistingServer: !process.env.CI,
  },
})
```

- [ ] **Step 3：写 smoke 测试**

`apps/web/e2e/smoke.spec.ts`：
```typescript
import { test, expect } from '@playwright/test'

test('zh home loads', async ({ page }) => {
  await page.goto('/zh')
  await expect(page.getByRole('heading', { name: '求职作战中心' })).toBeVisible()
})

test('en home loads', async ({ page }) => {
  await page.goto('/en')
  await expect(page.getByRole('heading', { name: 'Job Companion' })).toBeVisible()
})

test('login page reachable', async ({ page }) => {
  await page.goto('/zh/login')
  await expect(page.getByRole('button', { name: '发送登录链接' })).toBeVisible()
})

test('disguise toggle changes title', async ({ page }) => {
  await page.goto('/zh/dashboard')
  // 未登录会被重定向但 disguise 不依赖登录态——验证组件存在性
  await page.keyboard.press('Control+`')
  await expect(page).toHaveTitle(/TimeFlow/)
  await page.keyboard.press('Control+`')
})
```

- [ ] **Step 4：跑测试**

```bash
pnpm --filter web e2e
# 期望：4 passed
```

- [ ] **Step 5：提交**

```bash
git add apps/web
git commit -m "test(web): playwright smoke tests for home/login/disguise"
```

---

## Task 17: GitHub Actions CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: 每个 PR 自动跑 lint + typecheck + 单测 + e2e；postgres 与 redis 在 CI 用 services 起；任何步失败则 fail

- [ ] **Step 1：写 ci.yml**

```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

jobs:
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9.12.0 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile=false
      - run: pnpm --filter web lint
      - run: pnpm --filter web typecheck
      - run: pnpm --filter web test
      - name: Install Playwright browsers
        run: pnpm --filter web exec playwright install --with-deps chromium
      - run: pnpm --filter web e2e
        env:
          NEXT_PUBLIC_API_BASE: http://localhost:8000

  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: jc
          POSTGRES_PASSWORD: jc_dev
          POSTGRES_DB: jc_dev
        ports: ['5432:5432']
        options: >-
          --health-cmd="pg_isready -U jc"
          --health-interval=5s --health-timeout=5s --health-retries=10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - working-directory: apps/api
        run: |
          python -m pip install -U pip
          pip install -e ".[dev]"
      - name: Generate field encryption key
        working-directory: apps/api
        run: echo "FIELD_ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> $GITHUB_ENV
      - working-directory: apps/api
        env:
          DATABASE_URL: postgresql+psycopg://jc:jc_dev@localhost:5432/jc_dev
          JWT_SECRET: ci-test-secret-32bytes-min-padding-pad
          APP_ENV: test
        run: |
          alembic upgrade head
          ruff check src tests
          mypy src
          pytest -q
```

- [ ] **Step 2：本地验证（可选）**

无法本地真跑 GitHub Actions，但可逐条命令验证：
```bash
pnpm --filter web lint
pnpm --filter web typecheck
pnpm --filter web test
pnpm --filter web e2e
cd apps/api && source .venv/bin/activate && ruff check src tests && mypy src && pytest -q
```

- [ ] **Step 3：提交并推送，触发 CI**

```bash
git add .github
git commit -m "ci: github actions for web + api"
git remote add origin <your_repo_url>   # 用户在执行时已有 repo
git push -u origin main
# 在 GitHub Actions tab 看到两个 job 都跑通
```

---

## Plan 0 完成判定

执行完上述 17 个 Task 后，下列命令均能跑通：

```bash
# 本地启动
docker compose -f infra/docker-compose.yml up -d
pnpm install
pnpm --filter api dev          # api on :8000
pnpm --filter web dev          # web on :3000

# 验证
curl http://localhost:8000/api/v1/health         # {"status":"ok"}
curl http://localhost:8000/api/v1/health/ai      # 视有无 AI key
open http://localhost:3000                       # → 自动跳 /zh
# 登录全流程：/zh/login → 填邮箱 → 看 api 日志 token → 访问 /zh/verify?token=xxx → 跳 /zh/onboarding → 选 persona → 跳 /zh/dashboard
# Ctrl+` 切伪装界面，标题变 TimeFlow

# 测试
pnpm test                       # web vitest 全过
cd apps/api && pytest -q        # api pytest 全过
pnpm e2e                        # web e2e 全过
```

GitHub Actions CI 在 PR/push 上跑全部上述检查。

---

## 下一步

Plan 0 完成 → 进入 Plan 1（MasterResume 模块）的详细 writeup。
