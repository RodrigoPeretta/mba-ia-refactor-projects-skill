from datetime import datetime, timezone


def utcnow():
    """Instante atual em UTC, naive — mesmo formato dos datetimes já gravados no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
