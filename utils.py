import datetime


def str_to_bool(value):
    if value in ("y", "Y", "1", 1, "True", "true", "YES", "yes", "Yes"):
        return True

    if value in ("n", "N", "0", 0, "False", "false", "NO", "no", "No"):
        return False

    # The value might be some other string, so if its none of these, just
    # return the original value
    return value


def time_ago(value):
    if not isinstance(value, datetime.date):
        raise ValueError

    # We want them both to be timestamps, so we can compare without errors
    now = datetime.datetime.now()
    then = datetime.datetime.fromisoformat(value.isoformat())

    delta: datetime.timedelta = now - then
    if delta.days < 28:
        return f"{round(delta.days, 0)} days ago"

    if delta.days < 365:
        months = delta.days / 28
        return f"{round(months, 0)} months ago"

    years = delta.days / 365
    return f"{round(years, 2)} years ago"


def notice_period(notice_duration):
    if notice_duration.days < 7:
        return f"{notice_duration.days:3.1f} days"

    if notice_duration.days < 28:
        d = notice_duration.days / 7
        return f"{d:3.1f} weeks"

    m = notice_duration.days / 28
    return f"{m:0.0f} months"


def to_title(value: str):
    value = value.replace("_", " ")
    return value.title()
