from time import perf_counter

from fastapi import APIRouter

from src.ai.llm_client import LLMClient

router = APIRouter(prefix="/api/v1/health", tags=["health"])
_llm = LLMClient()


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ai")
async def health_ai() -> dict[str, str | int]:
    t0 = perf_counter()
    text = await _llm.acomplete(
        model="auto-light",
        system="reply with single word: pong",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=16,
    )
    return {
        "status": "ok" if "pong" in text.lower() else "degraded",
        "model": "auto-light",
        "latency_ms": int((perf_counter() - t0) * 1000),
    }
