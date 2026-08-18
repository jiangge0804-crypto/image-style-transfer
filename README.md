# image-style-transfer · 图片风格转换技能

> 一个开箱即用的 **AI Agent Skill**：上传任意图片，说一句风格名，自动转换为 27 种精心调校的画风。
> 你不需要会写提示词，中文随口一说就行。

[![Skill](https://img.shields.io/badge/type-Agent%20Skill-blue)](https://github.com) [![Styles](https://img.shields.io/badge/styles-27-green)](image-style-transfer/references/style-library.json) [![Engine](https://img.shields.io/badge/engine-Jimeng%20Seedream%205.0%20Lite-orange)](image-style-transfer/scripts/generate_image_seedream.py) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 这是什么

`image-style-transfer` 是一个遵循 **Agent Skill 规范**（SKILL.md + references 资产文件）的技能包。把它安装到任何支持 Skills 的 AI 助手后，助手会获得一个「图片风格转换器」：

```
你：上传一张照片 +「转成吉卜力风」
AI：自动匹配风格库 → 调用生图引擎 → 返回转换后的图片
```

**默认生图引擎：即梦「图片 5.0 Lite」= 火山方舟 `doubao-seedream-5-0-lite-260128`**——skill 自带 [`scripts/generate_image_seedream.py`](image-style-transfer/scripts/generate_image_seedream.py)，国内直连 [火山方舟 ark.cn-beijing.volces.com](https://console.volcengine.com/ark)，仅需配置 `ARK_API_KEY` 即可使用；无 Key 或 API 不可用时，自动降级到 [`scripts/generate_image_minimax.py`](image-style-transfer/scripts/generate_image_minimax.py) (MiniMax image-01)，再不行就降级到宿主 Agent 自带的通用图生图工具。

```
你：上传一张照片 +「转成吉卜力风」
  ↓
Agent 读 style-library.json 匹配 → 取出 prompt + input_fidelity
  ↓
调用 scripts/generate_image_seedream.py (--image <你的照片> --prompt <库里提示词>)
  ↓
国内直连即梦 Seedream 5.0 Lite → 自动按原图比例输出 2K 像素 → 返回生成图
```

**核心资产**是 [`references/style-library.json`](image-style-transfer/references/style-library.json)：27 个风格条目，每个都包含——

| 字段 | 说明 |
|------|------|
| `id` / `name_zh` / `name_en` | 风格标识与中英文名 |
| `aliases` | 中文触发词别名（说任何一个都能命中） |
| `prompt` | 精心调校的风格提示词原文 |
| `input_fidelity` | 设计意图标注（`high` 保留原图 / `medium` 保留构图 / `low` 允许重构） |

## 内置 27 种风格

### 🎨 动漫插画类（10）
| 风格 | 触发词示例 |
|------|-----------|
| 吉卜力风 | 宫崎骏、吉卜力 |
| 新海诚风 | 新海诚、你的名字 |
| 赛璐璐动画风 | 动画风、日系动画 |
| 日式黑白漫画 | 漫画、黑白漫画 |
| 美式漫画风 | 美漫、漫威、DC |
| 厚涂插画 | 厚涂、油画感 |
| 扁平插画 | 扁平、矢量插画 |
| Q版二头身 | Q版、萌系、二头身 |
| 浮世绘 | 和风、木版画 |
| 赛博朋克动漫 | 赛博朋克、霓虹 |

### ✏️ 生活创意类（6）
| 风格 | 触发词示例 | 效果 |
|------|-----------|------|
| 丑萌涂鸦插画 | 丑萌、沙雕、表情包风 | 蜡笔潦草手稿感，比例扭曲、五官滑稽 |
| Colorwalk人物冰箱贴 | 冰箱贴、人物冰箱贴 | 从照片提取人物做成旅行纪念冰箱贴图标 |
| ins手绘感plog | ins风、plog、手绘笔记 | 原图上加白色手绘注释+轮廓线，Instagram story 质感 |
| 治愈风插画 | 治愈、治愈系 | 大色块+颗粒肌理，童趣意识流 |
| 童趣涂鸦插画 | 童趣、儿童涂鸦 | 大胆俏皮配色，白纸上的异想天开 |
| 平面简笔手绘 | 简笔画、儿童简笔 | 稚嫩摇摆线条，原始触觉感 |

### 🌆 潮流复古类（4）
| 风格 | 触发词示例 | 效果 |
|------|-----------|------|
| CityPop插画 | citypop、昭和风 | 80年代日本动画美学+高饱和复古色块 |
| 波普风格插画 | 波普、半色调网点 | 1950-60年代儿童绘本印刷质感 |
| 日系几何平面 | 丝网印刷、90年代复古 | 几何块面堆叠+丝网印刷风 |
| 多巴胺插画 | 多巴胺 | 活泼亮眼多巴胺配色+柔和色块 |

### 🏮 国风艺术类（3）
| 风格 | 触发词示例 | 效果 |
|------|-----------|------|
| 国风肌理插画 | 国风、蓝紫渐变 | 扁平矢量+磨砂噪点肌理+马卡龙渐变 |
| 国潮鎏金插画 | 国潮、鎏金、敦煌风 | 翠绿洒金+敦煌色彩+骨法描线 |
| 超现实铜版画 | 铜版画、版画 | 极繁主义蓝色线条版画，超现实自然融合 |

### 🏛️ 建筑海报类（4）
| 风格 | 触发词示例 | 效果 |
|------|-----------|------|
| 建筑信息图插画 | 建筑插画、信息图 | 建筑重塑为测绘档案风信息图（含测量线、比例尺） |
| 概念性分解建筑 | 爆炸图、建筑分解 | 超精细3D渲染轴向爆炸图+技术标注层 |
| 建筑冰箱贴设计 | 建筑冰箱贴、地标冰箱贴 | 提取地标建筑做成冰箱贴图标 |
| 高端插画海报 | 轻奢海报、建筑海报 | 轻奢简约风竖版艺术海报，杂志封面调性 |

## 安装

### 前提

- 一个能调用图生图的 Agent 环境（WorkBuddy、Claude Code、Cursor 等均可）
- 若使用默认的 **即梦 Seedream 5.0 Lite** 引擎：申请一个 [火山方舟 API Key](https://console.volcengine.com/ark/region:cn-beijing/apiKey)，写到 shell 配置：
  ```bash
  echo 'export ARK_API_KEY="你的key"' >> ~/.zshrc && source ~/.zshrc
  ```
  无 Key 时 Agent 会自动降级到 MiniMax image-01（需另外配 `MINIMAX_API_KEY`），再不行就降级到宿主自带的图生图工具。

### 安装

```bash
git clone https://github.com/jiangge0804-crypto/image-style-transfer.git
cp -r image-style-transfer/image-style-transfer ~/.workbuddy/skills/
```

安装后重启会话或新开对话即可生效。

## 使用

安装后无需记 skill 名，自然说话即可触发：

- 「把这张照片**转成吉卜力风**」
- 「给我来个**冰箱贴**」（自动匹配 Colorwalk人物冰箱贴 或 建筑冰箱贴，按图片内容选择）
- 「这张建筑照做成**轻奢海报**」
- 「这3张图都转成**治愈风**」（批量：多图单风格）
- 「这张图分别试试**CityPop**和**波普**」（批量：单图多风格对比）

Agent 会读取风格库匹配触发词 → 取出调校好的提示词 → 按该风格配置的保真度调用图生图 → 返回结果。

## 引擎说明

| 引擎 | 优点 | 缺点 | 何时使用 |
|------|------|------|---------|
| **即梦 Seedream 5.0 Lite** = `doubao-seedream-5-0-lite-260128`（**默认**） | 主体一致性强、人物面部保留好；国内直连；按张 ¥0.22 便宜；图生图支持 base64；可输出 1K/2K/3K/4K | 不接受 `size: adaptive` 关键字（需传 `WIDTHxHEIGHT` 或 2k/3k/4k）；图生图中可能出 AI 文字伪影 | 默认首选；尤其人像、Q版/丑萌需要保留角色的场景；中文/国风 prompt 效果也好 |
| **MiniMax image-01**（备选 1） | 主体一致性强；国内直连 | 文字伪影相对更明显；图生图只支持 1 张 reference | 即梦 API 报错或缺 `ARK_API_KEY` 时回退 |
| **宿主自带图生图**（备选 2） | 三档 `input_fidelity` 可精细控制构图保留度 | 主体一致性弱于上述两个 | 用户明确要求时 |

**关于 `input_fidelity` 字段**：即梦和 MiniMax 的图生图 API 都不直接接收三档保真度参数。该字段被保留为「风格作者设计意图标注」——`high` 风格的 prompt 会显式要求最大程度保留原图，`low` 风格的 prompt 则允许画面重构。

**关于 AI 文字伪影**：即梦和 MiniMax 在国风/水墨/古风/英文招牌类风格中偶尔会生成假字。规避方法：自定义/调整这类风格时在 prompt 里加 `no text, no letters, no characters, no watermark`。

## 扩充风格库

往 [`references/style-library.json`](image-style-transfer/references/style-library.json) 的 `styles` 数组追加条目即可，保持相同字段结构：

```json
{
  "id": "my-new-style",
  "name_zh": "我的新风格",
  "name_en": "My New Style",
  "category": "自定义",
  "aliases": ["触发词1", "触发词2"],
  "prompt": "风格提示词，中英文均可……",
  "input_fidelity": "medium"
}
```

`input_fidelity` 选择建议：
- `high` — 在原图上做加法（如加注释、描边），最大保留原图
- `medium` — 保留构图与主体，重绘画风（默认）
- `low` — 允许重构画面（改头身比、提取元素做图标、爆炸图等）

## 项目结构

```
image-style-transfer/
├── README.md                          # 本文件
├── LICENSE                            # MIT
└── image-style-transfer/              # 技能包本体
    ├── SKILL.md                       # Agent 工作流指令（匹配→转换→批量→呈现）
    ├── scripts/
    │   ├── generate_image_seedream.py  # 即梦 Seedream 5.0 Lite 生图脚本（默认引擎，Ark API）
    │   └── generate_image_minimax.py   # MiniMax image-01 生图脚本（备选引擎 1）
    └── references/
        └── style-library.json         # 27 种风格提示词库（核心资产）
```

## 许可

[MIT](LICENSE) — 风格提示词可自由使用、修改、二次分发。欢迎 PR 扩充风格库 🎉
