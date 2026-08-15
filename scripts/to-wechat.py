#!/usr/bin/env python3
"""to-wechat.py — 将Markdown正文转为微信草稿"""
import sys
import json
import os
import re
import html


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


def main():
    if len(sys.argv) < 5:
        print("用法: to-wechat.py <body.md> <title> <author> <token> <output.html> [digest] [thumb_media_id]")
        sys.exit(1)

    body_file = sys.argv[1]
    title = sys.argv[2]
    author = sys.argv[3]
    token = sys.argv[4]
    output_file = sys.argv[5]
    digest = sys.argv[6] if len(sys.argv) > 6 else ""
    thumb_media_id = sys.argv[7] if len(sys.argv) > 7 else ""
    source_url = sys.argv[8] if len(sys.argv) > 8 else ""

    with open(body_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    html = md_to_wechat_html(md_text, title, author, source_url)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"📄 本地HTML: {output_file}")

    if not thumb_media_id:
        print("⚠️  没有封面图（thumb_media_id），草稿可能失败")

    article = {
        "title": title,
        "author": author,
        "content": html,
        "show_cover_pic": 1,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    if digest:
        article["digest"] = digest
    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id
    if source_url:
        article["content_source_url"] = source_url
        print(f"🔗 原文链接: {source_url}")

    draft = {"articles": [article]}

    debug_file = output_file.replace('.html', '_draft.json')
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    print(f"🔍 草稿JSON: {debug_file}")

    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = json.dumps(draft, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=data,
        headers={'Content-Type': 'application/json'})

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())

        if 'media_id' in result:
            print(f"🎉 草稿已创建到公众号后台！")
            print(f"   打开 https://mp.weixin.qq.com/cgi-bin/appmsg 即可查看")
            for f in [output_file, debug_file]:
                if os.path.exists(f):
                    os.remove(f)
            print(f"🧹 临时文件已清理")
        else:
            print(f"❌ 草稿创建失败: {result}")
            sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ API请求失败: {e.code} {body}")
        sys.exit(1)


if __name__ == '__main__':
    # 延迟导入 urllib（只需在 main 里用）
    import urllib.request
    import urllib.error
    # Windows GBK 控制台打印 emoji 会 UnicodeEncodeError，强制 UTF-8 输出
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
