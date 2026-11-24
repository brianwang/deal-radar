import json
import re

from .config import settings
from .llm import chat

SCORE_PROMPT = """你是一个接单匹配顾问。根据技能画像，判断下面这条需求值不值得接，并打分 0-100。

技能画像：{profile}

需求标题：{title}
需求描述：{description}
预算：{budget}

打分标准：
- 90-100：完全匹配技能，预算高，需求清晰，企业客户
- 70-89：匹配，但预算一般或需求需澄清
- 40-69：部分相关，但需要额外学习，或沟通成本高
- 0-39：不匹配、纯体力活、低价值或高风险

只输出 JSON，不要任何多余文字：
{{"score": <0-100 的整数>, "reason": "<40 字以内中文理由>", "risk": "<20 字以内主要风险>"}}
"""


def score_demand(demand: dict) -> dict:
    prompt = SCORE_PROMPT.format(
        profile=settings.skill_profile,
        title=demand["title"],
        description=(demand.get("description") or "")[:3000],
        budget=demand.get("budget") or "未说明",
    )
    raw = chat([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1000)
    return _parse_json(raw)


def _parse_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"LLM 没有返回 JSON: {raw[:200]}")
    data = json.loads(match.group(0))
    data["score"] = max(0, min(100, int(data.get("score", 0))))
    data.setdefault("reason", "")
    data.setdefault("risk", "")
    return data
