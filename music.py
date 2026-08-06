"""View-model builder for the music page.

Data comes from the scrobble_vault, which lives in the separate last-analysis project. 
This module never talks to its database and does not depend on its internals beyond
the shape of the /music-summary response.

Everything the template needs is computed here, and seperated into sections.
"""

import math
import os
import threading
import time
from datetime import datetime, timezone

import requests

# Single env var, not host/port pieces: on the Docker network this becomes
# http://scrobble_vault:8000 with no other change.
VAULT_URL = os.getenv("SCROBBLE_VAULT_URL", "http://127.0.0.1:8000").rstrip("/")

# The payload is ~1.8MB and changes at most once a sync interval, so refetching
# it per request (and per period-tab click) would be wasteful.
CACHE_TTL_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 15

PERIOD_IDS = ("7d", "30d", "365d", "all_time")
DEFAULT_PERIOD = "7d"

# The reference UI shows at most 10 discovery rows per column.
DISCOVERY_LIMIT = 10

# gunicorn serves this with threads, so two requests can miss the cache at the
# same instant. The lock costs nothing on the hit path and stops 1.8MB fetches when the TTL expires.
_cache = {"fetched_at": 0.0, "payload": None}
_cache_lock = threading.Lock()


class VaultUnavailable(Exception):
    """The scrobble vault could not be reached and no cached payload exists."""


def fetch_summary(force=False):
    """Return the /music-summary payload, cached for CACHE_TTL_SECONDS.

    If the vault is unreachable but a previous payload is cached, the stale one
    is served rather than failing the page, a slightly out-of-date chart beats
    an error card.
    """
    now = time.monotonic()
    with _cache_lock:
        if not force and _cache["payload"] is not None and now - _cache["fetched_at"] < CACHE_TTL_SECONDS:
            return _cache["payload"]
        cached = _cache["payload"]

    # Fetched outside the lock: a slow or hanging vault must not block every
    # other request for REQUEST_TIMEOUT_SECONDS.
    try:
        response = requests.get(f"{VAULT_URL}/music-summary", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        if cached is not None:
            return cached
        raise VaultUnavailable(str(exc)) from exc

    with _cache_lock:
        _cache["fetched_at"] = time.monotonic()
        _cache["payload"] = payload
    return payload


# --- formatting helpers ------------------------------------------------------


def time_ago(unix_seconds):
    """"3 days ago" style relative time. Independent of the viewer's timezone."""
    if not unix_seconds:
        return None

    delta = int(time.time()) - int(unix_seconds)
    if delta < 60:
        return "just now"

    for limit, size, name in (
        (3600, 60, "minute"),
        (86400, 3600, "hour"),
        (604800, 86400, "day"),
        (2629800, 604800, "week"),
        (31557600, 2629800, "month"),
        (None, 31557600, "year"),
    ):
        if limit is None or delta < limit:
            value = delta // size
            return f"{value} {name}{'s' if value != 1 else ''} ago"


def format_hour(hour):
    """0 -> '12 AM', 13 -> '1 PM'."""
    hour = int(hour) % 24
    suffix = "AM" if hour < 12 else "PM"
    display = hour % 12
    return f"{12 if display == 0 else display} {suffix}"


def format_utc(unix_seconds, with_time=True):
    """Absolute timestamps are rendered in UTC and labelled as such.

    Flask cannot know the viewer's timezone, and converting client-side would
    mean shipping JavaScript for it. Being explicit about UTC is honest and
    costs nothing.
    """
    if not unix_seconds:
        return None
    moment = datetime.fromtimestamp(int(unix_seconds), tz=timezone.utc)
    if with_time:
        return moment.strftime("%b %-d, %Y at %H:%M UTC")
    return moment.strftime("%b %-d, %Y")


def comma(value):
    """Thousands separator, the Jinja equivalent of JS toLocaleString()."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value


# --- chart geometry ----------------------------------------------------------


def nice_max(value):
    """Pick a readable y-axis ceiling, e.g. 23 -> 25, 4.2 -> 5."""
    if value <= 0:
        return 1

    magnitude = 10 ** math.floor(math.log10(value))
    for step in (s * magnitude for s in (1, 2, 2.5, 5, 10)):
        if math.ceil(value / step) * step >= value and math.ceil(value / step) <= 6:
            return math.ceil(value / step) * step

    return math.ceil(value / (magnitude * 10)) * magnitude * 10


def y_ticks(maximum):
    """Five evenly spaced axis labels from 0 to `maximum`."""
    return [round(maximum / 4 * i, 1) for i in range(5)]


def _tidy(number):
    """Drop the trailing .0 so axis labels read '20' rather than '20.0'."""
    return int(number) if float(number).is_integer() else number


def _bar_chart(rows, peak_key, peak_value, x_labels):
    """Shared shape for both bar charts: bars, axis ticks and label positions."""
    values = [row["value"] for row in rows]
    maximum = nice_max(max(values)) if values else 1

    bars = []
    for index, row in enumerate(rows):
        bars.append({
            "label": row["label"],
            "sublabel": row["sublabel"],
            "is_peak": row[peak_key] == peak_value if peak_value is not None else False,
            # Zero bars still get a 2% stub so the axis doesn't look gappy.
            "height_pct": (row["value"] / maximum * 100) if row["value"] > 0 else 2,
        })

    return {
        "bars": bars,
        "y_ticks": [_tidy(t) for t in y_ticks(maximum)],
        # Percentage positions so labels sit under their bar's centre.
        "x_labels": [
            {"text": text, "left_pct": (index + 0.5) / len(bars) * 100}
            for index, text in x_labels
            if index < len(bars)
        ],
    }


def clock_chart(clock):
    """24 hourly bars, in UTC. See format_utc for why there's no local shift."""
    if not clock or not clock.get("hours"):
        return None

    rows = []
    for hour in clock["hours"]:
        average = hour.get("average_scrobbles") or 0
        # Zero-listening hours omit average_listening_string entirely, so this
        # default keeps the tooltip from reading "0.0 avg · ".
        listened = hour.get("average_listening_string") or "0s"
        rows.append({
            "value": average,
            "label": format_hour(hour["hour"]),
            "sublabel": f"{average} avg · {listened}",
            "hour": hour["hour"],
        })

    peak = (clock.get("peak_hour") or {}).get("hour")
    return _bar_chart(rows, "hour", peak,
                      [(0, "12am"), (6, "6am"), (12, "12pm"), (18, "6pm"), (23, "11pm")])


def weekday_chart(weekday):
    """Seven bars, Monday first. Timezone-insensitive enough to leave alone."""
    if not weekday or not weekday.get("days"):
        return None

    rows = []
    for day in weekday["days"]:
        average = day.get("average_scrobbles") or 0
        listened = day.get("average_listening_string") or "0s"
        rows.append({
            "value": average,
            "label": day["weekday"],
            "sublabel": f"{average} avg · {listened}",
            "index": day["weekday_index"],
        })

    peak = (weekday.get("peak_day") or {}).get("weekday_index")
    x_labels = [(i, day["weekday"][:3]) for i, day in enumerate(weekday["days"])]
    return _bar_chart(rows, "index", peak, x_labels)


# --- row builders ------------------------------------------------------------


def pick_image(item, *prefixes):
    """First non-null artwork URL, largest first, trying each prefix in order.

    Any of these keys can be null, recent tracks in particular often have no
    album art and fall back to the artist image.
    """
    for prefix in prefixes:
        for size in ("extralarge", "large", "medium", "small"):
            url = item.get(f"{prefix}_image_{size}")
            if url:
                return url
    return None


def rank_rows(items, kind, with_discovery_label=False):
    """Normalise artists/albums/tracks into the single shape rank_chart renders."""
    rows = []
    for item in items or []:
        if kind == "artists":
            name = item.get("artist_name")
            subname = None
            image = pick_image(item, "artist")
        elif kind == "albums":
            name = item.get("album_name")
            subname = item.get("artist_name")
            image = pick_image(item, "album", "artist")
        else:
            name = item.get("track_name")
            subname = item.get("artist_name")
            image = pick_image(item, "album", "artist")

        rows.append({
            "name": name or "Unknown",
            "subname": subname,
            "image": image,
            "plays": item.get("plays") or 0,
            "sublabel": (
                f"discovered {time_ago(item.get('first_listened_at'))}"
                if with_discovery_label and item.get("first_listened_at") else None
            ),
        })
    return rows


def _discovery_column(discoveries, key, kind, empty_label):
    """One New Discoveries column, sliced to DISCOVERY_LIMIT."""
    items = discoveries.get(kind) or []
    count = discoveries.get(f"{kind}_count") or 0
    return {
        "label": key,
        "rows": rank_rows(items[:DISCOVERY_LIMIT], kind, with_discovery_label=True),
        "count": count,
        "truncated": count > DISCOVERY_LIMIT,
        "empty_label": empty_label,
    }


def recent_rows(tracks):
    """The 15 most recent tracks. Always read off the 7d period, never the
    selected one, these are 'what I just played', not a per-period statistic."""
    rows = []
    for track in tracks or []:
        name = track.get("track_name") or "Unknown"
        rows.append({
            "name": name,
            "artist": track.get("artist_name"),
            "image": pick_image(track, "album", "artist"),
            "listened_at": format_utc(track.get("listened_at")),
        })
    return rows


# --- the view model ----------------------------------------------------------


def build_view(summary, period_id):
    """Everything music.html needs, with every optional field already resolved."""
    periods = summary.get("periods") or []
    by_id = {p["period"]: p for p in periods}
    period = by_id.get(period_id) or (periods[0] if periods else None)
    if period is None:
        raise VaultUnavailable("summary contained no periods")

    stats = period.get("stats") or {}
    listening_time = stats.get("listening_time") or {}
    clock = stats.get("listening_clock") or {}
    weekday = stats.get("listening_weekday") or {}
    active_day = stats.get("most_active_day") or {}
    discoveries = stats.get("new_in_timeframe")

    peak_hour = clock.get("peak_hour") or {}
    peak_day = weekday.get("peak_day") or {}

    # Recent tracks come from the first period regardless of the selection.
    first_stats = (periods[0].get("stats") or {}) if periods else {}

    missing = listening_time.get("missing_duration_count")

    return {
        "periods": [{"id": p["period"], "label": p["label"]} for p in periods],
        "selected": period["period"],
        "period_label": period["label"],
        "last_synced": time_ago(summary.get("last_synced_at")),
        "recent": recent_rows(first_stats.get("recent_tracks")),
        "stats_cards": [
            {"label": "Tracks listened", "value": comma(stats.get("total_scrobbles", 0)),
             "sub": f"{comma(stats.get('active_days', 0))} active days"},
            {"label": "Unique artists", "value": comma(stats.get("unique_artists_count", 0)), "sub": None},
            {"label": "Unique albums", "value": comma(stats.get("unique_albums_count", 0)), "sub": None},
            {"label": "Unique tracks", "value": comma(stats.get("unique_tracks_count", 0)), "sub": None},
            {"label": "Listening time", "value": listening_time.get("total_string"),
             "sub": (f"Missing dur: {comma(missing)} track{'' if missing == 1 else 's'}"
                     if missing is not None else None)},
            {"label": "First track recorded", "value": format_utc(stats.get("first_listened_at"), with_time=False),
             "sub": format_utc(stats.get("first_listened_at")) and
                    datetime.fromtimestamp(int(stats["first_listened_at"]), tz=timezone.utc).strftime("%H:%M UTC")},
            {"label": "Last track recorded", "value": format_utc(stats.get("last_listened_at"), with_time=False),
             "sub": format_utc(stats.get("last_listened_at")) and
                    datetime.fromtimestamp(int(stats["last_listened_at"]), tz=timezone.utc).strftime("%H:%M UTC")},
            {"label": "Most active day", "value": active_day.get("day"),
             # .get, not [...]: the vault omits these on a day with no duration
             # data, and a partial dict is still truthy.
             "sub": (f"{active_day.get('total_listening_string') or '0s'} · "
                     f"{comma(active_day.get('scrobbles') or 0)} "
                     f"track{'' if active_day.get('scrobbles') == 1 else 's'}" if active_day else None)},
        ],
        "highlights": {
            "peak_hour": {
                "value": format_hour(peak_hour["hour"]) + " UTC" if peak_hour.get("hour") is not None else None,
                "sub": (f"{peak_hour.get('average_listening_string') or '0s'} avg · "
                        f"{peak_hour.get('average_scrobbles')} avg "
                        f"track{'' if peak_hour.get('average_scrobbles') == 1 else 's'}") if peak_hour else None,
            },
            "peak_day": {
                "value": peak_day.get("weekday"),
                "sub": (f"{peak_day.get('average_listening_string') or '0s'} avg · "
                        f"{peak_day.get('average_scrobbles')} avg "
                        f"track{'' if peak_day.get('average_scrobbles') == 1 else 's'}") if peak_day else None,
            },
            "discoveries": {
                "value": (f"{comma(discoveries.get('artists_count') or 0)} new "
                          f"artist{'' if discoveries.get('artists_count') == 1 else 's'}") if discoveries else None,
                "sub": (f"{comma(discoveries.get('albums_count') or 0)} "
                        f"album{'' if discoveries.get('albums_count') == 1 else 's'} · "
                        f"{comma(discoveries.get('tracks_count') or 0)} "
                        f"track{'' if discoveries.get('tracks_count') == 1 else 's'}") if discoveries else None,
            },
        },
        "top_charts": [
            {"label": "Artists", "rows": rank_rows(stats.get("top_artists"), "artists")},
            {"label": "Albums", "rows": rank_rows(stats.get("top_albums"), "albums")},
            {"label": "Tracks", "rows": rank_rows(stats.get("top_tracks"), "tracks")},
        ],
        # Absent for all_time, the section is skipped entirely in that case.
        "discoveries": [
            _discovery_column(discoveries, "Artists", "artists", "No new artists this period"),
            _discovery_column(discoveries, "Albums", "albums", "No new albums this period"),
            _discovery_column(discoveries, "Tracks", "tracks", "No new tracks this period"),
        ] if discoveries else None,
        "clock": clock_chart(clock),
        "weekday": weekday_chart(weekday),
    }
