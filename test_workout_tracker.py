"""Tests for the workout_tracker module (standard library unittest)."""

import os
import tempfile
import unittest

from workout_tracker import (
    ExerciseSet,
    Workout,
    WorkoutTracker,
    estimate_one_rep_max,
)


class EstimateOneRepMaxTests(unittest.TestCase):
    def test_single_rep_returns_weight(self):
        self.assertEqual(estimate_one_rep_max(100, 1), round(100 * (1 + 1 / 30), 1))

    def test_epley_formula(self):
        # 100kg x 5 -> 100 * (1 + 5/30) = 116.7
        self.assertEqual(estimate_one_rep_max(100, 5), 116.7)

    def test_rejects_zero_reps(self):
        with self.assertRaises(ValueError):
            estimate_one_rep_max(100, 0)


class ExerciseSetTests(unittest.TestCase):
    def test_volume(self):
        self.assertEqual(ExerciseSet("squat", 100, 5).volume, 500)

    def test_requires_exercise_name(self):
        with self.assertRaises(ValueError):
            ExerciseSet("   ", 100, 5)

    def test_rejects_bad_reps(self):
        with self.assertRaises(ValueError):
            ExerciseSet("squat", 100, 0)

    def test_round_trip_dict(self):
        original = ExerciseSet("bench", 80, 8, muscle_group="chest")
        restored = ExerciseSet.from_dict(original.to_dict())
        self.assertEqual(restored.exercise, "bench")
        self.assertEqual(restored.weight, 80)
        self.assertEqual(restored.reps, 8)
        self.assertEqual(restored.muscle_group, "chest")


class WorkoutTests(unittest.TestCase):
    def test_total_volume_and_exercises(self):
        workout = Workout(workout_date="2026-01-01")
        workout.add_set("squat", 100, 5, "legs")
        workout.add_set("squat", 100, 5, "legs")
        workout.add_set("bench", 80, 5, "chest")
        self.assertEqual(workout.total_volume, 100 * 5 + 100 * 5 + 80 * 5)
        self.assertEqual(workout.exercises(), ["squat", "bench"])


class WorkoutTrackerTests(unittest.TestCase):
    def _sample_tracker(self):
        tracker = WorkoutTracker()
        tracker.log("bench", 80, 5, muscle_group="chest", workout_date="2026-01-01")
        tracker.log("bench", 85, 5, muscle_group="chest", workout_date="2026-01-08")
        tracker.log("squat", 100, 5, muscle_group="legs", workout_date="2026-01-08")
        return tracker

    def test_log_groups_same_day_into_one_workout(self):
        tracker = self._sample_tracker()
        self.assertEqual(len(tracker.workouts), 2)  # two distinct dates

    def test_personal_record(self):
        tracker = self._sample_tracker()
        pr = tracker.personal_record("bench")
        self.assertEqual(pr.weight, 85)
        self.assertIsNone(tracker.personal_record("deadlift"))

    def test_personal_record_is_case_insensitive(self):
        tracker = self._sample_tracker()
        self.assertIsNotNone(tracker.personal_record("BENCH"))

    def test_volume_by_muscle_group(self):
        tracker = self._sample_tracker()
        totals = tracker.volume_by_muscle_group()
        self.assertEqual(totals["chest"], 80 * 5 + 85 * 5)
        self.assertEqual(totals["legs"], 100 * 5)

    def test_progress_is_sorted_by_date(self):
        tracker = self._sample_tracker()
        history = tracker.progress("bench")
        self.assertEqual([d for d, _ in history], ["2026-01-01", "2026-01-08"])
        self.assertLess(history[0][1], history[1][1])

    def test_summary(self):
        tracker = self._sample_tracker()
        summary = tracker.summary()
        self.assertEqual(summary["workouts"], 2)
        self.assertEqual(summary["total_sets"], 3)
        self.assertEqual(summary["total_volume"], 80 * 5 + 85 * 5 + 100 * 5)

    def test_save_and_load_round_trip(self):
        tracker = self._sample_tracker()
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            tracker.save(path)
            reloaded = WorkoutTracker.load(path)
            self.assertEqual(
                reloaded.total_volume(), tracker.total_volume()
            )
            self.assertEqual(len(reloaded.workouts), len(tracker.workouts))
        finally:
            os.remove(path)

    def test_load_missing_file_returns_empty(self):
        tracker = WorkoutTracker.load("/nonexistent/path/workouts.json")
        self.assertEqual(tracker.workouts, [])


if __name__ == "__main__":
    unittest.main()
