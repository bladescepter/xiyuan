# Docker ≥29.x 敏感环境变量脱敏

## 现象

运行中的容器，`JWT_TOKEN`、`AUTHOR_EMAIL` 等敏感环境变量从任何途径都无法读取：

- `docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}'` → `JWT_TOKEN=***`
- `docker exec <container> env` → `JWT_TOKEN=***`
- `/proc/<pid>/environ` → `***`
- `/var/lib/docker/containers/<id>/config.v2.json` → `***`

## 原因

Docker Engine ≥29.x 引入了环境变量脱敏保护。当 Docker 检测到环境变量名匹配常见敏感模式（`TOKEN`、`JWT`、`SECRET`、`KEY`、`PASSWORD` 等），会在**所有输出层面**截断其值：

- Docker API（`docker inspect`）
- 进程环境（`/proc/<pid>/environ`）
- Docker daemon 磁盘存储（`config.v2.json`）

实际值**不存在于任何可读位置**，不是加密，而是彻底截断。

## 影响

重建容器时必须提供这些值，因为无法从现有容器恢复。如果用户也不记得初始值，只能重新生成或重置。

## 已知受影响的值

| 容器 | 变量 | 处理方式 |
|:-----|:-----|:---------|
| waline | `JWT_TOKEN` | 重新生成随机 base64（`openssl rand -base64 32`），告知用户重新登录 |
| waline | `AUTHOR_EMAIL` | 除非改邮箱，否则写死，不受影响 |

## 诊断方法

```bash
# 检查是否被脱敏
docker exec waline env | grep JWT_TOKEN
# 输出为 JWT_TOKEN=***  → 已脱敏

# 检查 Docker 版本
docker version --format '{{.Server.Version}}'
# ≥29.x 则此机制生效
```

## 重建时的应对

1. 如果值已知 → 直接传
2. 如果值已脱敏且用户不知道 → 重新生成，告知影响
3. 对于 `AUTHOR_EMAIL` 等固定值 → 直接从文档或记忆获取

## 通用建议

首次部署时，把 `JWT_TOKEN` 等敏感值存到 `.env` 文件（`docker run --env-file`）或密码管理器中，避免后续重建时丢失。
