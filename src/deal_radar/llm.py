import httpx

from .config import settings


class LLMError(RuntimeError):
    pass


def _request(messages: list[dict], temperature: float, max_tokens: int) -> tuple[str, str]:
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    try:
        with httpx.Client(timeout=180) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise LLMError(f"LLM 请求失败: {exc}") from exc

    try:
        choice = data["choices"][0]
        content = (choice["message"].get("content") or "").strip()
        finish_reason = choice.get("finish_reason") or ""
    except (KeyError, IndexError) as exc:
        raise LLMError(f"LLM 返回格式异常: {data}") from exc
    return content, finish_reason


def chat(messages: list[dict], temperature: float = 0.3, max_tokens: int = 1200) -> str:
    """调用 OpenAI 兼容的 /chat/completions。

    推理模型（如 deepseek 系列）会先消耗 completion 预算做 thinking，
    预算不足时 content 为空、finish_reason=length。这里自动放大预算重试一次。
    """
    content, finish_reason = _request(messages, temperature, max_tokens)
    if not content and finish_reason == "length":
        content, finish_reason = _request(messages, temperature, max_tokens * 3)
    if not content:
        raise LLMError(f"LLM 返回空内容（finish_reason={finish_reason or 'unknown'}）")
    return content
