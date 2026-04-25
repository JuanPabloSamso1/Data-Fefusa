"""Weekly ETL scheduler — runs main.main() every Saturday at 10:00 (Argentina time)."""
from __future__ import annotations

import logging
import traceback
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/Argentina/Mendoza")


def run_etl() -> None:
    """Synchronous wrapper — APScheduler calls this in a thread pool."""
    logger.info("=== Scheduler: iniciando ETL semanal ===")
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from main import main as etl_main  # project root main.py
        etl_main()
        logger.info("=== Scheduler: ETL completado ===")
    except Exception:
        logger.error("=== Scheduler: ETL falló ===\n%s", traceback.format_exc())


def start() -> None:
    scheduler.add_job(
        run_etl,
        trigger=CronTrigger(
            day_of_week="sat",
            hour=10,
            minute=0,
            timezone="America/Argentina/Mendoza",
        ),
        id="weekly_etl",
        replace_existing=True,
        misfire_grace_time=3600,  # fire up to 1h late if service was down
    )
    scheduler.start()
    logger.info("Scheduler iniciado — ETL corre cada sábado 10:00 (Mendoza)")


def stop() -> None:
    scheduler.shutdown(wait=False)
