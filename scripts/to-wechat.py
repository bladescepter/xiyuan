#!/usr/bin/env python3
"""跨平台将博客 Markdown 转为微信公众号草稿。"""
import argparse
import html
import json
import mimetypes
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit


# business-navy 主题样式（深蓝 + 金色点缀）
STYLES = {
    "body": "font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; font-size: 15.5px; color: #0f1a33; line-height: 1.8; letter-spacing: 0.35px; word-spacing: 1.5px; padding: 20px 22px; background: #ffffff;",
    "h2": "font-size: 18px; font-weight: 800; color: #0b2445; margin: 40px 0 18px; padding: 2px 0 2px 16px; border-left: 4px solid #c9a74a; line-height: 1.5; letter-spacing: 0.3px;",
    "h3": "font-size: 15.5px; font-weight: 700; color: #0b2445; margin: 28px 0 12px; padding: 0; letter-spacing: 0.3px;",
    "p": "margin: 16px 0; text-indent: 0; text-align: justify; color: #1a233a; line-height: 1.85;",
    "blockquote": "margin: 24px 0; padding: 18px 22px; background: #f4f6fb; border-left: 3px solid #c9a74a; color: #2a3552; font-size: 14.5px; border-radius: 0; line-height: 1.85; letter-spacing: 0.3px;",
    "strong": "color: #0b2445; font-weight: 800; border-bottom: 2px solid #c9a74a; padding: 0 1px;",
    "em": "font-style: italic; color: #5a6580;",
    "code_inline": "background: #eef2f8; color: #0b2445; padding: 2px 7px; border-radius: 2px; font-size: 13px; font-family: 'JetBrains Mono', 'Menlo', 'Consolas', monospace; border: 1px solid #d6dde9;",
    "code_block": "background: #0b2445; color: #e7ecf5; padding: 16px 18px; border-radius: 4px; font-size: 12.5px; line-height: 1.65; font-family: 'JetBrains Mono', 'Menlo', 'Consolas', monospace; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; margin: 24px 0; border: 1px solid #1a3360;",
    "ul": "margin: 18px 0; padding-left: 0; list-style: none;",
    "ol": "margin: 18px 0; padding-left: 28px; color: #c9a74a; font-weight: 700;",
    "li": "margin: 10px 0; line-height: 1.8; color: #1a233a; font-weight: 400;",
    "hr": "border: none; height: 1px; background: linear-gradient(to right, transparent, #c9a74a, transparent); margin: 40px 0;",
    "a": "color: #1a4480; text-decoration: none; border-bottom: 1px solid rgba(26,68,128,0.4);",
    "table": "width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 14px; border-top: 2px solid #0b2445; border-bottom: 2px solid #0b2445; table-layout: fixed; word-break: break-word;",
    "th": "background: #0b2445; color: #c9a74a; padding: 10px 12px; text-align: left; font-weight: 700; font-size: 12.5px; letter-spacing: 1px; word-break: break-word; line-height: 1.5;",
    "td": "padding: 10px 8px; border-bottom: 1px solid #e6ebf3; color: #1a233a; font-size: 13px; word-break: break-word; line-height: 1.55;",
    "img": "max-width: 100%; height: auto; border-radius: 2px; box-shadow: 0 6px 20px rgba(11,36,69,0.1); border: 1px solid #e0e5ee; display: block; margin: 24px auto;",
}


CALLOUT_STYLES = {
    "note": {"border": "#2e5bff", "bg": "#eef2ff", "icon": "ℹ️ "},
    "abstract": {"border": "#5a6580", "bg": "#eef2f8", "icon": "📝 "},
    "summary": {"border": "#5a6580", "bg": "#eef2f8", "icon": "📝 "},
    "tldr": {"border": "#5a6580", "bg": "#eef2f8", "icon": "📝 "},
    "info": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "ℹ️ "},
    "todo": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "✅ "},
    "tip": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "💡 "},
    "hint": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "💡 "},
    "important": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "❗ "},
    "success": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "✅ "},
    "check": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "✅ "},
    "done": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "✅ "},
    "question": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "❓ "},
    "help": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "❓ "},
    "faq": {"border": "#5a9e8f", "bg": "#e0f0ec", "icon": "❓ "},
    "warning": {"border": "#c9a74a", "bg": "#f8f3e3", "icon": "⚠️ "},
    "caution": {"border": "#c9a74a", "bg": "#f8f3e3", "icon": "⚠️ "},
    "attention": {"border": "#c9a74a", "bg": "#f8f3e3", "icon": "⚠️ "},
    "failure": {"border": "#c43a30", "bg": "#fce8e4", "icon": "❌ "},
    "fail": {"border": "#c43a30", "bg": "#fce8e4", "icon": "❌ "},
    "missing": {"border": "#c43a30", "bg": "#fce8e4", "icon": "❌ "},
    "danger": {"border": "#c43a30", "bg": "#fce8e4", "icon": "⚡ "},
    "error": {"border": "#c43a30", "bg": "#fce8e4", "icon": "⚡ "},
    "bug": {"border": "#c43a30", "bg": "#fce8e4", "icon": "🐞 "},
    "example": {"border": "#5a6580", "bg": "#eef2f8", "icon": "💡 "},
    "quote": {"border": "#7a85a0", "bg": "#eef2f8", "icon": "💬 "},
    "cite": {"border": "#7a85a0", "bg": "#eef2f8", "icon": "💬 "},
}
# 规范化为小写键
CALLOUT_STYLES = {k.lower(): v for k, v in CALLOUT_STYLES.items()}


def _escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def process_inline(text):
    """处理行内语法: 图片,链接,行内代码,粗体,斜体"""
    # 1. 转义 < >
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    # 2. 图片
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
        lambda m: f'<img src="{html.escape(m.group(2), quote=True)}" alt="{html.escape(m.group(1), quote=True)}" style="{STYLES["img"]}"/>',
        text)
    # 3. 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" style="{STYLES["a"]}">{m.group(1)}</a>',
        text)
    # 4. 行内代码 `code`
    text = re.sub(r'`([^`]+)`',
        lambda m: f'<code style="{STYLES["code_inline"]}">{_escape_html(m.group(1))}</code>',
        text)
    # 5. 粗体 **
    text = re.sub(r'\*\*([^*\n]+)\*\*', lambda m: f'<strong style="{STYLES["strong"]}">{m.group(1)}</strong>', text)
    # 6. 斜体 *
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', lambda m: f'<em style="{STYLES["em"]}">{m.group(1)}</em>', text)
    return text


def md_to_wechat_html(md_text: str, title: str = "", author: str = "", source_url: str = "") -> str:
    """将Markdown转为微信公众号排版适配HTML"""
    lines = md_text.split("\n")
    html_parts = []

    in_code = False
    code_lines = []
    in_blockquote = False
    bq_lines = []
    current_callout = None   # None or callout type key
    callout_title = ""
    in_list = False
    list_type = None  # "ul" or "ol"
    list_items = []

    def flush_list():
        nonlocal in_list, list_items, list_type
        if in_list and list_items:
            tag = list_type or "ul"
            items = "\n".join(
                f'<li style="{STYLES["li"]}">{item}</li>' for item in list_items
            )
            html_parts.append(f'<{tag} style="{STYLES[tag]}">{items}</{tag}>')
            list_items = []
            in_list = False
            list_type = None

    def flush_blockquote():
        nonlocal in_blockquote, bq_lines, current_callout, callout_title
        if in_blockquote and bq_lines:
            if current_callout:
                cs = CALLOUT_STYLES.get(current_callout, CALLOUT_STYLES["note"])
                title_html = f'<strong style="color: {cs["border"]}; font-size: 15px;">{cs["icon"]}{callout_title}</strong><br>' if callout_title else ""
                content = "<br>".join(bq_lines)
                html_parts.append(
                    f'<div style="margin: 24px 0; padding: 16px 18px; background: {cs["bg"]}; '
                    f'border-left: 4px solid {cs["border"]}; border-radius: 8px; '
                    f'color: #1a233a; font-size: 14.5px; line-height: 1.8;">'
                    f'{title_html}{content}</div>'
                )
            else:
                content = "<br>".join(bq_lines)
                html_parts.append(f'<blockquote style="{STYLES["blockquote"]}">{content}</blockquote>')
            bq_lines = []
            in_blockquote = False
            current_callout = None
            callout_title = ""

    for line in lines:
        s = line.strip()

        # 代码块
        if s.startswith("```"):
            if in_code:
                html_parts.append(f'<pre style="{STYLES["code_block"]}">{"\n".join(code_lines)}</pre>')
                code_lines = []
                in_code = False
            else:
                flush_list()
                flush_blockquote()
                in_code = True
            continue
        if in_code:
            code_lines.append(_escape_html(line))
            continue

        # 引用 / Obsidian callout
        if s.startswith(">"):
            flush_list()
            # 检测 callout 格式: > [!TYPE] Title
            cal = re.match(r'^>\s*\[!(\w+)\]\s*(.*)', s)
            if cal:
                ctype = cal.group(1).lower()
                if ctype in CALLOUT_STYLES:
                    if not in_blockquote:
                        in_blockquote = True
                        current_callout = ctype
                        callout_title = cal.group(2).strip()
                    continue
            # 普通 blockquote
            in_blockquote = True
            bq_lines.append(process_inline(s.lstrip(">").strip()))
            continue
        else:
            flush_blockquote()

        # 标题
        hm = re.match(r'^(#{2,3})\s+(.+)$', s)
        if hm:
            flush_list()
            level = len(hm.group(1))
            tag = f"h{level}"
            html_parts.append(f'<{tag} style="{STYLES[tag]}">{process_inline(hm.group(2))}</{tag}>')
            continue

        # 分割线
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', s):
            flush_list()
            html_parts.append(f'<hr style="{STYLES["hr"]}"/>')
            continue

        # 无序列表
        um = re.match(r'^[-*+]\s+(.+)$', s)
        if um:
            if not in_list or list_type != "ul":
                flush_list()
                in_list = True
                list_type = "ul"
            list_items.append(process_inline(um.group(1)))
            continue

        # 有序列表
        om = re.match(r'^\d+\.\s+(.+)$', s)
        if om:
            if not in_list or list_type != "ol":
                flush_list()
                in_list = True
                list_type = "ol"
            list_items.append(process_inline(om.group(1)))
            continue

        flush_list()

        if not s:
            continue

        # 纯图片行
        im = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', s)
        if im:
            html_parts.append(
                f'<p style="text-align:center;margin:24px 0;">'
                f'<img src="{html.escape(im.group(2), quote=True)}" alt="{html.escape(im.group(1), quote=True)}" style="{STYLES["img"]}"/>'
                f'</p>'
            )
            continue

        # 普通段落
        html_parts.append(f'<p style="{STYLES["p"]}">{process_inline(s)}</p>')

    flush_list()
    flush_blockquote()

    # 未闭合代码块
    if in_code and code_lines:
        html_parts.append(f'<pre style="{STYLES["code_block"]}">{"\n".join(code_lines)}</pre>')

    body = "\n".join(html_parts)

    # 开头和结尾装饰
    header = ('<section style="text-align: center;">\n'
              f'  <p style="color: #c9a74a; font-size: 18px; margin: 10px 0 6px; user-select: none; opacity: 0.6; letter-spacing: 2px;">(ㅅ˘ㅂ˘)  Hi~</p>\n'
              f'  <hr style="border: none; height: 1px; background: linear-gradient(to right, transparent, #c9a74a, transparent); margin: 0 0 24px; opacity: 0.4;">\n'
              f'</section>')

    footer = ""
    if source_url:
        footer = (f'  <hr style="border: none; height: 1px; background: linear-gradient(to right, transparent, #c9a74a, transparent); margin: 32px 0 6px; opacity: 0.4;">\n'
                  f'  <p style="text-align: center; color: #c9a74a; font-size: 18px; margin: 0 0 12px; user-select: none; opacity: 0.6; letter-spacing: 2px;">( ´ ω ` )ノﾞ  Bye~Bye~</p>\n'
                  f'  <section style="text-align: center; color: #7a85a0; font-size: 13px; opacity: 0.7; padding-bottom: 10px;">\n'
                  f'    <p>本文首发于 <a href="{source_url}" style="color: #1a4480; text-decoration: none; border-bottom: 1px solid rgba(26,68,128,0.3);">xiyuan.wiki</a></p>\n'
                  f'  </section>')

    return (f'<section style="{STYLES["body"]}">\n'
            f'  {header}\n'
            f'  {body}\n'
            f'  {footer}\n'
            f'</section>')


POSTS_DIR = Path(__file__).resolve().parent.parent / "src" / "content" / "posts"
BLOG_BASE_URL = "https://xiyuan.wiki"
REQUIRED_CATEGORY_TAGS = {"随笔", "杜撰", "打油", "折腾"}
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)\s]+)\)")


def parse_frontmatter(content):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.S)
    if not match:
        raise ValueError("文章缺少有效的 YAML frontmatter。")
    return match.group(1), content[match.end():]


def _yaml_scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def _frontmatter_value(frontmatter, name, default=""):
    for line in frontmatter.splitlines():
        match = re.match(rf"^{re.escape(name)}\s*:\s*(.*)$", line)
        if match:
            return _yaml_scalar(match.group(1))
    return default


def _frontmatter_tags(frontmatter):
    lines = frontmatter.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^tags\s*:\s*(.*)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value.startswith("[") and value.endswith("]"):
            return {_yaml_scalar(item) for item in value[1:-1].split(",") if item.strip()}
        tags = set()
        if value:
            tags.add(_yaml_scalar(value))
        for tag_line in lines[index + 1:]:
            if not tag_line.strip():
                continue
            item = re.match(r"^\s+-\s+(.*?)\s*$", tag_line)
            if item:
                tags.add(_yaml_scalar(item.group(1)))
                continue
            if tag_line[:1].isspace():
                continue
            break
        return tags
    return set()


def find_post(selector, posts_dir):
    candidate = Path(selector).expanduser()
    if candidate.is_file():
        path = candidate.resolve()
        content = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)
        return path, frontmatter, body

    if not posts_dir.is_dir():
        raise FileNotFoundError(f"文章目录不存在：{posts_dir}")

    matches = []
    for path in sorted(posts_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        try:
            frontmatter, body = parse_frontmatter(content)
        except ValueError:
            continue
        slug = _frontmatter_value(frontmatter, "slug", path.stem)
        if selector == slug or selector == path.stem:
            matches.append((path, frontmatter, body))
    if not matches:
        raise FileNotFoundError(f"未找到文章：{selector}（搜索目录：{posts_dir}）")
    if len(matches) > 1:
        names = ", ".join(item[0].name for item in matches)
        raise ValueError(f"文章标识不唯一：{selector}；匹配到：{names}")
    return matches[0]


def _default_env_path():
    if os.name == "nt":
        config_home = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        config_home = Path.home() / "Library" / "Application Support"
    else:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "xiyuan" / ".env"


def load_settings(env_file):
    configured_path = env_file or os.environ.get("WX_ENV_FILE")
    path = Path(configured_path).expanduser() if configured_path else _default_env_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"找不到微信凭据文件：{path}。请创建该文件，或用 --env-file / WX_ENV_FILE 指定路径。"
        )
    if os.name != "nt":
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            raise PermissionError(
                f"凭据文件权限过宽：{path}（当前 {mode:o}）；请将权限收紧为仅当前用户可读写，例如 chmod 600。"
            )

    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator:
            continue
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        values[key] = value

    missing = [key for key in ("WX_APPID", "WX_APPSECRET") if not values.get(key)]
    if missing:
        raise ValueError(f"凭据文件缺少必填项：{', '.join(missing)}。密钥不要发送到聊天或写入仓库。")
    return values


def _curl_quote(value):
    value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    value = value.replace("\r", "\\r").replace("\n", "\\n")
    return f'"{value}"'


def _curl_request(url, work_dir, proxy=None, form=None, body_file=None, headers=None, timeout=120):
    curl = shutil.which(os.environ.get("CURL", "curl"))
    if not curl:
        raise RuntimeError("找不到 curl；请安装 curl 并确保它位于 PATH 中。")

    output_fd, output_name = tempfile.mkstemp(prefix="wx-response-", dir=work_dir)
    config_fd, config_name = tempfile.mkstemp(prefix="wx-curl-", suffix=".conf", dir=work_dir)
    output_path = Path(output_name)
    config_path = Path(config_name)
    try:
        os.close(output_fd)
        lines = [
            "silent",
            "show-error",
            "location",
            "connect-timeout = 15",
            f"max-time = {int(timeout)}",
            "max-filesize = 52428800",
            'write-out = "%{http_code}"',
            f"output = {_curl_quote(output_path.as_posix())}",
            f"url = {_curl_quote(url)}",
        ]
        if proxy:
            lines.append(f"proxy = {_curl_quote(proxy)}")
        if form:
            field_name, file_path, mime_type = form
            form_value = f"{field_name}=@{Path(file_path).resolve().as_posix()};type={mime_type}"
            lines.append(f"form = {_curl_quote(form_value)}")
        if body_file:
            lines.append(f"header = {_curl_quote('Content-Type: application/json; charset=utf-8')}")
            lines.append(f"data-binary = {_curl_quote('@' + Path(body_file).resolve().as_posix())}")
        for header in headers or []:
            lines.append(f"header = {_curl_quote(header)}")
        with os.fdopen(config_fd, "w", encoding="utf-8", newline="\n") as config:
            config.write("\n".join(lines) + "\n")
        if os.name != "nt":
            os.chmod(config_path, 0o600)

        result = subprocess.run(
            [curl, "--config", str(config_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            host = urlsplit(url).netloc
            raise RuntimeError(f"请求 {host} 失败（curl 退出码 {result.returncode}）；请检查网络、代理和服务状态。")
        status_text = result.stdout.strip()
        if not status_text.isdigit():
            raise RuntimeError("curl 未返回有效 HTTP 状态码。")
        status = int(status_text)
        if status < 200 or status >= 300:
            host = urlsplit(url).netloc
            raise RuntimeError(f"请求 {host} 失败（HTTP {status}）。")
        return output_path.read_bytes()
    finally:
        try:
            os.close(config_fd)
        except OSError:
            pass
        output_path.unlink(missing_ok=True)
        config_path.unlink(missing_ok=True)


def _decode_api_response(data):
    try:
        result = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("微信 API 返回了无法解析的响应。") from exc
    if not isinstance(result, dict):
        raise RuntimeError("微信 API 返回格式异常。")
    if result.get("errcode") not in (None, 0, "0"):
        raise RuntimeError(
            f"微信 API 错误：errcode={result.get('errcode')}，errmsg={result.get('errmsg', '未知错误')}"
        )
    return result


def _new_local_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_ssh_tunnel(settings, ssh_target, ssh_key, ssh_port):
    ssh = shutil.which("ssh")
    if not ssh:
        raise RuntimeError("找不到 ssh；请安装 OpenSSH Client 并确保 ssh 位于 PATH 中。")
    port = _new_local_port()
    command = [
        ssh, "-N", "-D", f"127.0.0.1:{port}",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        "-o", "ServerAliveInterval=30",
    ]
    key_value = ssh_key or settings.get("WX_SSH_KEY") or os.environ.get("WX_SSH_KEY")
    if key_value:
        key_path = Path(key_value).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(f"SSH 私钥文件不存在：{key_path}")
        command.extend(["-i", str(key_path)])
    else:
        default_key = Path.home() / ".ssh" / "bladescepter.pem"
        if default_key.is_file():
            command.extend(["-i", str(default_key)])
    command.extend(["-p", str(ssh_port), ssh_target])

    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise RuntimeError(f"无法启动 SSH 隧道：{exc}") from exc

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"SSH 隧道启动失败（退出码 {process.returncode}）；请检查 SSH 目标、密钥、端口和网络。"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return process, f"socks5h://127.0.0.1:{port}"
        except OSError:
            time.sleep(0.1)
    stop_ssh_tunnel(process)
    raise RuntimeError("SSH 隧道在 10 秒内未就绪；请检查 SSH 目标、密钥、端口和网络。")


def stop_ssh_tunnel(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _upload_body_image(image_url, index, token, proxy, work_dir):
    image_data = _curl_request(image_url, work_dir, timeout=90)
    suffix = Path(urlsplit(image_url).path).suffix.lower()
    if suffix == ".webp":
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("文章包含 WebP 图片；转换需要 Pillow，请运行 python -m pip install Pillow。") from exc
        try:
            with Image.open(BytesIO(image_data)) as image:
                converted = BytesIO()
                image.convert("RGB").save(converted, format="PNG")
                image_data = converted.getvalue()
            suffix, mime_type = ".png", "image/png"
        except Exception as exc:
            raise RuntimeError(f"第 {index} 张 WebP 图片无法转换。") from exc
    else:
        mime_type = mimetypes.guess_type("image" + suffix)[0] or "image/jpeg"
        if not suffix:
            suffix = ".jpg"

    image_path = work_dir / f"body-image-{index}{suffix}"
    image_path.write_bytes(image_data)
    url = "https://api.weixin.qq.com/cgi-bin/media/uploadimg?" + urlencode({"access_token": token})
    response = _curl_request(url, work_dir, proxy=proxy, form=("media", image_path, mime_type))
    result = _decode_api_response(response)
    uploaded_url = result.get("url")
    if not uploaded_url:
        raise RuntimeError(f"第 {index} 张正文图片上传失败：微信 API 未返回图片 URL。")
    return uploaded_url


def _upload_cover(cover_url, token, proxy, work_dir):
    cover_data = _curl_request(cover_url, work_dir, timeout=90)
    cover_path = work_dir / "wechat-cover.png"
    cover_path.write_bytes(cover_data)
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material?" + urlencode(
        {"access_token": token, "type": "image"}
    )
    result = _decode_api_response(
        _curl_request(url, work_dir, proxy=proxy, form=("media", cover_path, "image/png"))
    )
    return result.get("media_id", "")


def build_parser():
    parser = argparse.ArgumentParser(
        description="将博客文章转换为微信公众号草稿；脚本跨平台运行，需 Python、curl 和 OpenSSH。"
    )
    parser.add_argument("post", help="文章 slug 或 Markdown 文件路径")
    parser.add_argument("--posts-dir", type=Path, default=POSTS_DIR, help="文章目录（默认使用本仓库 src/content/posts）")
    parser.add_argument("--env-file", type=Path, help="凭据文件路径；默认使用各平台的用户配置目录")
    parser.add_argument("--site-url", help="博客根地址，默认 https://xiyuan.wiki")
    parser.add_argument("--ssh-target", help="SSH 出口目标，例如 ubuntu@119.28.143.201")
    parser.add_argument("--ssh-key", type=Path, help="SSH 私钥路径；也可设置 WX_SSH_KEY")
    parser.add_argument("--ssh-port", type=int, help="SSH 端口，默认 22")
    parser.add_argument("--direct", action="store_true", help="不建 SSH 隧道，直接访问微信 API（出口 IP 必须在白名单中）")
    parser.add_argument("--dry-run", action="store_true", help="只检查文章并生成 HTML，不访问网络或微信 API")
    parser.add_argument("--preview-html", type=Path, help="将生成的 HTML 写入该路径，适用于 --dry-run 或保留预览")
    return parser


def _write_preview(path, rendered):
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    print(f"HTML 预览已保存：{path.resolve()}")


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        post_path, frontmatter, body = find_post(args.post, args.posts_dir.expanduser())
        title = _frontmatter_value(frontmatter, "title", post_path.stem)
        slug = _frontmatter_value(frontmatter, "slug", post_path.stem)
        author = _frontmatter_value(frontmatter, "author", "陆西园")
        digest = _frontmatter_value(frontmatter, "description", "")
        tags = _frontmatter_tags(frontmatter)
        if REQUIRED_CATEGORY_TAGS.isdisjoint(tags):
            required = "、".join(sorted(REQUIRED_CATEGORY_TAGS))
            raise ValueError(f"文章缺少分类标签：至少添加一个 {required} 后再同步。")
        if not title or len(title) > 32:
            raise ValueError("标题不能为空且不得超过 32 个字符（微信公众号接口限制）。")
        if len(author) > 16:
            raise ValueError("作者名不得超过 16 个字符（微信公众号接口限制）。")
        if len(digest) > 120:
            raise ValueError("摘要不得超过 120 个字符（微信公众号接口限制）。")

        site_url = (args.site_url or os.environ.get("WX_SITE_URL") or BLOG_BASE_URL).rstrip("/")
        source_url = f"{site_url}/posts/{quote(slug, safe='')}/"
        print(f"文章：{title}（slug {slug}）")
        print(f"原文：{source_url}")

        if args.dry_run:
            rendered = md_to_wechat_html(body, title, author, source_url)
            if args.preview_html:
                _write_preview(args.preview_html, rendered)
            print(f"预演完成：{len(IMAGE_RE.findall(body))} 张正文图片；未访问网络、未调用微信 API。")
            return 0

        settings = load_settings(args.env_file)
        ssh_target = args.ssh_target or settings.get("WX_SSH_TARGET") or os.environ.get("WX_SSH_TARGET") or "ubuntu@119.28.143.201"
        ssh_port = args.ssh_port or int(settings.get("WX_SSH_PORT") or os.environ.get("WX_SSH_PORT") or "22")
        process = None
        proxy = None
        with tempfile.TemporaryDirectory(prefix="to-wechat-") as temporary_dir:
            work_dir = Path(temporary_dir)
            try:
                if not args.direct:
                    process, proxy = start_ssh_tunnel(settings, ssh_target, args.ssh_key, ssh_port)
                    print(f"SSH API 隧道已就绪：{ssh_target}")

                token_url = "https://api.weixin.qq.com/cgi-bin/token?" + urlencode({
                    "grant_type": "client_credential",
                    "appid": settings["WX_APPID"],
                    "secret": settings["WX_APPSECRET"],
                })
                token_result = _decode_api_response(_curl_request(token_url, work_dir, proxy=proxy))
                token = token_result.get("access_token")
                if not token:
                    raise RuntimeError("微信 API 未返回 access_token。")

                image_urls = list(dict.fromkeys(IMAGE_RE.findall(body)))
                updated_body = body
                for index, image_url in enumerate(image_urls, 1):
                    print(f"正文图片 {index}/{len(image_urls)}：上传中…")
                    uploaded_url = _upload_body_image(image_url, index, token, proxy, work_dir)
                    updated_body = updated_body.replace(image_url, uploaded_url)

                rendered = md_to_wechat_html(updated_body, title, author, source_url)
                if args.preview_html:
                    _write_preview(args.preview_html, rendered)

                if len(rendered) >= 20000 or len(rendered.encode("utf-8")) >= 1_000_000:
                    raise ValueError("排版后的正文超过微信公众号接口限制（少于 2 万字符且小于 1 MB）。")

                cover_url = f"{site_url}/posts/{quote(slug, safe='')}/index.png"
                print("封面将上传为公众号永久素材（会占用素材额度）。")
                thumb_media_id = _upload_cover(cover_url, token, proxy, work_dir)
                if not thumb_media_id:
                    raise RuntimeError("微信未返回封面素材 ID，无法创建公众号图文草稿。")

                article = {
                    "title": title,
                    "author": author,
                    "content": rendered,
                    "show_cover_pic": 1,
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                }
                if digest:
                    article["digest"] = digest
                if thumb_media_id:
                    article["thumb_media_id"] = thumb_media_id
                article["content_source_url"] = source_url
                payload_path = work_dir / "draft-payload.json"
                payload_path.write_text(json.dumps({"articles": [article]}, ensure_ascii=False), encoding="utf-8")
                draft_url = "https://api.weixin.qq.com/cgi-bin/draft/add?" + urlencode({"access_token": token})
                result = _decode_api_response(
                    _curl_request(draft_url, work_dir, proxy=proxy, body_file=payload_path)
                )
                media_id = result.get("media_id")
                if not media_id:
                    raise RuntimeError("微信 API 未返回草稿 media_id，草稿可能未创建。")
                print("公众号草稿创建成功。")
                print("请登录 https://mp.weixin.qq.com/ 在草稿箱预览并手动发布。")
                print(f"草稿 media_id：{media_id}")
                return 0
            finally:
                stop_ssh_tunnel(process)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
