# coding=utf-8
"""
短链接服务模块

提供 URL 缩短功能，支持多种短链接服务
"""

import logging
import urllib.parse
from functools import lru_cache
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# 短链接缓存（避免重复请求）
_url_cache: dict = {}


def shorten_url(url: str, service: str = "tinyurl", timeout: int = 3) -> str:
    """缩短 URL

    Args:
        url: 原始长链接
        service: 短链接服务，支持:
            - "tinyurl": TinyURL（免费，无需 API Key）
            - "isgd": is.gd（免费，无需 API Key）
            - "vgd": v.gd（免费，无需 API Key）
        timeout: 请求超时时间（秒）

    Returns:
        短链接，如果失败则返回原始链接
    """
    if not url:
        return url

    # 检查缓存
    cache_key = f"{service}:{url}"
    if cache_key in _url_cache:
        return _url_cache[cache_key]

    try:
        if service == "tinyurl":
            short_url = _shorten_tinyurl(url, timeout)
        elif service == "isgd":
            short_url = _shorten_isgd(url, timeout)
        elif service == "vgd":
            short_url = _shorten_vgd(url, timeout)
        else:
            logger.warning(f"未知的短链接服务: {service}，使用原始链接")
            return url

        if short_url:
            _url_cache[cache_key] = short_url
            return short_url

    except Exception as e:
        logger.debug(f"短链接转换失败 ({service}): {e}")

    return url


def _shorten_tinyurl(url: str, timeout: int = 3) -> Optional[str]:
    """使用 TinyURL 缩短链接

    TinyURL API 不需要注册，免费使用
    """
    api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(url, safe='')}"

    response = requests.get(api_url, timeout=timeout)
    if response.status_code == 200:
        short_url = response.text.strip()
        if short_url.startswith("http"):
            return short_url

    return None


def _shorten_isgd(url: str, timeout: int = 3) -> Optional[str]:
    """使用 is.gd 缩短链接

    is.gd API 不需要注册，免费使用
    """
    api_url = f"https://is.gd/create.php?format=simple&url={urllib.parse.quote(url, safe='')}"

    response = requests.get(api_url, timeout=timeout)
    if response.status_code == 200:
        short_url = response.text.strip()
        if short_url.startswith("http"):
            return short_url

    return None


def _shorten_vgd(url: str, timeout: int = 3) -> Optional[str]:
    """使用 v.gd 缩短链接

    v.gd API 不需要注册，免费使用（is.gd 的姊妹服务）
    """
    api_url = f"https://v.gd/create.php?format=simple&url={urllib.parse.quote(url, safe='')}"

    response = requests.get(api_url, timeout=timeout)
    if response.status_code == 200:
        short_url = response.text.strip()
        if short_url.startswith("http"):
            return short_url

    return None


def clear_cache():
    """清除短链接缓存"""
    global _url_cache
    _url_cache = {}
    logger.debug("短链接缓存已清除")


def get_cache_stats() -> dict:
    """获取缓存统计信息"""
    return {
        "cached_urls": len(_url_cache),
    }
