from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "update-player-stats-hourly": {
        "task": "update_player_stats",
        "schedule": crontab(minute=0),
        "args": (116,),
    },
}
