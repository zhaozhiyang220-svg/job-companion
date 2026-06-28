import pytest

from src.jobs.scheduler import scheduler, shutdown_scheduler, start_scheduler


@pytest.mark.asyncio
async def test_scheduler_starts_and_registers_job() -> None:
    # AsyncIOScheduler.start() 需要运行中的事件循环，故测试为 async。
    start_scheduler()
    try:
        jobs = scheduler.get_jobs()
        assert any(j.id == "weekly_digest_regen" for j in jobs)
    finally:
        shutdown_scheduler()
