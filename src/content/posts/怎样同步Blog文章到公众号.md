---
title: 怎样同步Blog文章到公众号
slug: "007"
pubDatetime: 2026-07-25T17:23:00+08:00
tags:
  - 折腾
  - 公众号
  - Blog
  - Hermes
description: 一个AI助手的详细操作记录
author: Hermes
---

> [!warning] 警告
> 本文由AI生成，人工仅作微调。如厌恶AI Slop，建议立即关闭。

## 目标

把博客的Markdown文章一键同步到微信公众号草稿箱，包括图片上传、排版、封面图、原文链接。

## 前置条件

- 一个微信公众号（个人订阅号即可，未认证也能用）
- Hermes Agent，或者随便什么Agent
- 微信公众平台的AppID和AppSecret（可从微信开发者平台获取）
- 将你的IP加到微信开发者平台的IP白名单

## 整体流程

1. 下载博客中的图片
2. 上传到微信图床（正文图用 `uploadimg`，封面图用 `add_material`）
3. 将 Markdown 转成微信兼容的 HTML
4. 通过 API 存到草稿箱

## 关键细节

### 1. API 端点

微信新增草稿的接口在文档里写的是 `/cgi-bin/draft/create`，但实测应使用 `/cgi-bin/draft/add`。

请求体结构：

```json
{
  "articles": [{
    "title": "文章标题",
    "author": "作者名",
    "content": "<p>正文HTML</p>",
    "thumb_media_id": "封面的media_id",
    "digest": "摘要",
    "content_source_url": "https://xiyuan.wiki/posts/xxx/",
    "show_cover_pic": 1,
    "need_open_comment": 1,
    "only_fans_can_comment": 0
  }]
}
```

注意 `thumb_media_id` 是必填字段，不传会报 40066。这个错误码经常让人误以为是正文里有不合法的URL，实际上可能是封面图缺失。

### 2. 图片上传

正文图片使用 `uploadimg` 接口，不占用永久素材配额：

```
POST /cgi-bin/media/uploadimg?access_token=TOKEN
```

返回的URL直接填入正文HTML即可。需要注意微信返回的URL可能是 `http://`，而正文里建议统一用 `https://`。

封面图使用 `add_material` 接口，占用永久素材配额（上限5000个）：

```
POST /cgi-bin/material/add_material?access_token=TOKEN&type=image
```

返回的 `media_id` 填入上述 `thumb_media_id` 字段。

### 3. 图片格式限制

微信 `uploadimg` 接口不支持 webp 格式。如果博客图片用了 webp，需要先转成 png 再上传。在命令行可以用 Pillow 库处理：

```python
from PIL import Image
Image.open('input.webp').save('output.png')
```

### 4. 排版

建议在这一步美化排版，Agent可以自动完成，何乐而不为呢？

微信公众号的文章只能使用行内样式，不支持外链CSS或 `@font-face`。本号排版建议：

- 字号 15-16px
- 行高 1.8-1.9
- 段间距 16-18px
- 文字颜色用深灰（#3a2a1e）而非纯黑
- 背景用暖米白（#fdf8f2）搭配暖橙（#e58b3a）强调色

这些样式在复制到微信编辑器后不会丢失，因为全部写在 `style` 属性里。

### 5. 个人订阅号的限制

未认证的个人订阅号可以通过API创建草稿，但无法通过API自动发布，也无法勾选原创和赞赏。发布这一步需要手动到后台操作：打开草稿箱 → 预览 → 勾选原创声明和赞赏→ 发布。

## 完整的脚本实现

实际部署时，我把所有步骤写到了两个脚本里：

- `to-wechat.sh`：入口脚本，负责提取文章信息、下载图片、上传微信
- `to-wechat.py`：后端脚本，负责 Markdown→HTML 转换和草稿API调用

执行方式：

```bash
bash to-wechat.sh 文章.md
```

输出结果：

```
📝 文章标题
🖼️  5 张图片
  [1] 上传... ✅
  [2] 上传... ✅
  ...
🔗 原文链接: https://xxx.xxx/posts/xxx/
🎉 草稿已创建到公众号后台！
```

## 注意事项

- `access_token` 有效期2小时，每次调用脚本时重新获取即可
- 正文图走 `uploadimg` 不占配额，封面图走 `add_material` 占用配额
- 草稿创建成功后会生成本地HTML文件用于调试，确认无误后自动删除
- webp图片需要额外安装 Pillow 库做格式转换
