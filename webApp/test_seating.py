"""Standalone tests for the pure seating algorithm (no Flask/DB needed).

Run:  python3 test_seating.py
"""
from seating import plan_seating, balanced_counts, candidate_sort_key


def _room(room_id, name, rows, cols):
    return {'room_id': room_id, 'name': name, 'rows': rows, 'columns': cols}


def _stud(sid, board, cand, access=False, exam_id=1):
    return {'id': sid, 'board': board, 'candidate_number': cand,
            'access': access, 'exam_id': exam_id, 'name': f'S{sid}'}


def check(name, cond):
    print(("PASS" if cond else "FAIL") + " - " + name)
    if not cond:
        raise AssertionError(name)


# 1. Even split: 5 students, two 3x1 rooms -> 3 + 2, not 4 + 1.
def test_even_split():
    rooms = [_room(1, 'A', 3, 1), _room(2, 'B', 3, 1)]
    students = [_stud(i, 'AQA', f'{i:04d}') for i in range(1, 6)]
    res = plan_seating(students, rooms)
    per_room = {}
    for s in res['seats']:
        per_room[s['room_id']] = per_room.get(s['room_id'], 0) + 1
    check('even split fills both rooms', len(per_room) == 2)
    check('even split is 3 + 2', sorted(per_room.values()) == [2, 3])
    check('no student unplaced', res['unplaced'] == [])


# 2. Grouping by board + sorting by candidate number within board.
def test_group_and_sort():
    rooms = [_room(1, 'Hall', 10, 10)]  # one big room
    students = [
        _stud(10, 'OCR', '0100'),
        _stud(11, 'AQA', '0050'),
        _stud(12, 'AQA', '0002'),
        _stud(13, 'OCR', '0007'),
        _stud(14, 'AQA', '0009'),
    ]
    res = plan_seating(students, rooms)
    # Seats are emitted in placement order (row-major in a single room), so the
    # order of student_ids reflects the sorted grouping.
    order = [s['student_id'] for s in res['seats']]
    # AQA first (0002,0009,0050) then OCR (0007,0100)
    check('grouped by board then candidate number',
          order == [12, 14, 11, 13, 10])


# 3. Access-arrangement candidates are NOT auto-seated.
def test_access_excluded():
    rooms = [_room(1, 'Hall', 10, 10)]
    students = [
        _stud(1, 'AQA', '0001'),
        _stud(2, 'AQA', '0002', access=True),
        _stud(3, 'AQA', '0003'),
    ]
    res = plan_seating(students, rooms)
    seated = {s['student_id'] for s in res['seats']}
    check('access student is not seated', 2 not in seated)
    check('standard students are seated', {1, 3} <= seated)


# 4. Capacity overflow -> extras reported as unplaced.
def test_overflow():
    rooms = [_room(1, 'Small', 2, 1)]  # capacity 2
    students = [_stud(i, 'AQA', f'{i:04d}') for i in range(1, 5)]  # 4 students
    res = plan_seating(students, rooms)
    check('only capacity seated', len(res['seats']) == 2)
    check('overflow reported', len(res['unplaced']) == 2)


# 5. Row-major seat coordinates within a room.
def test_row_major():
    rooms = [_room(1, 'Grid', 2, 3)]  # 2 rows x 3 cols
    students = [_stud(i, 'AQA', f'{i:04d}') for i in range(1, 5)]  # 4 students
    res = plan_seating(students, rooms)
    coords = sorted((s['row'], s['column']) for s in res['seats'])
    check('row-major coords', coords == [(0, 0), (0, 1), (0, 2), (1, 0)])


# 6. Fewest rooms used: 3 students, three big rooms -> only 1 room used, balanced.
def test_fewest_rooms():
    rooms = [_room(1, 'A', 10, 10), _room(2, 'B', 10, 10), _room(3, 'C', 10, 10)]
    students = [_stud(i, 'AQA', f'{i:04d}') for i in range(1, 4)]
    res = plan_seating(students, rooms)
    used_rooms = {s['room_id'] for s in res['seats']}
    check('fewest rooms used (1)', used_rooms == {1})


# 7. balanced_counts edge cases.
def test_balanced_counts():
    # When capacity forces a second room, balance it (3 + 2, never 4 + 1)...
    check('5 over [3,3] -> [3,2]', balanced_counts(5, [3, 3]) == [3, 2])
    # ...but with two big halls, 5 candidates fit in one (don't open a second room).
    check('5 over [30,30] -> [5,0]', balanced_counts(5, [30, 30]) == [5, 0])
    check('0 students -> zeros', balanced_counts(0, [5, 5]) == [0, 0])
    check('exact fill', balanced_counts(6, [3, 3]) == [3, 3])
    check('spills to third room', balanced_counts(7, [3, 3, 3]) == [3, 2, 2])
    check('small room capped', balanced_counts(20, [4, 30]) == [4, 16])


# 8. Candidate sort key: numeric-aware, unassigned last.
def test_sort_key():
    keys = sorted(['10', '2', None, '', 'ABC'], key=candidate_sort_key)
    check('numeric before text before empty', keys[:2] == ['2', '10'])
    check('empty/None sort last', keys[-2:] == [None, ''] or keys[-2:] == ['', None])


if __name__ == '__main__':
    for fn in [test_even_split, test_group_and_sort, test_access_excluded,
               test_overflow, test_row_major, test_fewest_rooms,
               test_balanced_counts, test_sort_key]:
        print(f"\n# {fn.__name__}")
        fn()
    print("\nAll seating tests passed.")
