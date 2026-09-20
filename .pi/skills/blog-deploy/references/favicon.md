# Favicon — 圆形透明黑鸟黄喙

## 当前状态

| 文件 | 路径 | 说明 |
|------|------|------|
| `favicon.png` | `/public/favicon.png` | 32x32 RGBA, 圆形透明底 |
| `favicon.ico` | `/public/favicon.ico` | 32x32 ICO (从 PNG 转换) |

HTML 引用（`src/layouts/Layout.astro`）：
```html
<link rel="icon" type="image/png" href={getAssetPath("favicon.png")} />
```
浏览器优先使用 PNG 格式；ICO 作为兼容兜底（旧版 IE 等）。

## 设计

- 黑鸟黄喙（黑色 = 全不透明，鸟喙/眼睛 = 金黄色）
- 圆形裁切，圆外全透明
- 边缘通过 4x 超采样抗锯齿实现平滑过渡
- **鸟不变色**（亮暗模式下都是黑鸟）

## 工作流原则

**用户出设计稿，agent 只做缩放+部署。** 用户用自有工具（如 Photoshop、Figma、在线编辑器）完成透明背景设计，agent 不应尝试用 Pillow 抠图/加透明背景——用户手工做的效果更好，代码处理容易产生锯齿。

## 重建流程

### 1. 处理用户交付的源图

用户交付的通常是高分辨率（如 2048×2048）的**调色板 PNG（Mode P）**，已有透明背景（通过调色板索引标记透明）。关键步骤：

```python
from PIL import Image

img = Image.open("原始-favicon.png")  # Mode P, 2048x2048
img_rgba = img.convert('RGBA')       # 调色板模式→RGBA，透明索引自动保留
favicon = img_rgba.resize((32, 32), Image.LANCZOS)
```

> ⚠️ **不要用 Pillow 自己抠图/加透明背景**。用户手动做的透明效果比代码处理的好得多，没有锯齿/白边问题。agent 的任务只是缩放和部署。验证时检查四角 alpha=0 确认透明生效即可。

```python
from PIL import Image

img = Image.open("原始-favicon.png")  # 高分辨率 PNG, 已有透明区域
img_rgba = img.convert('RGBA')       # 调色板模式转 RGBA（透明通道保留）
favicon = img_rgba.resize((32, 32), Image.LANCZOS)

# 验证
pixels = list(favicon.getdata())
transparent = sum(1 for p in pixels if p[3] == 0)
opaque = sum(1 for p in pixels if p[3] >= 254)
anti_alias = sum(1 for p in pixels if 0 < p[3] < 254)
print(f"透明: {transparent}, 不透明: {opaque}, 抗锯齿: {anti_alias}")

favicon.save("favicon.png")
favicon.save("favicon.ico", format="ICO", sizes=[(32,32)])
```

关键参数：
- `Image.LANCZOS` — 高质量下采样，保持边缘平滑
- 检查四角 alpha=0 确认透明生效
- 验证 `anti_alias > 0` 确保边缘有过渡

### 2. 部署

用 SCP 上传到宿主机：  
```bash
scp favicon.png ubuntu@172.17.0.1:/home/ubuntu/blog-astro/public/favicon.png
scp favicon.ico ubuntu@172.17.0.1:/home/ubuntu/blog-astro/public/favicon.ico
```

### 3. 强制刷新浏览器缓存

用 `?v=N`（N 递增）参数追加到 favicon 链接，跳过浏览器缓存。修改 `src/layouts/Layout.astro`：

```astro
<!-- 改前 -->
<link rel="icon" type="image/png" href={getAssetPath("favicon.png")} />
<!-- 改后 -->
<link rel="icon" type="image/png" href={getAssetPath("favicon.png") + "?v=2"} />
```

> 每次更新 favicon 后 `v` 的数字 +1（v=1 → v=2 → v=3 …），只触发一次重新下载，之后正常走缓存。

## 验证

部署后硬刷新（Ctrl+F5 / Cmd+Shift+R）[xiyuan.wiki](https://xiyuan.wiki) 看浏览器标签页图标。
⚠️ Telegram 发图会压成 JPG 丢透明通道——无法通过 Telegram 预览确认透明效果，直接看网站或下载文件本地打开。
