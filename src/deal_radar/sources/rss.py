"""从 RSS 源导入需求。

很多平台有公开 RSS（如 We Work Remotely、V2EX 节点），先支持通用 RSS。
接单相关的 RSS 噪音很大，建议配合 keywords 做前置过滤。
"""

import feedparser

from ..db import add_demand


def import_rss(
    url: str, source: str = "rss", keywords: list[str] | None = None
) -> int:
    """抓取一个 RSS 源，把条目写入 demands 表，返回新增数量。

    keywords 非空时，只保留标题或摘要命中任一关键词的条目（不区分大小写）。
    """
    feed = feedparser.parse(url)
    added = 0
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        summary = (entry.get("summary") or entry.get("description") or "").strip()
        link = (entry.get("link") or "").split("#")[0]
        if not title:
            continue
        if keywords:
            haystack = f"{title} {summary}".lower()
            if not any(k.lower() in haystack for k in keywords):
                continue
        if add_demand(source=source, title=title, description=summary, url=link):
            added += 1
    return added
