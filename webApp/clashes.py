"""Pure exam-clash detection.

Kept free of Flask/SQLAlchemy imports so the logic can be unit-tested in
isolation (see test_clashes.py), mirroring seating.py. The route layer gathers
one entry per (candidate, scheduled paper) registration and calls
group_clashes(); each returned clash is one candidate-day needing attention.

Rules:
  * OVERLAP (serious): two of the candidate's papers on the same date whose
    time windows [start, start + duration) intersect. Back-to-back papers
    (one ends exactly when the next starts) do NOT overlap.
  * SAME DAY (warning): two or more papers from DIFFERENT exams on one date
    without a time overlap — the officer must plan the sitting order and any
    supervision between papers.
  * Multiple papers of the SAME exam on one day without an overlap are normal
    board scheduling and are not reported.
  * Papers with no date can't clash and are ignored. A paper with a date but
    no start time can't be checked for overlap, so it only contributes to
    SAME DAY. A missing duration is treated as 0 minutes.
"""
from datetime import datetime, timedelta, time


def _interval(entry):
    """(start, end) datetimes for an entry, or None if the time is unknown."""
    d, s = entry.get('date'), entry.get('start')
    if d is None or s is None:
        return None
    start = datetime.combine(d, s)
    duration = entry.get('duration')
    minutes = duration if isinstance(duration, int) and duration > 0 else 0
    return (start, start + timedelta(minutes=minutes))


def overlaps(a, b):
    """True if two entries' time windows intersect (touching edges don't)."""
    ia, ib = _interval(a), _interval(b)
    if ia is None or ib is None:
        return False
    return ia[0] < ib[1] and ib[0] < ia[1]


def time_range_str(day, start, duration):
    """'09:00 – 10:30' for display; degrades gracefully when time is unknown."""
    if start is None:
        return "time TBC"
    text = start.strftime('%H:%M')
    if isinstance(duration, int) and duration > 0:
        end = (datetime.combine(day, start) + timedelta(minutes=duration)).time()
        text += " – " + end.strftime('%H:%M')
    return text


def group_clashes(entries):
    """Group (candidate, paper) entries into per-candidate-per-day clashes.

    entries: dicts with student_id, date (datetime.date), start (datetime.time
    or None), duration (int minutes or None), exam_id, plus any display fields
    (name, candidate_number, exam, paper_code...) which are passed through.

    Returns a list sorted by date then name:
      {'student_id', 'name', 'candidate_number', 'date',
       'severity': 'overlap' | 'same_day', 'papers': [entry, ...]}
    """
    by_candidate_day = {}
    for e in entries:
        if e.get('date') is None:
            continue  # unscheduled papers can't clash
        by_candidate_day.setdefault((e['student_id'], e['date']), []).append(e)

    clashes = []
    for (sid, day), papers in by_candidate_day.items():
        if len(papers) < 2:
            continue

        has_overlap = any(overlaps(a, b)
                          for i, a in enumerate(papers) for b in papers[i + 1:])
        distinct_exams = {p.get('exam_id') for p in papers}
        if not has_overlap and len(distinct_exams) < 2:
            continue  # same exam's own papers spread over a day: normal

        papers.sort(key=lambda p: (p.get('start') is None,
                                   p.get('start') or time.min,
                                   p.get('paper_code') or ''))
        first = papers[0]
        clashes.append({
            'student_id': sid,
            'name': first.get('name'),
            'candidate_number': first.get('candidate_number'),
            'date': day,
            'severity': 'overlap' if has_overlap else 'same_day',
            'papers': papers,
        })

    clashes.sort(key=lambda c: (c['date'], c.get('name') or ''))
    return clashes
