# coding=utf-8
"""
抖音深度热度分析

输出两类列表：
- 实时热度：当前在榜、排名靠前的游戏相关话题
- 起量中：排名显著上升的游戏相关话题
"""

from typing import Dict, List, Optional, Callable, Any


def _get_latest_time(title_info: Dict, platform_id: str) -> Optional[str]:
    latest_time = None
    for meta in (title_info.get(platform_id, {}) or {}).values():
        last_time = meta.get("last_time")
        if last_time and (latest_time is None or last_time > latest_time):
            latest_time = last_time
    return latest_time


def _extract_rank_points(meta: Dict) -> List[int]:
    points: List[int] = []
    for p in meta.get("rank_timeline") or []:
        rank = p.get("rank")
        if rank is None:
            continue
        try:
            points.append(int(rank))
        except Exception:
            continue
    if not points:
        ranks = meta.get("ranks") or []
        for r in ranks:
            try:
                points.append(int(r))
            except Exception:
                continue
    return points


def _format_trend(points: List[int], max_points: int = 4) -> str:
    if not points:
        return ""
    tail = points[-max_points:]
    return "→".join(str(p) for p in tail)


def _calc_rising_metrics(
    points: List[int], window_points: int = 4
) -> Dict[str, int]:
    """计算起量指标：窗口累计提升 & 连续提升步数"""
    if not points:
        return {"total_improve": 0, "improve_steps": 0, "window_used": 0}

    window = points[-window_points:] if window_points > 0 else points
    if len(window) < 2:
        return {"total_improve": 0, "improve_steps": 0, "window_used": len(window)}

    total_improve = window[0] - window[-1]
    improve_steps = 0
    for i in range(1, len(window)):
        if window[i] < window[i - 1]:
            improve_steps += 1

    return {
        "total_improve": total_improve,
        "improve_steps": improve_steps,
        "window_used": len(window),
    }


def build_douyin_focus(
    *,
    title_info: Dict,
    id_to_name: Dict,
    matches_word_groups_func: Optional[Callable[[str, List[Dict], List[str], Optional[List[str]]], bool]] = None,
    load_frequency_words_func: Optional[Callable[[], Any]] = None,
    extra_keywords: Optional[List[str]] = None,
    must_keywords: Optional[List[str]] = None,
    allow_unfiltered_hot: bool = False,
    max_hot_items: int = 20,
    max_rising_items: int = 12,
    min_rank_improve: int = 8,
    min_total_improve: int = 10,
    min_consecutive_improve: int = 2,
    max_rank: int = 60,
    trend_points: int = 4,
    rising_window_points: int = 4,
    platform_id: str = "douyin",
) -> Dict:
    """构建抖音深度热度与起量列表"""
    if not title_info or platform_id not in title_info:
        return {}

    latest_time = _get_latest_time(title_info, platform_id)
    if not latest_time:
        return {}

    word_groups = filter_words = global_filters = None
    if matches_word_groups_func and load_frequency_words_func:
        word_groups, filter_words, global_filters = load_frequency_words_func()
    extra_keywords = [str(k) for k in (extra_keywords or []) if k is not None and str(k).strip()]
    must_keywords = [str(k) for k in (must_keywords or []) if k is not None and str(k).strip()]

    def collect_items(require_keyword_match: bool, require_latest_only: bool) -> tuple:
        hot_items: List[Dict] = []
        rising_items: List[Dict] = []

        for title, meta in (title_info.get(platform_id, {}) or {}).items():
            meta = meta or {}
            if require_latest_only and meta.get("last_time") != latest_time:
                continue

            if global_filters:
                if any(f in title for f in global_filters):
                    continue

            # 强制“游戏相关”白名单：必须命中任一关键词
            if must_keywords:
                if not any(k in title for k in must_keywords):
                    continue

            if require_keyword_match and matches_word_groups_func and word_groups is not None:
                if not matches_word_groups_func(title, word_groups, filter_words, global_filters):
                    if extra_keywords:
                        if not any(k in title for k in extra_keywords):
                            continue
                    else:
                        continue

            points = _extract_rank_points(meta)
            if not points:
                continue

            current_rank = points[-1]
            if current_rank <= 0 or current_rank > max_rank:
                continue

            prev_rank = points[-2] if len(points) >= 2 else None
            delta = (prev_rank - current_rank) if prev_rank is not None else 0
            rising_metrics = _calc_rising_metrics(points, window_points=rising_window_points)

            item = {
                "title": title,
                "url": meta.get("url") or "",
                "mobile_url": meta.get("mobileUrl") or meta.get("mobile_url") or "",
                "rank": current_rank,
                "delta": delta,
                "trend": _format_trend(points, max_points=trend_points),
                "total_improve": rising_metrics.get("total_improve", 0),
                "improve_steps": rising_metrics.get("improve_steps", 0),
                "window_used": rising_metrics.get("window_used", 0),
            }

            hot_items.append(item)
            if (
                delta >= min_rank_improve
                or (
                    item["total_improve"] >= min_total_improve
                    and item["improve_steps"] >= min_consecutive_improve
                )
            ):
                rising_items.append(item)

        return hot_items, rising_items

    hot_items, rising_items = collect_items(require_keyword_match=True, require_latest_only=True)
    if allow_unfiltered_hot and not hot_items:
        # 放宽：不过滤关键词，且不过滤 last_time（扩大覆盖）
        hot_items, rising_items = collect_items(require_keyword_match=False, require_latest_only=False)

    hot_items.sort(key=lambda x: x.get("rank", 9999))
    rising_items.sort(key=lambda x: (-x.get("delta", 0), x.get("rank", 9999)))

    return {
        "platform_id": platform_id,
        "platform_name": id_to_name.get(platform_id, platform_id),
        "hot": hot_items[: max_hot_items if max_hot_items > 0 else len(hot_items)],
        "rising": rising_items[: max_rising_items if max_rising_items > 0 else len(rising_items)],
    }
