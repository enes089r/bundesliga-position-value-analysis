import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.srs import (
    WordState,
    apply_correct,
    apply_incorrect,
    interval_days,
    is_derivation_activation_level,
    is_due,
    next_review_date,
)


def test_intervals():
    assert interval_days(1) == 1
    assert interval_days(2) == 2
    assert interval_days(3) == 4
    assert interval_days(4) == 9
    assert interval_days(5) == 14


def test_next_review_date_and_is_due():
    start = date(2026, 1, 1)
    assert next_review_date(start, 2) == date(2026, 1, 3)
    assert is_due(start, 2, date(2026, 1, 2)) is False
    assert is_due(start, 2, date(2026, 1, 3)) is True
    assert is_due(start, 2, date(2026, 1, 4)) is True


def test_apply_correct_moves_up_a_level():
    today = date(2026, 1, 1)
    state = WordState(level=1, level_start_date=date(2025, 12, 1), streak5=0, is_known=False)
    new_state = apply_correct(state, today)
    assert new_state.level == 2
    assert new_state.level_start_date == today
    assert new_state.streak5 == 0
    assert new_state.is_known is False


def test_apply_correct_entering_level5_counts_as_first_streak():
    today = date(2026, 1, 1)
    state = WordState(level=4, level_start_date=date(2025, 12, 1), streak5=0, is_known=False)
    new_state = apply_correct(state, today)
    assert new_state.level == 5
    assert new_state.streak5 == 1
    assert new_state.is_known is False


def test_level5_becomes_known_after_three_correct_total_28_days():
    day0 = date(2026, 1, 1)
    state = WordState(level=4, level_start_date=date(2025, 12, 1), streak5=0, is_known=False)

    # Level 4 -> 5 (1. dogru, gun 0)
    state = apply_correct(state, day0)
    assert state.level == 5 and state.streak5 == 1 and not state.is_known

    # 14 gun sonra (2. dogru)
    day14 = day0 + timedelta(days=interval_days(5))
    assert is_due(state.level_start_date, state.level, day14)
    state = apply_correct(state, day14)
    assert state.streak5 == 2 and not state.is_known

    # 14 gun sonra (3. dogru) -> Bilinenler
    day28 = day14 + timedelta(days=interval_days(5))
    assert is_due(state.level_start_date, state.level, day28)
    state = apply_correct(state, day28)
    assert state.streak5 == 3 and state.is_known is True
    assert (day28 - day0).days == 28


def test_level5_failure_drops_to_4_and_resets_streak():
    today = date(2026, 1, 15)
    state = WordState(level=5, level_start_date=date(2026, 1, 1), streak5=2, is_known=False)
    new_state = apply_incorrect(state, today)
    assert new_state.level == 4
    assert new_state.streak5 == 0
    assert new_state.level_start_date == today


def test_level1_failure_stays_at_level1():
    today = date(2026, 1, 15)
    state = WordState(level=1, level_start_date=date(2026, 1, 1), streak5=0, is_known=False)
    new_state = apply_incorrect(state, today)
    assert new_state.level == 1
    assert new_state.level_start_date == today


def test_known_word_is_frozen():
    today = date(2026, 1, 15)
    state = WordState(level=5, level_start_date=date(2026, 1, 1), streak5=3, is_known=True)
    assert apply_correct(state, today) == state
    assert apply_incorrect(state, today) == state


def test_is_derivation_activation_level():
    assert is_derivation_activation_level(3) is False
    assert is_derivation_activation_level(4) is True
    assert is_derivation_activation_level(5) is True
