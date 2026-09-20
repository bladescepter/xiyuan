# Shell 转义避险 — 远程文件修改方案

在与 VPS 远程文件交互时，EJS 模板中的 `<%`, `(`, `)`, `'`, `"`, `&` 等字符会反复导致 shell/Python 解析失败。以下是实测有效的方案，优先级从高到低。

## 方案 A：Python 本地编辑 + SCP 写回（最简单，推荐）

在容器内用 Python 读取远程文件、做修改、写临时文件、SCP 回远程：

```python
import subprocess, tempfile, os

# 1. 读取远程文件
r = subprocess.run(
    ['ssh', 'ubuntu@172.17.0.1', 'cat /path/to/target.astro'],
    capture_output=True, text=True)
content = r.stdout

# 2. 替换（纯 Python，零 shell 转义问题）
content = content.replace('旧字符串', '新字符串')

# 3. 写临时文件 → SCP 回远程
with tempfile.NamedTemporaryFile(mode='w', suffix='.astro', delete=False) as f:
    f.write(content)
    tmp = f.name
subprocess.run(['scp', tmp, 'ubuntu@172.17.0.1:/path/to/target.astro'],
               capture_output=True)
os.unlink(tmp)
```

适用场景：Astro 模板中的 `${import.meta.env...}`、JSX 模板字符串、含 `&` `%` `$` 等特殊字符的内容。

## 方案 B：用 base64 编码 + SSH pipe

在 Hermes 的 execute_code 中，用 base64 编码 Python 脚本，通过 SSH pipe 到远程执行：

```python
from hermes_tools import terminal
import base64

script = b'''with open('/path/to/target.ejs', encoding='utf-8') as f:
    c = f.read()
c = c.replace('old_str', 'new_str')
with open('/path/to/target.ejs', 'w', encoding='utf-8') as f:
    f.write(c)
print('DONE')
'''

b64 = base64.b64encode(script).decode()
cmd = f'echo "{b64}" | base64 -d | python3'
r = terminal(f'ssh ubuntu@172.17.0.1 "{cmd}"', timeout=10)
print(r["output"])
```

## 方案 C：写 Python 脚本到远程再执行

```bash
cat > /tmp/script.py << 'PYEOF'
with open('/path/to/file.ejs', encoding='utf-8') as f:
    c = f.read()
c = c.replace('old', 'new')
with open('/path/to/file.ejs', 'w', encoding='utf-8') as f:
    f.write(c)
print('DONE')
PYEOF
python3 /tmp/script.py
```

**注意**：`'PYEOF'` 带引号时 shell 不做变量/命令替换。

## 方案 D：printf 逐行写 Python 文件

```bash
printf '%s\n' \
  'import re' \
  'with open("path") as f:' \
  '    c = f.read(); c = c.replace("old", "new")' \
  'with open("path", "w") as f: f.write(c)' \
  'print("done")' > /tmp/script.py
python3 /tmp/script.py
```

## 绝对不要用的方法

| 方法 | 原因 |
|------|------|
| `sed -i '/pattern/d'` 删多行 CSS block | 只删含 pattern 的行，`{`、属性行、`}` 行残留 → 构建报 `Missing opening {` |
| `sed -i 's/.../.../'` 改 EJS | `&` 在 replacement 中是"匹配文本"，碰到 `&&` 就炸 |
| `python3 -c '...'` 带复杂字符串 | 单引号嵌套、括号、双引号全部爆炸 |
| Shell heredoc 直接写 EJS 模板 | `<% %>` 里 `%` 被 bash 尝试展开 |
| Shell heredoc 写 Astro 文件含 `${}`（哪怕 `<< 'EOF'`） | 当 SSH 外层用双引号时，`${import.meta.env...}` 仍会被 bash 展开为"替换表达式"导致报错。**`<<'EOF'` 只在本地 shell 防止展开**，SSH 命令串再包双引号时又恢复了展开 |

## 恢复方案：hero doc 把文件搞坏了怎么办

首次用 Python+tempfile+SCP 之前，先用 `git checkout -- <file>` 恢复原始版本：

```bash
ssh ubuntu@172.17.0.1 "cd /home/ubuntu/blog-astro && git checkout -- src/pages/index.astro"
```

> 这个操作**只恢复被损坏的单个文件**，不会影响同项目的其他修改（如 about.md、favicon 等）。已测试验证。
