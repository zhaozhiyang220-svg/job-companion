# 部署上线 Runbook — 腾讯云单机 Docker（公网 IP 裸跑 demo）

把 Job Companion 部署到一台腾讯云轻量服务器，浏览器经 `http://<公网IP>/` 访问。
架构：Caddy(:80) 同源反代 → web(3000) / api(8000)；api → postgres / redis（仅内网）。

> 仅适合 demo：HTTP 明文、cookie 非 secure、无域名/备案。上正式域名时再加 TLS。

---

## 0. 前置：本机一次性自检（可选）
```bash
cd apps/api && pytest -q && mypy src && ruff check src tests
```

## 1. 开机（腾讯云控制台）
- **轻量应用服务器**，镜像 `Docker` 或 `Ubuntu 22.04`，规格 **≥ 2C2G**（web 构建吃内存，推荐 2C4G，或 2C2G 配 2G swap），系统盘 ≥ 40G。
- 地域随意（demo 不备案）。记下**公网 IP**。

## 2. 防火墙 / 安全组
- 放通入站 **TCP 80**（应用）与 **TCP 22**（SSH）。
- **不要**放通 5432 / 6379 / 8000 / 3000（这些只走内网）。

## 3. 装 Docker（若用 Ubuntu 镜像）
```bash
curl -fsSL https://get.docker.com | sh
docker compose version   # 确认 v2
```
（2C2G 机器建议加 swap：`fallocate -l 2G /swap && chmod 600 /swap && mkswap /swap && swapon /swap`）

## 4. 上传代码
```bash
# 方式 A：已推 GitHub
git clone <你的仓库> /opt/job-companion
# 方式 B：本机 scp
#   scp -r ./job-companion root@<IP>:/opt/job-companion
cd /opt/job-companion
```

## 5. 配置 secrets
```bash
cp infra/.env.prod.example infra/.env.prod
# 生成强密钥：
openssl rand -hex 32                                                  # → JWT_SECRET
python3 -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"  # → FIELD_ENCRYPTION_KEY
openssl rand -hex 16                                                  # → POSTGRES_PASSWORD
```
编辑 `infra/.env.prod`，填入：
- `POSTGRES_PASSWORD` 与 `DATABASE_URL` 里的密码保持**一致**；
- `JWT_SECRET`、`FIELD_ENCRYPTION_KEY`；
- `DEEPSEEK_API_KEY`（现有 key）；
- `PUBLIC_WEB_URL=http://<公网IP>`；
- `INTERNAL_DASHBOARD_PASSWORD`。

## 6. 起服
```bash
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod up -d --build
```
首次 web 构建较慢（几分钟）。api 启动时自动 `alembic upgrade head`。
查看状态 / 日志：
```bash
docker compose -f infra/docker-compose.prod.yml ps
docker compose -f infra/docker-compose.prod.yml logs -f api
```

## 7. 冒烟测试
```bash
curl http://<IP>/api/v1/health/        # → {"status":"ok"}
curl http://<IP>/api/v1/health/ai      # → 真打一次 DeepSeek，pong
```
浏览器：
1. 开 `http://<IP>/` → 登录页输入邮箱 → 点发送。
2. 没配 SMTP，magic-link 会打到日志：
   ```bash
   docker compose -f infra/docker-compose.prod.yml logs api | grep "DEV EMAIL" | tail -1
   ```
   复制其中 `http://<IP>/auth/verify?token=...` 链接打开 → 登录成功。
3. 上传一份简历跑解析 → 建岗位 → 生成补丁 → 导 PDF（验证 WeasyPrint 中文不乱码）。
4. 成本仪表盘：`http://<IP>/internal/dashboard?password=<INTERNAL_DASHBOARD_PASSWORD>`。

## 8. 运维常用
```bash
# 更新代码后重建
git pull && docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod up -d --build
# 手动备份数据库
docker compose -f infra/docker-compose.prod.yml exec postgres \
  pg_dump -U jc jc > backup_$(date +%F).sql
# 停服
docker compose -f infra/docker-compose.prod.yml down
```

## 升级到正式域名（以后）
1. 域名解析到公网 IP（大陆需 ICP 备案）。
2. `Caddyfile` 顶部 `:80` 改成 `your-domain.com`（Caddy 自动签 HTTPS，需放通 443）。
3. `.env.prod` 的 `PUBLIC_WEB_URL` 改成 `https://your-domain.com`。
4. （同源反代不需 CORS；如改成 api 独立子域，再补 CORS 中间件 + cookie `secure/samesite=none`。）
