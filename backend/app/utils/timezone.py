# -*- coding: utf-8 -*-
"""
时区工具模块。

统一将 UTC 时间转换为中国标准时间（Asia/Shanghai，UTC+8）用于展示。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional


_CN_TZ = timezone(timedelta(hours=8))


def format_cn_time(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    将 datetime 转换为中国标准时间字符串。

    数据库中存储的是 UTC 时间（tzinfo=None），先按 UTC 解释再转 +8。
    """
    if dt is None:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_CN_TZ).strftime(fmt)


def now_cn() -> datetime:
    """返回当前中国标准时间。"""
    return datetime.now(_CN_TZ)
