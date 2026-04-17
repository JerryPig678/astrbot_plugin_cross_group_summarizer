

<div align="center">

# AstrBot Plugin: Group Summary (群聊总结)

![Visitor Count](https://visitor-badge.laobi.icu/badge?page_id=zhoufan47.astrbot_plugin_qq_group_summary)
![AstrBot Plugin](https://img.shields.io/badge/AstrBot-Plugin-green)
![Python](https://img.shields.io/badge/Python-3.13+-blue)
![License](https://img.shields.io/badge/License-AGPLv3-orange)

**一款清新美观的群聊总结生成器，支持数据可视化与 AI 智能摘要**

</div>

## 📖 简介

**Group Summary** 是一个为 AstrBot 设计的群聊总结插件。它利用 OneBot 11 (NapCat) API 回溯群聊历史消息，通过 Python 本地进行数据统计（活跃用户、发言趋势），并调用 LLM（大语言模型）对聊天内容进行语义总结。

最终结果将渲染为一张精美的 **HTML 图片** 发送给用户，包含统计图表、话题摘要以及 AI 的“悄悄话”点评。

P.S. 其实本质是个小维日记的超级青春版

### ✨ 核心特性

* **无需本地数据库**：直接通过 API 分页拉取漫游消息，即装即用，无数据负担。
* **精美可视化**：生成包含“活跃之星 Top5”。
* **AI 智能总结**：自动提取群内主要话题（Topic）及时间段。
* **Markdown 渲染**：支持在总结内容中渲染加粗、代码块等 Markdown 语法。
* **双模式触发**：支持指令 `/总结群聊` 及自然语言（Function Call）触发。
* **个性化配置**：支持自定义机器人人设名称、总结时间范围等。

## 🖼️ 效果预览

>
> ![预览图](https://i.imgs.ovh/2026/01/17/yTJQTt.jpeg)
## 🛠️ 安装与依赖

### 1. 基础环境
确保您的 AstrBot 正常运行，并且连接的上游（如 NapCatQQ）支持 `get_group_msg_history` (获取群消息历史) API。

### 2. 安装插件
将本插件文件夹 `group_summary` 放入 AstrBot 的 `data/plugins/` 目录下。


```bash
/AstrBot/data/plugins/group_summary/
├── __init__.py
├── _conf_schema.json
├── main.py
└── requirements.txt
```
### 3. 参数设置
进入AstrBot webui进行相关参数设置。

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码


## ❤️ 鸣谢
- 感谢 **AstrBot** 框架和 **AstrBot T2I Service** 。
- 受 **Loping151** 的启发，开发了本插件。"# astrbot_plugin_cross_group_summarizer" 
