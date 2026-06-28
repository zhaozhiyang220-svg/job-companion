from time import perf_counter
from uuid import UUID

from litellm import acompletion
from litellm.cost_calculator import completion_cost

from src.core.db import SessionLocal
from src.models.ai_call_log import AICallLog

# v1 用户侧统一调用 MiniMax；同家族两档兜底（M1 重活 → abab6.5s 轻活）
FALLBACK_CHAIN: dict[str, list[str]] = {
    "auto-m1": ["minimax/MiniMax-M1", "minimax/abab6.5s-chat"],
    "auto-light": ["minimax/abab6.5s-chat"],
}


class LLMClient:
    """统一 LLM 调用入口。自动两档兜底 + 自动写 ai_call_logs。"""

    async def acomplete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        user_id: UUID | None = None,
        scene: str = "unknown",
    ) -> str:
        full_messages: list[dict[str, str]] = [{"role": "system", "content": system}, *messages]
        chain = FALLBACK_CHAIN.get(model, [model])
        last_exc: Exception | None = None
        for candidate in chain:
            t0 = perf_counter()
            try:
                resp = await acompletion(
                    model=candidate, messages=full_messages, max_tokens=max_tokens
                )
                content: str | None = resp.choices[0].message.content
                latency = int((perf_counter() - t0) * 1000)
                self._log(user_id, scene, candidate, resp, latency, "ok", None)
                return content or ""
            except Exception as exc:  # noqa: BLE001
                latency = int((perf_counter() - t0) * 1000)
                self._log(user_id, scene, candidate, None, latency, "error", str(exc)[:500])
                last_exc = exc
                continue
        raise RuntimeError(f"All LLM fallbacks failed: {last_exc}")

    def _log(
        self,
        user_id: UUID | None,
        scene: str,
        model: str,
        resp: object,
        latency_ms: int,
        status: str,
        error: str | None,
    ) -> None:
        cost = 0.0
        if resp is not None:
            try:
                cost = float(completion_cost(completion_response=resp))
            except Exception:  # noqa: BLE001
                cost = 0.0
        usage = getattr(resp, "usage", None)
        db = SessionLocal()
        try:
            db.add(
                AICallLog(
                    user_id=user_id,
                    scene=scene,
                    model=model,
                    input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                    output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error,
                )
            )
            db.commit()
        finally:
            db.close()
