# coding=utf-8
"""
平台标题格式化模块

提供多平台标题格式化功能
"""

import logging
from typing import Dict, Optional

from trendradar.report.helpers import clean_title, html_escape, format_rank_display

logger = logging.getLogger(__name__)

# 短链接配置（由 context 初始化时设置）
_shorturl_config: Optional[Dict] = None


def set_shorturl_config(config: Optional[Dict]):
    """设置短链接配置

    Args:
        config: 短链接配置字典，包含 enabled, service, timeout
    """
    global _shorturl_config
    _shorturl_config = config


def get_short_url(url: str) -> str:
    """获取短链接

    Args:
        url: 原始链接

    Returns:
        短链接（如果启用）或原始链接
    """
    if not url:
        return url

    if not _shorturl_config or not _shorturl_config.get("enabled", False):
        return url

    try:
        from trendradar.utils.shorturl import shorten_url

        service = _shorturl_config.get("service", "tinyurl")
        timeout = _shorturl_config.get("timeout", 3)
        return shorten_url(url, service=service, timeout=timeout)
    except Exception as e:
        logger.debug(f"短链接转换失败: {e}")
        return url


def format_title_for_platform(
    platform: str, title_data: Dict, show_source: bool = True, show_keyword: bool = False
) -> str:
    """统一的标题格式化方法

    为不同平台生成对应格式的标题字符串。

    Args:
        platform: 目标平台，支持:
            - "feishu": 飞书
            - "dingtalk": 钉钉
            - "wework": 企业微信
            - "bark": Bark
            - "telegram": Telegram
            - "ntfy": ntfy
            - "slack": Slack
            - "html": HTML 报告
        title_data: 标题数据字典，包含以下字段:
            - title: 标题文本
            - source_name: 来源名称
            - time_display: 时间显示
            - count: 出现次数
            - ranks: 排名列表
            - rank_threshold: 高亮阈值
            - url: PC端链接
            - mobile_url: 移动端链接（优先使用）
            - is_new: 是否为新增标题（可选）
            - matched_keyword: 匹配的关键词（可选，platform 模式使用）
        show_source: 是否显示来源名称（keyword 模式使用）
        show_keyword: 是否显示关键词标签（platform 模式使用）

    Returns:
        格式化后的标题字符串
    """
    rank_display = format_rank_display(
        title_data["ranks"], title_data["rank_threshold"], platform
    )

    # 获取链接并转换为短链接（如果启用）
    original_url = title_data["mobile_url"] or title_data["url"]
    link_url = get_short_url(original_url)
    cleaned_title = clean_title(title_data["title"])

    # 获取关键词标签（platform 模式使用）
    keyword = title_data.get("matched_keyword", "") if show_keyword else ""

    if platform == "feishu":
        # 飞书简洁格式：[来源] 标题 (排名)
        if link_url:
            formatted_title = f"[{cleaned_title}]({link_url})"
        else:
            formatted_title = cleaned_title

        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if show_source:
            result = f"[{title_data['source_name']}] {title_prefix}{formatted_title}"
        elif show_keyword and keyword:
            result = f"[{keyword}] {title_prefix}{formatted_title}"
        else:
            result = f"{title_prefix}{formatted_title}"

        # 只显示排名，去掉时间和次数
        if rank_display:
            result += f" {rank_display}"

        return result

    elif platform == "dingtalk":
        if link_url:
            formatted_title = f"[{cleaned_title}]({link_url})"
        else:
            formatted_title = cleaned_title

        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if show_source:
            result = f"[{title_data['source_name']}] {title_prefix}{formatted_title}"
        elif show_keyword and keyword:
            result = f"[{keyword}] {title_prefix}{formatted_title}"
        else:
            result = f"{title_prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if title_data["time_display"]:
            result += f" - {title_data['time_display']}"
        if title_data["count"] > 1:
            result += f" ({title_data['count']}次)"

        return result

    elif platform in ("wework", "bark"):
        # WeWork 和 Bark 使用 markdown 格式
        if link_url:
            formatted_title = f"[{cleaned_title}]({link_url})"
        else:
            formatted_title = cleaned_title

        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if show_source:
            result = f"[{title_data['source_name']}] {title_prefix}{formatted_title}"
        elif show_keyword and keyword:
            result = f"[{keyword}] {title_prefix}{formatted_title}"
        else:
            result = f"{title_prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if title_data["time_display"]:
            result += f" - {title_data['time_display']}"
        if title_data["count"] > 1:
            result += f" ({title_data['count']}次)"

        return result

    elif platform == "telegram":
        if link_url:
            formatted_title = f'<a href="{link_url}">{html_escape(cleaned_title)}</a>'
        else:
            formatted_title = cleaned_title

        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if show_source:
            result = f"[{title_data['source_name']}] {title_prefix}{formatted_title}"
        elif show_keyword and keyword:
            result = f"<b>[{html_escape(keyword)}]</b> {title_prefix}{formatted_title}"
        else:
            result = f"{title_prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if title_data["time_display"]:
            result += f" <code>- {title_data['time_display']}</code>"
        if title_data["count"] > 1:
            result += f" <code>({title_data['count']}次)</code>"

        return result

    elif platform == "ntfy":
        if link_url:
            formatted_title = f"[{cleaned_title}]({link_url})"
        else:
            formatted_title = cleaned_title

        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if show_source:
            result = f"[{title_data['source_name']}] {title_prefix}{formatted_title}"
        elif show_keyword and keyword:
            result = f"[{keyword}] {title_prefix}{formatted_title}"
        else:
            result = f"{title_prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if title_data["time_display"]:
            result += f" `- {title_data['time_display']}`"
        if title_data["count"] > 1:
            result += f" `({title_data['count']}次)`"

        return result

    elif platform == "slack":
        # Slack 使用 mrkdwn 格式
        if link_url:
            # Slack 链接格式: <url|text>
            formatted_title = f"<{link_url}|{cleaned_title}>"
        else:
            formatted_title = cleaned_title

        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if show_source:
            result = f"[{title_data['source_name']}] {title_prefix}{formatted_title}"
        elif show_keyword and keyword:
            result = f"*[{keyword}]* {title_prefix}{formatted_title}"
        else:
            result = f"{title_prefix}{formatted_title}"

        # 排名（使用 * 加粗）
        rank_display = format_rank_display(
            title_data["ranks"], title_data["rank_threshold"], "slack"
        )
        if rank_display:
            result += f" {rank_display}"
        if title_data["time_display"]:
            result += f" `- {title_data['time_display']}`"
        if title_data["count"] > 1:
            result += f" `({title_data['count']}次)`"

        return result

    elif platform == "html":
        rank_display = format_rank_display(
            title_data["ranks"], title_data["rank_threshold"], "html"
        )

        # HTML 报告不使用短链接（保留原始链接便于追溯）
        link_url = title_data["mobile_url"] or title_data["url"]

        escaped_title = html_escape(cleaned_title)
        escaped_source_name = html_escape(title_data["source_name"])

        # 构建前缀（来源或关键词）
        if show_source:
            prefix = f'<span class="source-tag">[{escaped_source_name}]</span> '
        elif show_keyword and keyword:
            escaped_keyword = html_escape(keyword)
            prefix = f'<span class="keyword-tag">[{escaped_keyword}]</span> '
        else:
            prefix = ""

        if link_url:
            escaped_url = html_escape(link_url)
            formatted_title = f'{prefix}<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
        else:
            formatted_title = f'{prefix}<span class="no-link">{escaped_title}</span>'

        if rank_display:
            formatted_title += f" {rank_display}"
        if title_data["time_display"]:
            escaped_time = html_escape(title_data["time_display"])
            formatted_title += f" <font color='grey'>- {escaped_time}</font>"
        if title_data["count"] > 1:
            formatted_title += f" <font color='green'>({title_data['count']}次)</font>"

        if title_data.get("is_new"):
            formatted_title = f"<div class='new-title'>🆕 {formatted_title}</div>"

        return formatted_title

    else:
        return cleaned_title
