"""Standalone tests for the pure clash-detection logic (no Flask/DB needed).

Run:  python3 test_clashes.py
"""
from datetime import date, time

from clashes import group_clashes, overlaps


D = date(2026, 8, 10)
D2 = date(2026, 8, 11)


def _e(sid, exam_id, code, d=D, start=None, dur=90, name="Alice"):
    return {'student_id': sid, 'exam_id': exam_id, 'paper_code': code,
            'date': d, 'start': start, 'duration': dur,
            'name': name, 'candidate_number': f'{1000 + sid}'}


def check(name, cond):
    print(("PASS" if cond else "FAIL") + " - " + name)
    if not cond:
        raise AssertionError(name)


def test_overlap_detected():
    # 09:00-10:30 vs 10:00-11:30 -> overlap
    res = group_clashes([_e(1, 10, 'A1', start=time(9, 0)),
                         _e(1, 20, 'B1', start=time(10, 0))])
    check("one clash reported", len(res) == 1)
    check("severity is overlap", res[0]['severity'] == 'overlap')
    check("both papers listed in start order",
          [p['paper_code'] for p in res[0]['papers']] == ['A1', 'B1'])


def test_back_to_back_is_same_day():
    # 09:00-10:30 then 10:30-12:00 -> touching, not overlapping
    res = group_clashes([_e(1, 10, 'A1', start=time(9, 0)),
                         _e(1, 20, 'B1', start=time(10, 30))])
    check("back-to-back reported", len(res) == 1)
    check("back-to-back is same_day, not overlap", res[0]['severity'] == 'same_day')


def test_different_days_no_clash():
    res = group_clashes([_e(1, 10, 'A1', start=time(9, 0)),
                         _e(1, 20, 'B1', d=D2, start=time(9, 0))])
    check("different days -> no clash", res == [])


def test_same_exam_same_day_ignored():
    # Maths P1 + Maths P2 on one day without overlap: normal scheduling
    res = group_clashes([_e(1, 10, 'M1', start=time(9, 0)),
                         _e(1, 10, 'M2', start=time(13, 0))])
    check("same exam's papers on one day ignored", res == [])
    # ...but an overlap within the same exam IS a data-entry error worth flagging
    res = group_clashes([_e(1, 10, 'M1', start=time(9, 0)),
                         _e(1, 10, 'M2', start=time(9, 30))])
    check("overlap within same exam still flagged",
          len(res) == 1 and res[0]['severity'] == 'overlap')


def test_missing_times():
    # no date -> ignored entirely
    res = group_clashes([_e(1, 10, 'A1', d=None, start=time(9, 0)),
                         _e(1, 20, 'B1', start=time(9, 0))])
    check("undated paper can't clash", res == [])
    # date but no start time -> can't overlap, still a same-day warning
    res = group_clashes([_e(1, 10, 'A1', start=None),
                         _e(1, 20, 'B1', start=time(9, 0))])
    check("timeless paper -> same_day", len(res) == 1 and res[0]['severity'] == 'same_day')
    check("timeless paper sorts last",
          [p['paper_code'] for p in res[0]['papers']] == ['B1', 'A1'])


def test_per_student_grouping():
    # two students, same schedule: independent clashes; a third with one paper: none
    entries = [_e(1, 10, 'A1', start=time(9, 0), name="Alice"),
               _e(1, 20, 'B1', start=time(9, 30), name="Alice"),
               _e(2, 10, 'A1', start=time(9, 0), name="Bob"),
               _e(2, 20, 'B1', start=time(9, 30), name="Bob"),
               _e(3, 10, 'A1', start=time(9, 0), name="Cara")]
    res = group_clashes(entries)
    check("one clash per clashing student", len(res) == 2)
    check("sorted by name within a date", [c['name'] for c in res] == ["Alice", "Bob"])


def test_three_papers_one_day():
    # two different exams overlap; a third non-overlapping paper joins the group
    res = group_clashes([_e(1, 10, 'A1', start=time(9, 0)),
                         _e(1, 20, 'B1', start=time(10, 0)),
                         _e(1, 30, 'C1', start=time(14, 0))])
    check("all three papers grouped", len(res) == 1 and len(res[0]['papers']) == 3)
    check("group severity is overlap", res[0]['severity'] == 'overlap')


def test_overlaps_edge():
    a = _e(1, 10, 'A1', start=time(9, 0), dur=None)     # unknown duration -> 0 min
    b = _e(1, 20, 'B1', start=time(9, 0))
    check("zero-length paper at same start doesn't overlap", not overlaps(a, b))
    check("zero-length pair still same_day via grouping",
          group_clashes([a, b])[0]['severity'] == 'same_day')


if __name__ == '__main__':
    for fn in [test_overlap_detected, test_back_to_back_is_same_day,
               test_different_days_no_clash, test_same_exam_same_day_ignored,
               test_missing_times, test_per_student_grouping,
               test_three_papers_one_day, test_overlaps_edge]:
        print(f"\n# {fn.__name__}")
        fn()
    print("\nAll clash tests passed.")
