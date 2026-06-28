from litellm import acompletion

# v1 用户侧统一调用 MiniMax；同家族两档兜底（M1 重活 → abab6.5s 轻活）
FALLBACK_CHAIN: dict[str, list[str]] = {
    "auto-m1": ["minimax/MiniMax-M1", "minimax/abab6.5s-chat"],
    "auto-light": ["minimax/abab6.5s-chat"],
}


class LLMClient:
    """统一 LLM 调用入口。传 auto-m1/auto-light 时按链路自动兜底。"""

    async def acomplete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
    ) -> str:
        full_messages: list[dict[str, str]] = [{"role": "system", "content": system}, *messages]
        chain = FALLBACK_CHAIN.get(model, [model])
        last_exc: Exception | None = None
        for candidate in chain:
            try:
                resp = await acompletion(
                    model=candidate, messages=full_messages, max_tokens=max_tokens
                )
                content: str | None = resp.choices[0].message.content
                return content or ""
            except Exception as exc:
                last_exc = exc
                continue
        raise RuntimeError(f"All LLM fallbacks failed: {last_exc}")
