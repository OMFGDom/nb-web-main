from datetime import datetime

# Define Russian month names
MONTH_NAMES_RU = [
        "января", "февраля", "марта", "апреля",
        "мая", "июня", "июля", "августа",
        "сентября", "октября", "ноября", "декабря"
    ]

def pretty_date(date):
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    return f"{date.day} {MONTH_NAMES_RU[date.month - 1]} {date.year}, {date.strftime('%H:%M')}"

def article_pretty_date(date):
    return f"{date.day} {MONTH_NAMES_RU[date.month - 1]} {date.year}, {date.strftime('%H:%M')}"

def announce_date(date):
    MONTH_NAMES_RU = [
        "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август",
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    return f"{MONTH_NAMES_RU[date.month - 1]}‘{date.year % 100:02d}"

def duration_mmss(ms: int | None) -> str:
    if not ms or ms <= 0:
        return "--:--"
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{int(m):02d}:{int(s):02d}"

def duration_hhmm(ms: int | None) -> str:
    if not ms or ms <= 0:
        return ""
    s = ms // 1000
    m, _ = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{int(h)}:{int(m):02d}"
    return f"{int(m)}"

def duration_minutes_only(ms: int | None) -> str:
    """Показывает только минуты: '3 мин', '114 мин'"""
    if not ms or ms <= 0:
        return ""
    total_min = ms // 60000
    return f"{total_min} мин"

# from datetime import datetime, timedelta, timezone
#
# # Казахстан (UTC+5)
# LOCAL_TZ = timezone(timedelta(hours=5))
#
# MONTH_NAMES_RU = [
#     "января", "февраля", "марта", "апреля",
#     "мая", "июня", "июля", "августа",
#     "сентября", "октября", "ноября", "декабря",
# ]
# MONTH_NAMES_RU_UPPER = [
#     "Январь", "Февраль", "Март", "Апрель",
#     "Май", "Июнь", "Июль", "Август",
#     "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
# ]
#
#
# def _plural_ru(n: int, forms: tuple[str, str, str]) -> str:
#     if 11 <= (n % 100) <= 14:
#         return forms[2]
#     match n % 10:
#         case 1:
#             return forms[0]
#         case 2 | 3 | 4:
#             return forms[1]
#         case _:
#             return forms[2]
#
#
# def _to_local(value) -> datetime:
#     """
#     ISO строка или datetime → aware datetime в LOCAL_TZ (Казахстан).
#     """
#     if isinstance(value, datetime):
#         dt = value
#     else:
#         s = value.strip()
#         if s.endswith("Z"):
#             s = s[:-1]
#             try:
#                 dt = datetime.fromisoformat(s)
#             except ValueError:
#                 dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
#             dt = dt.replace(tzinfo=timezone.utc)  # это UTC
#             return dt.astimezone(LOCAL_TZ)        # перевод в Казахстан
#
#         try:
#             dt = datetime.fromisoformat(s)
#         except ValueError:
#             dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
#         if dt.tzinfo is None:
#             dt = dt.replace(tzinfo=LOCAL_TZ)
#         return dt.astimezone(LOCAL_TZ)
#
#     if dt.tzinfo is None:
#         dt = dt.replace(tzinfo=LOCAL_TZ)
#     return dt.astimezone(LOCAL_TZ)
#
#
# def pretty_date(value):
#     dt = _to_local(value)
#     now = datetime.now(LOCAL_TZ)  # обязательно aware и в Казахстане
#     diff = now - dt
#
#     if diff < timedelta(minutes=1):
#         return "только что"
#     if diff < timedelta(hours=1):
#         m = diff.seconds // 60
#         return f"{m} {_plural_ru(m, ('минута', 'минуты', 'минут'))} назад"
#     if diff < timedelta(hours=24):
#         h = diff.seconds // 3600
#         return f"{h} {_plural_ru(h, ('час', 'часа', 'часов'))} назад"
#     return f"{dt.day} {MONTH_NAMES_RU[dt.month - 1]} {dt.year}, {dt.strftime('%H:%M')}"
#
#
# article_pretty_date = pretty_date
#
#
# def announce_date(value):
#     dt = _to_local(value)
#     return f"{MONTH_NAMES_RU_UPPER[dt.month - 1]}‘{dt.year % 100:02d}"
