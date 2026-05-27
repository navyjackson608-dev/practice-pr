import pytest
from datetime import date
from shift_schedule import ShiftSchedule, generate_weekly_schedule, SHIFTS, DAYS


def make_schedule():
    s = ShiftSchedule()
    for name in ["Alice", "Bob", "Carol"]:
        s.add_staff(name)
    return s


def test_add_staff():
    s = ShiftSchedule()
    s.add_staff("Alice")
    assert "Alice" in s._staff


def test_add_duplicate_staff_raises():
    s = make_schedule()
    with pytest.raises(ValueError, match="already exists"):
        s.add_staff("Alice")


def test_remove_staff():
    s = make_schedule()
    s.assign("Mon", "morning", "Alice")
    s.remove_staff("Alice")
    assert "Alice" not in s._staff
    assert "Alice" not in s.get_shift("Mon", "morning")


def test_assign_and_get_shift():
    s = make_schedule()
    s.assign("Mon", "morning", "Alice")
    s.assign("Mon", "morning", "Bob")
    assert s.get_shift("Mon", "morning") == ["Alice", "Bob"]


def test_assign_invalid_day_raises():
    s = make_schedule()
    with pytest.raises(ValueError, match="Invalid day"):
        s.assign("Holiday", "morning", "Alice")


def test_assign_invalid_shift_raises():
    s = make_schedule()
    with pytest.raises(ValueError, match="Invalid shift"):
        s.assign("Mon", "dawn", "Alice")


def test_assign_unknown_staff_raises():
    s = make_schedule()
    with pytest.raises(ValueError, match="not found"):
        s.assign("Mon", "morning", "Dave")


def test_unassign():
    s = make_schedule()
    s.assign("Tue", "night", "Carol")
    s.unassign("Tue", "night", "Carol")
    assert s.get_shift("Tue", "night") == []


def test_unassign_not_assigned_raises():
    s = make_schedule()
    with pytest.raises(ValueError):
        s.unassign("Tue", "night", "Alice")


def test_get_staff_schedule():
    s = make_schedule()
    s.assign("Mon", "morning", "Alice")
    s.assign("Wed", "night", "Alice")
    result = s.get_staff_schedule("Alice")
    assert result == {"Mon": ["morning"], "Wed": ["night"]}


def test_get_staff_schedule_unknown_raises():
    s = make_schedule()
    with pytest.raises(ValueError, match="not found"):
        s.get_staff_schedule("Unknown")


def test_no_duplicate_assignment():
    s = make_schedule()
    s.assign("Fri", "afternoon", "Bob")
    s.assign("Fri", "afternoon", "Bob")
    assert s.get_shift("Fri", "afternoon").count("Bob") == 1


def test_generate_weekly_schedule():
    monday = date(2026, 5, 25)
    assignments = [
        (0, "morning", "Alice"),   # Mon
        (2, "afternoon", "Bob"),   # Wed
        (6, "night", "Carol"),     # Sun
    ]
    sched = generate_weekly_schedule(monday, ["Alice", "Bob", "Carol"], assignments)
    assert sched[date(2026, 5, 25)]["morning"] == ["Alice"]
    assert sched[date(2026, 5, 27)]["afternoon"] == ["Bob"]
    assert sched[date(2026, 5, 31)]["night"] == ["Carol"]
