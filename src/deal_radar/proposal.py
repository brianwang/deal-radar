from .config import settings
from .llm import chat

PROPOSAL_PROMPT = """你是 {profile} 方向的独立开发者。为下面这条需求写一封投标信（proposal），中文，直接可发送。

要求：
1. 开头一句话点出你理解对方的核心问题，不要泛泛而谈
2. 中间 2-3 句说明你会怎么做，给出具体技术方案
3. 提一个相关的追问，显示你认真读过需求
4. 结尾给一个明确的下一步，比如"可以先聊 20 分钟"
5. 全文 180-250 字，宁可具体，不要客套话，不要"您好，我是一名……"这种开头
6. 不要编造你没做过的项目

需求标题：{title}
需求描述：{description}
预算：{budget}
"""


def write_proposal(demand: dict) -> str:
    prompt = PROPOSAL_PROMPT.format(
        profile=settings.skill_profile,
        title=demand["title"],
        description=(demand.get("description") or "")[:3000],
        budget=demand.get("budget") or "未说明",
    )
    return chat([{"role": "user", "content": prompt}], temperature=0.6, max_tokens=3000).strip()
