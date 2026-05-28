from collections import defaultdict
from datetime import date, timedelta


SHIFTS = ["morning", "afternoon", "night"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class ShiftSchedule:
    def __init__(self):
        self._staff = []
        self._schedule = defaultdict(dict)  # {day: {shift: [staff_name, ...]}}

    def add_staff(self, name):
        if name in self._staff:
            raise ValueError(f"Staff '{name}' already exists")
        self._staff.append(name)

    def remove_staff(self, name):
        if name not in self._staff:
            raise ValueError(f"Staff '{name}' not found")
        self._staff.remove(name)
        for day in self._schedule:
            for shift in self._schedule[day]:
                if name in self._schedule[day][shift]:
                    self._schedule[day][shift].remove(name)

    def assign(self, day, shift, name):
        if day not in DAYS:
            raise ValueError(f"Invalid day '{day}'. Must be one of {DAYS}")
        if shift not in SHIFTS:
            raise ValueError(f"Invalid shift '{shift}'. Must be one of {SHIFTS}")
        if name not in self._staff:
            raise ValueError(f"Staff '{name}' not found. Add them first.")
        assigned = self._schedule[day].setdefault(shift, [])
        if name not in assigned:
            assigned.append(name)

    def unassign(self, day, shift, name):
        try:
            self._schedule[day][shift].remove(name)
        except (KeyError, ValueError):
            raise ValueError(f"'{name}' is not assigned to {day} {shift}")

    def get_shift(self, day, shift):
        return list(self._schedule[day].get(shift, []))

    def get_staff_schedule(self, name):
        if name not in self._staff:
            raise ValueError(f"Staff '{name}' not found")
        result = {}
        for day in DAYS:
            working = [s for s in SHIFTS if name in self._schedule[day].get(s, [])]
            if working:
                result[day] = working
        return result

    def display(self):
        col = 14
        header = f"{'':8}" + "".join(f"{s:^{col}}" for s in SHIFTS)
        print(header)
        print("-" * (8 + col * len(SHIFTS)))
        for day in DAYS:
            row = f"{day:8}"
            for shift in SHIFTS:
                names = self._schedule[day].get(shift, [])
                row += f"{', '.join(names) if names else '-':^{col}}"
            print(row)


def generate_weekly_schedule(start_date, staff_list, shift_assignments):
    """Build a schedule for the week starting on start_date.

    shift_assignments: list of (weekday_index 0=Mon, shift, name)
    Returns a dict {date: {shift: [names]}}
    """
    schedule = {}
    for offset in range(7):
        current = start_date + timedelta(days=offset)
        day_idx = current.weekday()
        day_shifts = defaultdict(list)
        for weekday, shift, name in shift_assignments:
            if weekday == day_idx and shift in SHIFTS:
                day_shifts[shift].append(name)
        schedule[current] = dict(day_shifts)
    return schedule
