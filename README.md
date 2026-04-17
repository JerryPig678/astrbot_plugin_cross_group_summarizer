<div align="center">

# AstrBot Plugin: Cross Group Summarizer (跨群监控归档)

![AstrBot Plugin](https://img.shields.io/badge/AstrBot-Plugin-green)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-AGPLv3-orange)

**一款跨群监控、定时总结、文件归档的群聊管理插件**

</div>

## 📖 简介

**Cross Group Summarizer** 是一个为 AstrBot 设计的跨群监控归档插件。它可以监控多个群聊的消息，定时生成精炼总结并发送到指定目标群，同时支持文件归档功能。

### ✨ 核心特性

- **多群监控**：支持同时监控多个群聊，统一汇总到一个目标群
- **定时总结**：每天固定时间自动生成总结，支持自定义时间点
- **智能摘要**：调用 LLM 提取重要通知和消息总结，分点精炼概括
- **合并转发**：总结内容以合并转发消息形式发送，清晰美观
- **T2I 图片**：生成精美的粉色系小猪主题总结图片
- **文件归档**：支持将图片/文件归档到目标群文件夹
- **增量获取**：只获取上次总结后的新消息，避免重复

## 📁 项目结构

```
astrbot_plugin_cross_group_summarizer/
├── main.py                 # 主插件代码
├── metadata.yaml           # 插件元数据
├── _conf_schema.json       # 配置项定义
├── requirements.txt        # Python 依赖
├── templates/
│   └── report.html         # HTML 总结模板
├── CHANGELOG.md            # 更新日志
├── LICENSE                 # 许可证
└── README.md               # 说明文档
```

## 🛠️ 安装与配置

### 1. 环境要求

- AstrBot 正常运行
- 连接的上游（如 NapCatQQ）支持以下 API：
  - `get_group_msg_history` - 获取群消息历史
  - `send_group_forward_msg` - 发送合并转发消息
  - `upload_group_file` - 上传群文件
  - `create_group_file_folder` - 创建群文件夹

### 2. 安装插件

将插件文件夹放入 AstrBot 的 `data/plugins/` 目录下：

```bash
/AstrBot/data/plugins/astrbot_plugin_cross_group_summarizer/
```

### 3. 配置参数

在 AstrBot WebUI 中配置以下参数：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `monitored_groups` | 监控的群聊列表（群号） | `123456789,987654321` |
| `target_group` | 发送总结的目标群 | `111222333` |
| `summary_schedule` | 定时总结时间（24小时制） | `22:00` |
| `summary_hours` | 总结时间范围（小时） | `24` |
| `max_msg_count` | 最大分析消息量 | `500` |
| `provider_id` | LLM 提供商 ID | 留空使用默认 |
| `bot_name` | 机器人名称 | `BOT` |

## 📝 使用方法

### 指令列表

| 指令 | 说明 | 权限 |
|------|------|------|
| `/归档总结 [小时]` | 手动触发总结 | 管理员 |
| `/归档文件` | 回复图片/文件消息归档到目标群 | 管理员 |
| `/归档状态` | 查看当前配置状态 | 管理员 |

### 使用流程

1. **配置监控群和目标群**：在 WebUI 中设置 `monitored_groups` 和 `target_group`
2. **设置定时时间**：配置 `summary_schedule`（如 `22:00`）
3. **自动运行**：每天固定时间自动总结并发送到目标群
4. **手动触发**：使用 `/归档总结` 指令立即生成总结
5. **文件归档**：回复图片/文件消息后发送 `/归档文件` 进行归档

## 🎨 总结输出

### 输出格式

1. **合并转发消息**：包含群名、时间范围、重要通知、消息总结
2. **T2I 图片**：精美的粉色系小猪主题总结卡片
3. **群文件上传**：总结图片自动上传到群文件夹

### 总结内容

- **重要通知**：提取群内通知、公告、重要信息，分点列出
- **消息总结**：分点概括群内讨论的主要内容，包含时间段

## ❤️ 鸣谢

### 原项目致谢

本项目基于 [astrbot_plugin_qq_group_summary](https://github.com/zhoufan47/astrbot_plugin_qq_group_summary) 进行二次开发，感谢原作者 **zhoufan47** 的开源贡献！

原项目提供了以下核心功能的参考实现：
- 群消息历史获取逻辑
- LLM 调用与 JSON 解析
- HTML 模板渲染

### 框架致谢

- 感谢 **AstrBot** 框架提供的插件开发支持
- 感谢 **AstrBot T2I Service** 提供的文转图服务

## 📄 许可证

本项目采用 AGPLv3 许可证，详见 [LICENSE](LICENSE) 文件。

## 👥 贡献指南

- 🌟 Star 这个项目！
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

---

<div align="center">

**Made with ❤️ by JerryPig678**

</div>
