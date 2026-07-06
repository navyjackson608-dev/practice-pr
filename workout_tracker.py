"""Muscle training (workout) management tool.

A dependency-free tool for logging strength-training workouts and
reviewing your progress. Data is stored as JSON so it is easy to
inspect and back up.

Core concepts
-------------
- A *set* is one performed set: an exercise, a weight, and a rep count.
- A *workout* is a dated session containing one or more sets.
- The :class:`WorkoutTracker` loads/saves workouts and computes stats
  such as training volume, personal records, and estimated 1RM.
"""

from __future__ import annotations

import json
from datetime import date, datetime


# Muscle groups are free-form, but these are offered as sensible defaults
# for anyone building a UI or validating input.
MUSCLE_GROUPS = (
    "chest",
    "back",
    "shoulders",
    "legs",
    "arms",
    "core",
    "full_body",
)


def estimate_one_rep_max(weight, reps):
    """Estimate a one-rep max (1RM) from a work set.

    Uses the Epley formula: ``1RM = weight * (1 + reps / 30)``.
    A single rep returns the weight itself.

    Args:
        weight: Weight lifted (any unit, e.g. kilograms).
        reps: Number of repetitions completed (must be >= 1).

    Returns:
        The estimated one-rep max as a float, rounded to one decimal.
    """
    if reps < 1:
        raise ValueError("reps must be at least 1")
    if weight < 0:
        raise ValueError("weight must not be negative")
    return round(weight * (1 + reps / 30), 1)


class ExerciseSet:
    """A single performed set of an exercise."""

    def __init__(self, exercise, weight, reps, muscle_group=None):
        if not exercise or not exercise.strip():
            raise ValueError("exercise name is required")
        if weight < 0:
            raise ValueError("weight must not be negative")
        if reps < 1:
            raise ValueError("reps must be at least 1")
        self.exercise = exercise.strip()
        self.weight = weight
        self.reps = reps
        self.muscle_group = muscle_group

    @property
    def volume(self):
        """Training volume for this set (weight * reps)."""
        return self.weight * self.reps

    @property
    def estimated_one_rep_max(self):
        """Estimated 1RM for this set."""
        return estimate_one_rep_max(self.weight, self.reps)

    def to_dict(self):
        return {
            "exercise": self.exercise,
            "weight": self.weight,
            "reps": self.reps,
            "muscle_group": self.muscle_group,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            exercise=data["exercise"],
            weight=data["weight"],
            reps=data["reps"],
            muscle_group=data.get("muscle_group"),
        )

    def __repr__(self):
        return (
            f"ExerciseSet({self.exercise!r}, weight={self.weight}, "
            f"reps={self.reps})"
        )


class Workout:
    """A dated training session made up of one or more sets."""

    def __init__(self, workout_date=None, note="", sets=None):
        self.date = workout_date or date.today().isoformat()
        self.note = note
        self.sets = list(sets) if sets else []

    def add_set(self, exercise, weight, reps, muscle_group=None):
        """Add a performed set and return it."""
        performed = ExerciseSet(exercise, weight, reps, muscle_group)
        self.sets.append(performed)
        return performed

    @property
    def total_volume(self):
        """Sum of volume across every set in the workout."""
        return sum(s.volume for s in self.sets)

    def exercises(self):
        """Return the distinct exercise names in this workout."""
        seen = []
        for s in self.sets:
            if s.exercise not in seen:
                seen.append(s.exercise)
        return seen

    def to_dict(self):
        return {
            "date": self.date,
            "note": self.note,
            "sets": [s.to_dict() for s in self.sets],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            workout_date=data.get("date"),
            note=data.get("note", ""),
            sets=[ExerciseSet.from_dict(s) for s in data.get("sets", [])],
        )

    def __repr__(self):
        return f"Workout(date={self.date!r}, sets={len(self.sets)})"


class WorkoutTracker:
    """Manage a collection of workouts with JSON persistence."""

    def __init__(self, workouts=None):
        self.workouts = list(workouts) if workouts else []

    # -- persistence ---------------------------------------------------

    @classmethod
    def load(cls, path):
        """Load a tracker from a JSON file, or an empty one if missing."""
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except FileNotFoundError:
            return cls()
        return cls([Workout.from_dict(w) for w in raw.get("workouts", [])])

    def save(self, path):
        """Write all workouts to a JSON file."""
        payload = {"workouts": [w.to_dict() for w in self.workouts]}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    # -- logging -------------------------------------------------------

    def add_workout(self, workout):
        """Add a :class:`Workout` and keep the list sorted by date."""
        self.workouts.append(workout)
        self.workouts.sort(key=lambda w: w.date)
        return workout

    def log(self, exercise, weight, reps, muscle_group=None, workout_date=None):
        """Convenience helper: log a single set on a given day.

        If a workout already exists for ``workout_date`` the set is
        appended to it; otherwise a new workout is created.
        """
        target_date = workout_date or date.today().isoformat()
        workout = self._workout_on(target_date)
        if workout is None:
            workout = Workout(workout_date=target_date)
            self.add_workout(workout)
        return workout.add_set(exercise, weight, reps, muscle_group)

    def _workout_on(self, target_date):
        for workout in self.workouts:
            if workout.date == target_date:
                return workout
        return None

    # -- stats ---------------------------------------------------------

    def total_volume(self):
        """Total training volume across all workouts."""
        return sum(w.total_volume for w in self.workouts)

    def personal_record(self, exercise):
        """Return the heaviest set logged for ``exercise``.

        Returns the :class:`ExerciseSet` with the greatest weight, or
        ``None`` if the exercise has never been logged. Ties are broken
        by the higher rep count.
        """
        best = None
        for workout in self.workouts:
            for performed in workout.sets:
                if performed.exercise.lower() != exercise.strip().lower():
                    continue
                if best is None or (performed.weight, performed.reps) > (
                    best.weight,
                    best.reps,
                ):
                    best = performed
        return best

    def volume_by_muscle_group(self):
        """Aggregate training volume per muscle group.

        Sets without a muscle group are grouped under ``"unspecified"``.
        """
        totals = {}
        for workout in self.workouts:
            for performed in workout.sets:
                key = performed.muscle_group or "unspecified"
                totals[key] = totals.get(key, 0) + performed.volume
        return totals

    def progress(self, exercise):
        """Return estimated-1RM progress over time for an exercise.

        Returns a list of ``(date, best_estimated_1rm)`` tuples, one per
        workout in which the exercise appears, ordered by date.
        """
        history = []
        for workout in self.workouts:
            best = None
            for performed in workout.sets:
                if performed.exercise.lower() != exercise.strip().lower():
                    continue
                one_rm = performed.estimated_one_rep_max
                if best is None or one_rm > best:
                    best = one_rm
            if best is not None:
                history.append((workout.date, best))
        history.sort(key=lambda item: item[0])
        return history

    def summary(self):
        """Return a dict of headline stats across all workouts."""
        return {
            "workouts": len(self.workouts),
            "total_sets": sum(len(w.sets) for w in self.workouts),
            "total_volume": self.total_volume(),
            "volume_by_muscle_group": self.volume_by_muscle_group(),
        }


def _parse_date(value):
    """Validate a YYYY-MM-DD date string, returning it unchanged."""
    datetime.strptime(value, "%Y-%m-%d")
    return value


def _build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="Log strength-training workouts and track progress."
    )
    parser.add_argument(
        "--file",
        default="workouts.json",
        help="path to the JSON data file (default: workouts.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_log = sub.add_parser("log", help="log a single set")
    p_log.add_argument("exercise")
    p_log.add_argument("weight", type=float)
    p_log.add_argument("reps", type=int)
    p_log.add_argument("--muscle-group", choices=MUSCLE_GROUPS, default=None)
    p_log.add_argument("--date", type=_parse_date, default=None)

    sub.add_parser("summary", help="show headline stats")

    p_pr = sub.add_parser("pr", help="show the personal record for an exercise")
    p_pr.add_argument("exercise")

    p_prog = sub.add_parser("progress", help="show 1RM progress for an exercise")
    p_prog.add_argument("exercise")

    return parser


def main(argv=None):
    """Command-line entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    tracker = WorkoutTracker.load(args.file)

    if args.command == "log":
        performed = tracker.log(
            args.exercise,
            args.weight,
            args.reps,
            muscle_group=args.muscle_group,
            workout_date=args.date,
        )
        tracker.save(args.file)
        print(
            f"Logged: {performed.exercise} "
            f"{performed.weight}x{performed.reps} "
            f"(volume {performed.volume}, est. 1RM "
            f"{performed.estimated_one_rep_max})"
        )
    elif args.command == "summary":
        stats = tracker.summary()
        print(f"Workouts:     {stats['workouts']}")
        print(f"Total sets:   {stats['total_sets']}")
        print(f"Total volume: {stats['total_volume']}")
        if stats["volume_by_muscle_group"]:
            print("Volume by muscle group:")
            for group, volume in sorted(stats["volume_by_muscle_group"].items()):
                print(f"  {group:12s} {volume}")
    elif args.command == "pr":
        best = tracker.personal_record(args.exercise)
        if best is None:
            print(f"No sets logged for {args.exercise!r}.")
        else:
            print(
                f"PR for {best.exercise}: {best.weight}x{best.reps} "
                f"(est. 1RM {best.estimated_one_rep_max})"
            )
    elif args.command == "progress":
        history = tracker.progress(args.exercise)
        if not history:
            print(f"No sets logged for {args.exercise!r}.")
        else:
            print(f"Estimated 1RM progress for {args.exercise}:")
            for when, one_rm in history:
                print(f"  {when}  {one_rm}")


if __name__ == "__main__":
    main()
