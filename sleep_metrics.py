"""
Prototype: TIB / TST / SE calculations for the sleep tracker.

Time encoding convention (see NOTES.md):
- TTB assumed PM by default. Negative sign flips to AM.
- TOB assumed AM by default. Negative sign flips to PM.
- 1200 TTB = midnight (00:00). 1200 TOB = noon (12:00).
- Records are dated by TOB (wake) date. TTB, when in its default PM sense,
  falls on the PREVIOUS calendar day. TTB in its AM sense (negative, i.e.
  after midnight) falls on the SAME calendar day as TOB.
- TOB never shifts the calendar date, regardless of AM/PM -- the record's
  date IS the TOB date by definition.
"""

from datetime import datetime, timedelta


def parse_time_value(raw, field):
    """
    Parse a TTB or TOB raw value into (hour24, minute, is_next_or_prev_day_shift).
    field: 'ttb' or 'tob'
    Returns (hour, minute, date_offset_days) where date_offset_days is
    relative to the record's TOB date (0 = same day, -1 = previous day).
    """
    raw = str(raw).strip()
    negative = raw.startswith('-')
    val = abs(int(raw))

    if val == 1200:
        # Special-cased regardless of sign per convention
        if field == 'ttb':
            return 0, 0, 0       # midnight, same day as TOB
        else:  # tob
            return 12, 0, 0      # noon, same day (TOB always same day)

    hours = val // 100
    minutes = val % 100

    if field == 'ttb':
        period = 'AM' if negative else 'PM'
        date_offset = 0 if period == 'AM' else -1
    else:  # tob
        period = 'PM' if negative else 'AM'
        date_offset = 0  # TOB date never shifts

    if period == 'AM':
        hour24 = 0 if hours == 12 else hours
    else:  # PM
        hour24 = 12 if hours == 12 else hours + 12

    return hour24, minutes, date_offset


def calculate_sleep_metrics(record_date, ttb_raw, sl, noa, waso, ema, tob_raw):
    """
    record_date: date object (the TOB/wake date, matches the DB 'date' column)
    ttb_raw, tob_raw: raw encoded values, e.g. 1030, -120, 1200
    sl, waso, ema: minutes (numeric)
    noa: not used in TIB/TST/SE math directly, but kept for completeness

    Returns dict with tib_minutes, tst_minutes, se_percent (rounded to 1dp)
    """
    ttb_h, ttb_m, ttb_offset = parse_time_value(ttb_raw, 'ttb')
    tob_h, tob_m, tob_offset = parse_time_value(tob_raw, 'tob')

    ttb_dt = datetime.combine(record_date, datetime.min.time()) \
        + timedelta(days=ttb_offset, hours=ttb_h, minutes=ttb_m)
    tob_dt = datetime.combine(record_date, datetime.min.time()) \
        + timedelta(days=tob_offset, hours=tob_h, minutes=tob_m)

    tib_minutes = (tob_dt - ttb_dt).total_seconds() / 60

    sl = sl or 0
    waso = waso or 0
    ema = ema or 0
    tst_minutes = tib_minutes - sl - waso - ema

    se_percent = (tst_minutes / tib_minutes * 100) if tib_minutes > 0 else None

    return {
        'tib_minutes': round(tib_minutes, 1),
        'tst_minutes': round(tst_minutes, 1),
        'se_percent': round(se_percent, 1) if se_percent is not None else None,
        'ttb_datetime': ttb_dt,
        'tob_datetime': tob_dt,
    }


if __name__ == '__main__':
    from datetime import date

    test_cases = [
        # (label, record_date, ttb, sl, noa, waso, ema, tob)
        ("normal night", date(2026, 7, 3), 1030, 15, 2, 20, 10, 630),
        ("late bedtime after midnight", date(2026, 7, 3), -100, 5, 0, 0, 0, 800),
        ("afternoon wake (PM TOB)", date(2026, 7, 3), 1130, 10, 1, 15, 5, -300),
        ("midnight TTB special case", date(2026, 7, 3), 1200, 10, 1, 10, 5, 700),
        ("noon TOB special case", date(2026, 7, 3), 2200, 20, 3, 30, 15, 1200),
    ]

    for label, rdate, ttb, sl, noa, waso, ema, tob in test_cases:
        result = calculate_sleep_metrics(rdate, ttb, sl, noa, waso, ema, tob)
        print(f"--- {label} ---")
        print(f"  TTB raw={ttb} -> {result['ttb_datetime']}")
        print(f"  TOB raw={tob} -> {result['tob_datetime']}")
        print(f"  TIB: {result['tib_minutes']} min  "
              f"TST: {result['tst_minutes']} min  "
              f"SE: {result['se_percent']}%")
        print()
