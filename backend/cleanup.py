"""
MindSpace — Background Cleanup Scheduler
=========================================
Runs every 60 seconds to delete expired sessions, messages, and rooms.
MongoDB TTL indexes handle this at DB level too; this is a safety net.
"""

from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from db import sessions_col, messages_col, rooms_col


def _now():
    return datetime.now(timezone.utc)


def cleanup_expired_data():
    """Delete all docs whose expiry has passed."""
    now = _now()

    s = sessions_col.delete_many({"session_end": {"$lt": now}})
    m = messages_col.delete_many({"expires_at":  {"$lt": now}})
    r = rooms_col.delete_many(   {"expires_at":  {"$lt": now}, "is_default": False})

    print(
        f"[Cleanup] Sessions: {s.deleted_count} | "
        f"Messages: {m.deleted_count} | "
        f"Rooms: {r.deleted_count}"
    )


def start_cleanup_scheduler():
    """Start the APScheduler background job."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_expired_data,
        trigger="interval",
        seconds=60,
        id="mindspace_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Cleanup job started — runs every 60 seconds")
