# coding=utf-8
"""
全网热点事件聚合

目的：从最新批次的多平台热榜中，去重聚合出“全网热点事件”列表，
用于推送消息中的独立区块，方便围绕热点做内容/游戏创作。
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from trendradar.report.helpers import clean_title


_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[，。！？、：；“”‘’（）()【】《》<>「」『』·…—\-]+")


def _normalize_title(title: str) -> str:
    """用于跨平台去重的标题归一化（保守，不做激进同义合并）"""
    t = clean_title(title or "")
    t = t.strip().lower()
    t = _SPACE_RE.sub(" ", t)
    t = _PUNCT_RE.sub("", t)
    return t


def build_hot_events(
    *,
    title_info: Dict,
    id_to_name: Dict,
    max_items: int = 15,
    min_platforms: int = 2,
) -> List[Dict]:
    """
    从 title_info 中聚合“全网热点事件”（最新批次）。

    Args:
        title_info: {platform_id: {title: meta}}，meta 通常包含 last_time, ranks, url/mobileUrl 等
        id_to_name: 平台 id -> 名称
        max_items: 最多返回多少条事件
        min_platforms: 至少出现在多少个平台才算“全网”（不够则自动降到 1）

    Returns:
        events: [{title, platforms, platform_count, best_rank, url, mobile_url, ranks, rank_threshold}]
    """
    if not title_info:
        return []

    # 取最新批次时间（只聚合当前在榜的“热点事件”）
    latest_time: Optional[str] = None
    for _pid, titles in title_info.items():
        for _t, meta in (titles or {}).items():
            lt = (meta or {}).get("last_time") or ""
            if lt and (latest_time is None or lt > latest_time):
                latest_time = lt

    if not latest_time:
        return []

    # 归一化去重：key -> 聚合信息
    groups: Dict[str, Dict] = {}

    for platform_id, titles in (title_info or {}).items():
        platform_name = id_to_name.get(platform_id, platform_id)
        for title, meta in (titles or {}).items():
            meta = meta or {}
            if meta.get("last_time") != latest_time:
                continue

            key = _normalize_title(title)
            if not key:
                continue

            ranks = meta.get("ranks") or []
            current_rank = None
            if ranks:
                # ranks 可能是历史列表，最后一个对应 latest_time
                try:
                    current_rank = int(ranks[-1])
                except Exception:
                    current_rank = None

            url = meta.get("url") or ""
            mobile_url = meta.get("mobileUrl") or meta.get("mobile_url") or ""

            g = groups.get(key)
            if not g:
                groups[key] = {
                    "title": title,
                    "platforms": [platform_name],
                    "platform_count": 1,
                    "best_rank": current_rank if current_rank is not None else 9999,
                    "url": url,
                    "mobile_url": mobile_url,
                }
            else:
                # title：保留更长/信息更全的那个（很粗略，但能避免太短）
                if len(title) > len(g["title"]):
                    g["title"] = title
                if platform_name not in g["platforms"]:
                    g["platforms"].append(platform_name)
                    g["platform_count"] += 1
                if current_rank is not None and current_rank < g["best_rank"]:
                    g["best_rank"] = current_rank
                if not g.get("mobile_url") and mobile_url:
                    g["mobile_url"] = mobile_url
                if not g.get("url") and url:
                    g["url"] = url

    events = list(groups.values())
    if not events:
        return []

    # 先按 min_platforms 过滤；如果过滤后为空，则降级到 1（至少保证有内容）
    filtered = [e for e in events if e.get("platform_count", 0) >= max(min_platforms, 1)]
    if not filtered and min_platforms > 1:
        filtered = events

    # 排序：跨平台覆盖数优先，其次最佳排名（越小越靠前）
    filtered.sort(key=lambda e: (-int(e.get("platform_count", 0)), int(e.get("best_rank", 9999))))

    # 输出结构：补充 ranks 给 formatter 用
    output: List[Dict] = []
    for e in filtered[: max(max_items, 0) or 0]:
        best_rank = int(e.get("best_rank", 9999))
        output.append(
            {
                "title": e.get("title", ""),
                "platforms": e.get("platforms", []),
                "platform_count": int(e.get("platform_count", 0)),
                "best_rank": best_rank if best_rank != 9999 else 0,
                "url": e.get("url", ""),
                "mobile_url": e.get("mobile_url", ""),
                # 兼容 formatter 的 rank_display
                "ranks": [best_rank] if best_rank != 9999 else [],
            }
        )

    return output

