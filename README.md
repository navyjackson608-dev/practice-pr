# practice-pr

A small collection of dependency-free Python utilities.

## String utilities

Common string operations (`string_utils.py`):

- Count words in a string
- Reverse a string
- Check if a string is a palindrome

```python
from string_utils import count_words, reverse_string, is_palindrome

print(count_words("hello world"))   # 2
print(reverse_string("hello"))      # "olleh"
print(is_palindrome("racecar"))     # True
```

## Muscle training tracker

Log strength-training workouts and track your progress
(`workout_tracker.py`). Data is stored as human-readable JSON.

### As a library

```python
from workout_tracker import WorkoutTracker

tracker = WorkoutTracker.load("workouts.json")
tracker.log("bench", 80, 5, muscle_group="chest", workout_date="2026-01-01")
tracker.log("bench", 85, 5, muscle_group="chest", workout_date="2026-01-08")

print(tracker.personal_record("bench"))   # heaviest set logged
print(tracker.progress("bench"))          # estimated-1RM history
print(tracker.summary())                  # headline stats

tracker.save("workouts.json")
```

### From the command line

```bash
# Log a set (creates/updates workouts.json)
python3 workout_tracker.py log bench 80 5 --muscle-group chest --date 2026-01-01

# Review your training
python3 workout_tracker.py summary
python3 workout_tracker.py pr bench
python3 workout_tracker.py progress bench
```

Estimated one-rep max (1RM) uses the Epley formula:
`1RM = weight * (1 + reps / 30)`.

## Running the tests

```bash
python3 -m unittest discover
```

## Installation

No external dependencies required. Python 3.8+ recommended.
