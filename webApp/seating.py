"""Pure seating-allocation logic for the exam seating planner.

Kept deliberately free of Flask/SQLAlchemy imports so the placement algorithm can
be unit-tested in isolation (see test_seating.py). The route layer gathers the
students + rooms from the database, calls plan_seating(), and persists the result.

Rules (from the exams officer's requirements):
  * Only NON access-arrangement candidates are auto-seated. Access-arrangement
    candidates are handled separately (placed by hand into spare rooms).
  * Candidates are grouped by exam board and, within a board, ordered by
    candidate number, so papers can be handed out in order.
  * Candidates fill the FEWEST rooms needed, balanced as evenly as possible across
    those rooms, so a room is never left with a lone straggler (5 across 2 rooms
    becomes 3 + 2, not 4 + 1).
"""


def candidate_sort_key(candidate_number):
    """Order candidate numbers naturally; unassigned candidates sort last.

    Pure-numeric strings sort by value ("2" before "10"); other assigned values
    sort lexicographically after the numeric ones; missing values come last.
    """
    if candidate_number is None or str(candidate_number).strip() == "":
        return (2, 0, "")
    text = str(candidate_number).strip()
    if text.isdigit():
        return (0, int(text), text)
    return (1, 0, text)


def balanced_counts(n, caps):
    """How many candidates to put in each room.

    `caps` is the per-room capacity in placement order. Uses the fewest leading
    rooms whose combined capacity covers `n`, then water-fills across just those
    rooms (repeatedly add one to the least-filled room that still has space) so the
    load is spread as evenly as possible without leaving a near-empty room. If total
    capacity is smaller than `n`, every room is filled to capacity (caller reports
    the overflow as unplaced). Returns a list the same length as `caps`.
    """
    counts = [0] * len(caps)
    if n <= 0 or not caps:
        return counts

    # Fewest leading rooms whose capacity covers n (or all of them if it can't).
    used = len(caps)
    cumulative = 0
    for i, cap in enumerate(caps):
        if cumulative >= n:
            used = i
            break
        cumulative += cap
    used = max(used, 1)

    remaining = n
    while remaining > 0:
        target = -1
        for i in range(used):
            if counts[i] < caps[i] and (target == -1 or counts[i] < counts[target]):
                target = i
        if target == -1:
            break  # no capacity left among the rooms in play
        counts[target] += 1
        remaining -= 1
    return counts


def plan_seating(students, rooms):
    """Auto-allocate standard candidates to seats.

    students: list of dicts with at least id, board, candidate_number, exam_id and
              access (bool). Access-arrangement candidates are ignored here.
    rooms:    list of dicts with room_id, name, rows, columns (already filtered to
              the centre being planned).

    Returns {'seats': [...], 'unplaced': [student_id, ...]} where each seat is
    {'student_id', 'room_id', 'row', 'column', 'exam_id'}. Seats fill each room
    row-major (left to right, top to bottom).
    """
    standard = [s for s in students if not s.get('access')]
    standard.sort(key=lambda s: (
        (s.get('board') or '').upper(),
        candidate_sort_key(s.get('candidate_number')),
    ))

    ordered_rooms = sorted(rooms, key=lambda r: (r.get('name') or '', r.get('room_id') or 0))
    caps = [max(0, int(r.get('rows') or 0) * int(r.get('columns') or 0)) for r in ordered_rooms]

    counts = balanced_counts(len(standard), caps)

    seats = []
    idx = 0
    for room, count in zip(ordered_rooms, counts):
        cols = max(1, int(room.get('columns') or 1))
        for seat_i in range(count):
            student = standard[idx]
            idx += 1
            seats.append({
                'student_id': student['id'],
                'room_id': room['room_id'],
                'row': seat_i // cols,
                'column': seat_i % cols,
                'exam_id': student.get('exam_id'),
            })

    unplaced = [s['id'] for s in standard[idx:]]
    return {'seats': seats, 'unplaced': unplaced}
