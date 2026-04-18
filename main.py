import asyncio
import json
import os
import re
import time
import datetime
import traceback
from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


def _parse_llm_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            json_str = match.group()
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    raise ValueError("无法从 LLM 回复中提取有效的 JSON 数据")


SUMMARY_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>群聊总结</title>
    <style>
        :root {
            --pink-50: #FDF2F8; --pink-100: #FCE7F3; --pink-200: #FBCFE8;
            --pink-300: #F9A8D4; --pink-400: #F472B6; --pink-500: #EC4899;
            --pink-600: #DB2777; --pink-700: #BE185D;
            --gray-50: #FAFAFA; --gray-100: #F4F4F5; --gray-200: #E4E4E7;
            --gray-400: #A1A1AA; --gray-500: #71717A; --gray-700: #3F3F46; --gray-800: #27272A;
            --amber-50: #FFFBEB; --amber-100: #FEF3C7; --amber-500: #F59E0B; --amber-700: #B45309;
            --white: #FFFFFF;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            --radius-lg: 0.75rem; --radius-xl: 1rem; --radius-2xl: 1.5rem;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, var(--pink-100) 0%, var(--pink-200) 50%, var(--pink-300) 100%);
            min-height: 100vh; padding: 24px; line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .container { max-width: 480px; margin: 0 auto; }
        .card { 
            background: var(--white); 
            border-radius: var(--radius-2xl); 
            box-shadow: var(--shadow-xl); 
            overflow: hidden;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .header {
            background: linear-gradient(135deg, var(--pink-500) 0%, var(--pink-600) 100%);
            padding: 32px 24px; text-align: center; position: relative; overflow: hidden;
        }
        .pig-icon { 
            width: 72px; height: 72px; 
            margin: 0 auto 12px;
        }
        .pig-icon svg {
            width: 100%; height: 100%;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.15));
        }
        .header-title { 
            color: var(--white); 
            font-size: 22px; 
            font-weight: 700; 
            margin-bottom: 6px; 
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .header-subtitle { 
            color: rgba(255,255,255,0.9); 
            font-size: 13px; 
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .content { padding: 20px; }
        .stats-row { 
            display: flex; 
            justify-content: center; 
            gap: 24px; 
            margin-bottom: 20px;
            padding: 16px;
            background: linear-gradient(135deg, var(--pink-50) 0%, var(--pink-100) 100%);
            border-radius: var(--radius-xl);
            border: 1px solid var(--pink-200);
        }
        .stat-item { text-align: center; min-width: 50px; }
        .stat-value { font-size: 24px; font-weight: 700; color: var(--pink-600); line-height: 1.2; }
        .stat-label { font-size: 12px; color: var(--gray-500); margin-top: 2px; }
        .stat-divider { width: 1px; background: var(--pink-200); }
        .section { margin-bottom: 20px; }
        .section-header { display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 2px solid var(--pink-100); }
        .section-icon { 
            width: 22px; height: 22px; border-radius: 50%; 
            background: var(--pink-500); color: var(--white);
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: bold; margin-right: 8px;
            flex-shrink: 0;
        }
        .section-title { font-size: 15px; font-weight: 600; color: var(--gray-800); }
        .summary-list { display: flex; flex-direction: column; gap: 10px; }
        .summary-item { 
            background: linear-gradient(135deg, var(--pink-50) 0%, var(--white) 100%); 
            border-radius: var(--radius-lg); 
            padding: 12px 14px; 
            border-left: 4px solid var(--pink-400); 
            box-shadow: var(--shadow-sm);
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .summary-time { 
            font-size: 11px; 
            font-weight: 600; 
            color: var(--pink-500); 
            margin-bottom: 4px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .summary-text { 
            font-size: 13px; 
            color: var(--gray-700); 
            line-height: 1.5;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .notice-box { 
            background: linear-gradient(135deg, var(--amber-50) 0%, var(--amber-100) 100%); 
            border-radius: var(--radius-lg); 
            padding: 14px; 
            border-left: 4px solid var(--amber-500);
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .notice-list { display: flex; flex-direction: column; gap: 8px; }
        .notice-item { 
            font-size: 13px; 
            color: var(--amber-700); 
            line-height: 1.5; 
            padding-left: 14px; 
            position: relative;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .notice-item::before { content: ""; position: absolute; left: 0; top: 7px; width: 5px; height: 5px; background: var(--amber-500); border-radius: 50%; }
        .footer { background: var(--pink-50); padding: 16px 24px; text-align: center; border-top: 1px solid var(--pink-100); }
        .footer-text { font-size: 12px; color: var(--pink-500); font-weight: 500; }
        .divider { height: 1px; background: linear-gradient(90deg, transparent, var(--pink-200), transparent); margin: 16px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <header class="header">
                <div class="pig-icon">
                    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                        <ellipse cx="50" cy="55" rx="35" ry="30" fill="#FFB6C1"/>
                        <ellipse cx="50" cy="55" rx="32" ry="27" fill="#FFC0CB"/>
                        <ellipse cx="50" cy="62" rx="14" ry="10" fill="#FFB6C1"/>
                        <circle cx="44" cy="60" r="2" fill="#FF69B4"/>
                        <circle cx="56" cy="60" r="2" fill="#FF69B4"/>
                        <ellipse cx="50" cy="68" rx="4" ry="2" fill="#FF69B4"/>
                        <circle cx="38" cy="45" r="6" fill="#FFB6C1"/>
                        <circle cx="62" cy="45" r="6" fill="#FFB6C1"/>
                        <circle cx="38" cy="45" r="4" fill="#FFC0CB"/>
                        <circle cx="62" cy="45" r="4" fill="#FFC0CB"/>
                        <circle cx="40" cy="48" r="2" fill="#333"/>
                        <circle cx="60" cy="48" r="2" fill="#333"/>
                        <circle cx="41" cy="47" r="0.8" fill="#fff"/>
                        <circle cx="61" cy="47" r="0.8" fill="#fff"/>
                        <ellipse cx="35" cy="25" rx="8" ry="10" fill="#FFB6C1"/>
                        <ellipse cx="65" cy="25" rx="8" ry="10" fill="#FFB6C1"/>
                        <ellipse cx="35" cy="25" rx="6" ry="8" fill="#FFC0CB"/>
                        <ellipse cx="65" cy="25" rx="6" ry="8" fill="#FFC0CB"/>
                        <ellipse cx="35" cy="28" rx="3" ry="4" fill="#FF69B4"/>
                        <ellipse cx="65" cy="28" rx="3" ry="4" fill="#FF69B4"/>
                        <path d="M 20 55 Q 15 50, 20 45" stroke="#FFB6C1" stroke-width="3" fill="none" stroke-linecap="round"/>
                        <path d="M 80 55 Q 85 50, 80 45" stroke="#FFB6C1" stroke-width="3" fill="none" stroke-linecap="round"/>
                        <path d="M 45 75 Q 50 78, 55 75" stroke="#FF69B4" stroke-width="2" fill="none" stroke-linecap="round"/>
                    </svg>
                </div>
                <h1 class="header-title">{{ group_name }} 群聊总结</h1>
                <p class="header-subtitle">{{ date }} / 最近 {{ hours }} 小时</p>
            </header>
            <main class="content">
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value">{{ summary_points|length }}</div>
                        <div class="stat-label">话题</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                        <div class="stat-value">{{ hours }}h</div>
                        <div class="stat-label">时长</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                        <div class="stat-value">{% if important_notices and important_notices[0] != "无" %}{{ important_notices|length }}{% else %}0{% endif %}</div>
                        <div class="stat-label">通知</div>
                    </div>
                </div>
                {% if important_notices and important_notices|length > 0 and important_notices[0] != "无" %}
                <section class="section">
                    <div class="section-header">
                        <div class="section-icon">!</div>
                        <h2 class="section-title">重要通知</h2>
                    </div>
                    <div class="notice-box">
                        <div class="notice-list">
                            {% for notice in important_notices %}
                            {% if notice and notice != "无" %}
                            <div class="notice-item">{{ notice }}</div>
                            {% endif %}
                            {% endfor %}
                        </div>
                    </div>
                </section>
                <div class="divider"></div>
                {% endif %}
                <section class="section">
                    <div class="section-header">
                        <div class="section-icon">S</div>
                        <h2 class="section-title">消息总结</h2>
                    </div>
                    <div class="summary-list">
                        {% for point in summary_points %}
                        <article class="summary-item">
                            <div class="summary-time">{{ point.time_range }}</div>
                            <p class="summary-text">{{ point.content }}</p>
                        </article>
                        {% endfor %}
                    </div>
                </section>
            </main>
            <footer class="footer">
                <p class="footer-text">{{ bot_name }} 为您生成</p>
            </footer>
        </div>
    </div>
</body>
</html>
'''


@register("group_archiver", "JerryPig678", "群聊监控归档", "1.0.0")
class GroupArchiverPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        
        self.max_msg_count = self.config.get("max_msg_count", 500)
        self.max_query_rounds = self.config.get("max_query_rounds", 20)
        self.bot_name = self.config.get("bot_name", "BOT")
        self.msg_token_limit = self.config.get("token_limit", 15000)
        
        monitored_groups_str = self.config.get("monitored_groups", "")
        self.monitored_groups = [g.strip() for g in monitored_groups_str.split(",") if g.strip()]
        
        self.target_group = self.config.get("target_group", "")
        self.summary_schedule = self.config.get("summary_schedule", "22:00")
        self.summary_hours = self.config.get("summary_hours", 24)
        
        self._scheduler_task = None
        self._last_summary_time = {}
        self._recent_media_files = []
        self._target_umo = None
        
        self._plugin_data_path = Path("data/plugin_data/group_archiver")
        self._plugin_data_path.mkdir(parents=True, exist_ok=True)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "templates", "report.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                self.html_template = f.read()
            logger.info(f"群聊总结: 成功加载模板: {template_path}")
        except FileNotFoundError:
            logger.warning(f"群聊总结: 未找到模板文件，使用内置模板")
            self.html_template = SUMMARY_TEMPLATE
        
        logger.info(f"群聊总结: 初始化完成，监控群: {self.monitored_groups}，目标群: {self.target_group}")

    async def _load_last_summary_time(self, group_id: str) -> float:
        try:
            data = await self.get_kv_data(f"last_summary_{group_id}")
            return data if data else 0
        except:
            return 0

    async def _save_last_summary_time(self, group_id: str, timestamp: float):
        try:
            await self.put_kv_data(f"last_summary_{group_id}", timestamp)
        except Exception as e:
            logger.error(f"群聊总结: 保存时间戳失败: {e}")

    async def fetch_group_history(self, bot, group_id: str, hours_limit: int = 24, since_timestamp: float = 0):
        all_messages = []
        message_seq = 0
        prev_message_seq = -1
        cutoff_time = time.time() - (hours_limit * 3600)
        
        if since_timestamp > 0:
            cutoff_time = max(cutoff_time, since_timestamp)

        logger.info(f"群聊总结: 开始获取群 {group_id} 消息，时间范围: {datetime.datetime.fromtimestamp(cutoff_time)}")

        for round_idx in range(self.max_query_rounds):
            if len(all_messages) >= self.max_msg_count:
                break

            try:
                params = {
                    "group_id": group_id,
                    "count": 200,
                    "message_seq": message_seq,
                    "reverseOrder": True,
                }
                logger.info(f"群聊总结: Round {round_idx+1}: 获取参数: {params}")
                
                resp = await bot.api.call_action("get_group_msg_history", **params)

                round_messages = resp.get("messages", [])
                if not round_messages:
                    logger.info(f"群聊总结: Round {round_idx+1}: 未获取到消息，退出循环")
                    break
                    
                batch_msgs = round_messages
                first_msg_time = batch_msgs[0].get("time", 0)
                last_msg_time = batch_msgs[-1].get("time", 0)
                
                if first_msg_time <= last_msg_time:
                    oldest_msg_time = first_msg_time
                    newest_msg_time = last_msg_time
                    message_seq = batch_msgs[0]["message_seq"]
                else:
                    oldest_msg_time = last_msg_time
                    newest_msg_time = first_msg_time
                    message_seq = batch_msgs[-1]["message_seq"]
                
                logger.info(f"群聊总结: Round {round_idx+1}: 最旧消息时间: {oldest_msg_time}")
                logger.info(f"群聊总结: Round {round_idx+1}: 最新消息时间: {newest_msg_time}")
                
                if message_seq == prev_message_seq:
                    logger.info(f"群聊总结: Round {round_idx+1}: message_seq未变化({message_seq})，退出循环")
                    break
                    
                prev_message_seq = message_seq
                    
                logger.info(f"群聊总结: 本次获取到的最旧一条message_seq:{message_seq}")
                logger.info(f"群聊总结: Round {round_idx+1}: 获取到 {len(batch_msgs)} 条消息")
                
                if not batch_msgs:
                    logger.info(f"群聊总结: Round {round_idx+1}: batch_msgs为空，退出循环")
                    break

                all_messages.extend(batch_msgs)

                if oldest_msg_time < cutoff_time:
                    logger.info(f"群聊总结: Round {round_idx+1}: 已到达时间截止点，退出循环")
                    break

            except Exception as e:
                logger.error(f"群聊总结: Error: {traceback.format_exc()}")
                logger.info(f"群聊总结: Fetch loop error: {e}")
                break

        filtered_messages = [m for m in all_messages if m.get("time", 0) >= cutoff_time]
        return filtered_messages

    def process_messages(self, messages: list, hours_limit: int = 24):
        cutoff_time = time.time() - (hours_limit * 3600)
        logger.info(f"群聊总结: 开始处理 {len(messages)} 条消息")
        
        valid_msgs = []
        filter_date_count = 0
        filter_sys_msg_count = 0
        media_files = []
        
        for msg in messages:
            ts = msg.get("time", 0)
            if ts < cutoff_time:
                filter_date_count += 1
                continue

            raw_msg = msg.get("raw_message", "")
            sender = msg.get("sender", {})
            nickname = sender.get("card") or sender.get("nickname") or "未知用户"
            
            if "[CQ:image" in raw_msg:
                match = re.search(r'\[CQ:image,file=([^\],]+)', raw_msg)
                if match:
                    img_url = match.group(1)
                    media_files.append({
                        "type": "image",
                        "url": img_url,
                        "time": ts,
                        "name": nickname
                    })
            
            if "[CQ:file" in raw_msg:
                match = re.search(r'\[CQ:file,file=([^\],]+)', raw_msg)
                url_match = re.search(r'\[CQ:file[^]]*url=([^\],]+)', raw_msg)
                if match:
                    file_id = match.group(1)
                    file_url = url_match.group(1) if url_match else file_id
                    media_files.append({
                        "type": "file",
                        "url": file_url,
                        "file_id": file_id,
                        "time": ts,
                        "name": nickname
                    })
            
            if "[CQ:" in raw_msg:
                filter_sys_msg_count += 1
                continue

            content = raw_msg or ""

            valid_msgs.append({
                "time": ts,
                "name": nickname,
                "content": content
            })

        chat_log = "\n".join([
            f"[{datetime.datetime.fromtimestamp(m['time']).strftime('%Y.%m.%d %H:%M')}] {m['name']}: {m['content']}"
            for m in valid_msgs
        ])
        
        logger.info(f"群聊总结: 共获取到{len(valid_msgs)}条有效消息,过滤{filter_date_count}条时间超出限制消息,过滤{filter_sys_msg_count}条系统消息,收集{len(media_files)}个媒体文件")
        return valid_msgs, chat_log, media_files

    async def generate_summary(self, chat_log: str, group_name: str, hours: int) -> dict:
        if len(chat_log) > self.msg_token_limit:
            logger.warning(f"群聊总结: LLM 日志长度超过限制:{len(chat_log)}，已截断。")
            chat_log = chat_log[:self.msg_token_limit]

        prompt = f"""
你是一个班群记录员"{self.bot_name}"。请根据以下的班群聊天记录（最近{hours}小时），生成一份精炼的总结。

【要求】：
1. **重要通知**：提取群内的通知、公告、重要信息，按类别分类：
   - 学科类通知（作业、考试等）：标注学科名
   - 事务类通知（体检、返校、缴费等）：统一归为"事务通知"
   - 每点不超过25字，如果没有则填"无"
   - 格式：{{"category": "学科名或事务通知", "content": "通知内容"}}
   
2. **分学科总结**：按学科分类概括群内讨论的内容。学科包括：语文、数学、英语、物理、化学、生物、历史、地理、政治、其他。
   - 每个学科如果有相关讨论，则列出（时间+内容，不超过30字）
   - 没有讨论的学科不要列出
   - 格式：{{"subject": "学科名", "time_range": "时间", "content": "内容"}}
   
3. 严格返回纯JSON格式，不要使用markdown代码块：
{{"important_notices": [{{"category": "数学", "content": "明天交作业"}}, {{"category": "事务通知", "content": "周五体检"}}], "summary_points": [{{"subject": "数学", "time_range": "...", "content": "..."}}]}}

【聊天记录】：
{chat_log}
"""

        try:
            provider = self.context.get_provider_by_id(
                self.config.get("provider_id")) or self.context.get_using_provider()
            if not provider:
                logger.error("群聊总结: 未配置 LLM 提供商")
                return {"summary_points": [], "important_notices": ["未配置LLM提供商"]}

            response = await provider.text_chat(prompt, session_id=None)
            logger.info(f"群聊总结: LLM 原始回复: {response.completion_text}")
            
            cleaned_response = self._clean_llm_response(response.completion_text)
            analysis_data = _parse_llm_json(cleaned_response)
            return analysis_data
        except Exception as e:
            logger.error(f"群聊总结: LLM Error: {traceback.format_exc()}")
            return {"summary_points": [], "important_notices": [f"生成失败: {str(e)}"]}

    def _clean_llm_response(self, text: str) -> str:
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        return text

    async def render_summary_image(self, group_name: str, analysis_data: dict, hours: int) -> str:
        try:
            render_data = {
                "group_name": group_name,
                "date": datetime.datetime.now().strftime("%Y.%m.%d"),
                "hours": hours,
                "summary_points": analysis_data.get("summary_points", []),
                "important_notices": analysis_data.get("important_notices", []),
                "bot_name": self.bot_name
            }
            options = {"quality": 95, "device_scale_factor_level": "ultra", "viewport_width": 500}
            img_url = await self.html_render(self.html_template, render_data, options=options)
            logger.info(f"群聊总结: 图片渲染成功")
            return img_url
        except Exception as e:
            logger.error(f"群聊总结: 图片渲染失败: {traceback.format_exc()}")
            return None

    async def send_summary_to_target(self, group_name: str, analysis_data: dict, hours: int, media_files: list = None):
        try:
            img_url = await self.render_summary_image(group_name, analysis_data, hours)
            
            platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
            if not platform:
                logger.error("群聊总结: 未找到 AIOCQHTTP 平台")
                return False
            
            bot = platform.get_client()
            
            if img_url:
                try:
                    await bot.api.call_action(
                        "send_group_msg",
                        group_id=int(self.target_group),
                        message=f"[CQ:image,file={img_url}]"
                    )
                    logger.info(f"群聊总结: 图片发送成功")
                except Exception as e:
                    logger.error(f"群聊总结: 图片发送失败: {e}")
                
                try:
                    now = datetime.datetime.now()
                    file_name = f"summary_{group_name}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                    
                    download_result = await bot.api.call_action(
                        "download_file",
                        url=img_url,
                        thread_count=1
                    )
                    
                    if download_result:
                        file_path = download_result.get("file", "")
                        if file_path:
                            folder_name = "群聊总结"
                            folder_id = await self.get_or_create_folder(bot, self.target_group, folder_name)
                            await self.upload_group_file(bot, self.target_group, file_path, file_name, folder_id)
                            logger.info(f"群聊总结: 总结图片已上传到群文件夹")
                except Exception as e:
                    logger.error(f"群聊总结: 上传总结图片失败: {e}")
            
            if media_files and len(media_files) > 0:
                await self.send_media_forward(bot, group_name, media_files)
            
            return True
        except Exception as e:
            logger.error(f"群聊总结: 发送总结失败: {traceback.format_exc()}")
            return False

    async def send_media_forward(self, bot, group_name: str, media_files: list):
        try:
            if not media_files:
                return
            
            max_files = min(len(media_files), 20)
            media_files = media_files[:max_files]
            
            self._recent_media_files = media_files
            
            image_count = sum(1 for f in media_files if f.get("type") == "image")
            file_count = sum(1 for f in media_files if f.get("type") == "file")
            
            nodes = []
            
            nodes.append({
                "type": "node",
                "data": {
                    "uin": str(bot.self_id) if hasattr(bot, 'self_id') else '0',
                    "name": self.bot_name,
                    "content": [
                        {"type": "text", "data": {"text": f"【{group_name}】媒体文件 (图片{image_count}张, 文件{file_count}个)"}},
                        {"type": "text", "data": {"text": "使用 /保存 <序号> 保存文件"}}
                    ]
                }
            })
            
            for idx, media in enumerate(media_files, 1):
                media_url = media.get("url", "")
                media_name = media.get("name", "未知用户")
                media_time = media.get("time", 0)
                media_type = media.get("type", "image")
                file_id = media.get("file_id", "")
                
                if media_url:
                    time_str = datetime.datetime.fromtimestamp(media_time).strftime('%H:%M') if media_time else ""
                    if media_type == "image":
                        nodes.append({
                            "type": "node",
                            "data": {
                                "uin": str(bot.self_id) if hasattr(bot, 'self_id') else '0',
                                "name": f"{idx}. {media_name} {time_str}",
                                "content": [{"type": "image", "data": {"file": media_url}}]
                            }
                        })
                    else:
                        nodes.append({
                            "type": "node",
                            "data": {
                                "uin": str(bot.self_id) if hasattr(bot, 'self_id') else '0',
                                "name": f"{idx}. {media_name} {time_str}",
                                "content": [{"type": "file", "data": {"file": file_id or media_url, "name": file_id or media_url}}]
                            }
                        })
            
            await bot.api.call_action("send_group_forward_msg", group_id=int(self.target_group), messages=nodes)
            logger.info(f"群聊总结: 合并转发媒体文件成功，共 {len(media_files)} 个")
        except Exception as e:
            logger.error(f"群聊总结: 合并转发媒体文件失败: {traceback.format_exc()}")

    async def get_or_create_folder(self, bot, group_id: str, folder_name: str) -> str:
        try:
            resp = await bot.api.call_action("get_group_root_files", group_id=int(group_id))
            folders = resp.get("folders", [])
            for folder in folders:
                if folder.get("folder_name") == folder_name:
                    logger.info(f"群聊总结: 找到已存在的文件夹: {folder_name}")
                    return folder.get("folder_id", "")
            
            try:
                await bot.api.call_action(
                    "create_group_file_folder",
                    group_id=int(group_id),
                    name=folder_name
                )
                logger.info(f"群聊总结: 创建文件夹成功: {folder_name}")
            except Exception:
                logger.warning(f"群聊总结: 创建文件夹失败，可能已存在")
            
            resp = await bot.api.call_action("get_group_root_files", group_id=int(group_id))
            folders = resp.get("folders", [])
            for folder in folders:
                if folder.get("folder_name") == folder_name:
                    return folder.get("folder_id", "")
            
            return ""
        except Exception as e:
            logger.error(f"群聊总结: 获取/创建文件夹失败: {e}")
            return ""

    async def upload_group_file(self, bot, group_id: str, file_path: str, file_name: str, folder_id: str = None):
        try:
            params = {
                "group_id": int(group_id),
                "file": file_path,
                "name": file_name
            }
            if folder_id:
                params["folder"] = folder_id
            await bot.api.call_action("upload_group_file", **params)
            logger.info(f"群聊总结: 文件上传成功: {file_name}")
            return True
        except Exception as e:
            logger.error(f"群聊总结: 文件上传失败: {traceback.format_exc()}")
            return False

    async def send_file_to_group(self, bot, group_id: str, file_url: str, file_name: str):
        try:
            message = [
                {
                    "type": "file",
                    "data": {
                        "file": file_url,
                        "name": file_name
                    }
                }
            ]
            await bot.api.call_action("send_group_msg", group_id=int(group_id), message=message)
            logger.info(f"群聊总结: 文件发送成功: {file_name}")
            return True
        except Exception as e:
            logger.error(f"群聊总结: 文件发送失败: {traceback.format_exc()}")
            return False

    async def run_summary_for_group(self, group_id: str, hours: int = None):
        if hours is None:
            hours = self.summary_hours
            
        logger.info(f"群聊总结: 开始为群 {group_id} 生成总结")
        
        try:
            platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
            if not platform:
                logger.error("群聊总结: 未找到 AIOCQHTTP 平台")
                return None
                
            bot = platform.get_client()
            
            try:
                group_info = await bot.api.call_action("get_group_info", group_id=group_id)
                group_name = group_info.get("group_name", f"群{group_id}")
            except:
                group_name = f"群{group_id}"
            
            last_time = await self._load_last_summary_time(group_id)
            raw_messages = await self.fetch_group_history(bot, group_id, hours_limit=hours, since_timestamp=last_time)
            
            if not raw_messages:
                logger.info(f"群聊总结: 群 {group_id} 没有新消息")
                return None
            
            valid_msgs, chat_log, media_files = self.process_messages(raw_messages, hours_limit=hours)
            if not valid_msgs:
                logger.info(f"群聊总结: 群 {group_id} 没有有效消息")
                return None
            
            analysis_data = await self.generate_summary(chat_log, group_name, hours)
            
            await self._save_last_summary_time(group_id, time.time())
            
            return {
                "group_id": group_id,
                "group_name": group_name,
                "analysis_data": analysis_data,
                "hours": hours,
                "msg_count": len(valid_msgs),
                "media_files": media_files
            }
        except Exception as e:
            logger.error(f"群聊总结: 生成总结失败: {traceback.format_exc()}")
            return None

    async def scheduler_loop(self):
        logger.info(f"群聊总结: 定时任务启动，计划时间: {self.summary_schedule}")
        
        while True:
            try:
                now = datetime.datetime.now()
                schedule_time = datetime.datetime.strptime(self.summary_schedule, "%H:%M").time()
                target_datetime = datetime.datetime.combine(now.date(), schedule_time)
                
                if now.time() >= schedule_time:
                    target_datetime = datetime.datetime.combine(
                        now.date() + datetime.timedelta(days=1), 
                        schedule_time
                    )
                
                wait_seconds = (target_datetime - now).total_seconds()
                logger.info(f"群聊总结: 下次执行时间: {target_datetime}，等待 {wait_seconds} 秒")
                
                await asyncio.sleep(wait_seconds)
                
                if not self.monitored_groups or not self.target_group:
                    logger.warning("群聊总结: 未配置监控群或目标群，跳过定时任务")
                    continue
                
                platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
                if not platform:
                    logger.error("群聊总结: 未找到 AIOCQHTTP 平台")
                    continue
                
                bot = platform.get_client()
                
                await bot.api.call_action(
                    "send_group_msg",
                    group_id=int(self.target_group),
                    message=f"{self.bot_name}开始执行定时总结任务..."
                )
                
                for group_id in self.monitored_groups:
                    result = await self.run_summary_for_group(group_id)
                    if result:
                        await self.send_summary_to_target(
                            result["group_name"], 
                            result["analysis_data"], 
                            result["hours"],
                            result.get("media_files", [])
                        )
                        await asyncio.sleep(2)
                
                await bot.api.call_action(
                    "send_group_msg",
                    group_id=int(self.target_group),
                    message=f"{self.bot_name}定时总结任务完成"
                )
                
            except Exception as e:
                logger.error(f"群聊总结: 定时任务错误: {traceback.format_exc()}")
                await asyncio.sleep(60)

    @filter.on_astrbot_loaded()
    async def on_loaded(self):
        if self.monitored_groups and self.target_group and self.summary_schedule:
            self._scheduler_task = asyncio.create_task(self.scheduler_loop())
            logger.info("群聊总结: 定时任务已启动")
        else:
            logger.warning("群聊总结: 配置不完整，定时任务未启动")

    @filter.command("总结")
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def manual_summary(self, event: AstrMessageEvent, hours: int = 24):
        """手动触发总结: /总结 [小时数]"""
        if not self.target_group:
            yield event.plain_result("未配置目标群，请先在配置中设置 target_group")
            return
        
        if not self.monitored_groups:
            yield event.plain_result("未配置监控群，请先在配置中设置 monitored_groups")
            return
        
        platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
        if not platform:
            yield event.plain_result("无法获取平台实例")
            return
        
        bot = platform.get_client()
        
        yield event.plain_result(f"正在为 {len(self.monitored_groups)} 个监控群生成总结...")
        
        success_count = 0
        for group_id in self.monitored_groups:
            result = await self.run_summary_for_group(group_id, hours)
            if result:
                success = await self.send_summary_to_target(
                    result["group_name"], 
                    result["analysis_data"], 
                    result["hours"],
                    result.get("media_files", [])
                )
                if success:
                    success_count += 1
                await asyncio.sleep(2)
        
        yield event.plain_result(f"总结完成，成功: {success_count}/{len(self.monitored_groups)}")

    @filter.command("保存")
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def archive_file(self, event: AstrMessageEvent, index: int = 0):
        """保存文件到群: /保存 <序号>"""
        if not self.target_group:
            yield event.plain_result("未配置目标群")
            return
        
        if not self._recent_media_files:
            yield event.plain_result("没有可保存的文件，请先生成总结")
            return
        
        if index < 1 or index > len(self._recent_media_files):
            yield event.plain_result(f"序号无效，请输入 1-{len(self._recent_media_files)} 之间的数字")
            return
        
        try:
            platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
            if not platform:
                yield event.plain_result("无法获取平台实例")
                return
            
            bot = platform.get_client()
            
            media = self._recent_media_files[index - 1]
            file_url = media.get("url", "")
            media_type = media.get("type", "image")
            media_name = media.get("name", "未知用户")
            
            if not file_url:
                yield event.plain_result("文件URL无效")
                return
            
            now = datetime.datetime.now()
            if media_type == "image":
                file_name = f"{index}_{media_name}_{now.strftime('%H%M%S')}.jpg"
            else:
                file_name = f"{index}_{media_name}_{now.strftime('%H%M%S')}.file"
            
            success = await self.send_file_to_group(bot, self.target_group, file_url, file_name)
            
            if success:
                yield event.plain_result(f"文件已发送到目标群: {file_name}")
            else:
                yield event.plain_result("文件发送失败")
                
        except Exception as e:
            logger.error(f"群聊总结: 保存文件失败: {traceback.format_exc()}")
            yield event.plain_result(f"保存失败: {str(e)}")

    @filter.command("总结状态")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def check_status(self, event: AstrMessageEvent):
        """查看总结配置状态: /总结状态"""
        status_lines = [
            f"群聊总结状态",
            f"━━━━━━━━━━━━━━━",
            f"机器人名称: {self.bot_name}",
            f"监控群: {', '.join(self.monitored_groups) if self.monitored_groups else '未配置'}",
            f"目标群: {self.target_group if self.target_group else '未配置'}",
            f"定时时间: {self.summary_schedule}",
            f"总结范围: {self.summary_hours} 小时",
            f"最大消息数: {self.max_msg_count}",
        ]
        yield event.plain_result("\n".join(status_lines))

    async def terminate(self):
        if self._scheduler_task:
            self._scheduler_task.cancel()
            logger.info("群聊总结: 定时任务已停止")
