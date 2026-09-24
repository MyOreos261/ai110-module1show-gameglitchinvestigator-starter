"""Tests for the core game logic.

The first three tests ship with the starter and cover the happy path of
check_guess(). The rest are REGRESSION tests I added in Phase 2: each one
targets a specific bug that was fixed, and each one FAILS against the original
code. I verified that by re-creating the old buggy functions in a scratch
script and running these same assertions against them.
"""

import pytest

from logic_utils import check_guess, update_score


# --- starter tests ---------------------------------------------------------

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# --- regression tests for the bugs fixed in Phase 2 ------------------------

def test_hint_is_not_affected_by_digit_count():
    """Bug 1: the secret was cast to str on even attempts, so comparisons ran
    alphabetically -- "9" > "50" is True, which inverted the hint. Only guesses
    with a different digit count than the secret broke, which is why it looked
    random. Against the old code this returned "Too High" for a guess of 9.
    """
    assert check_guess(9, 50) == "Too Low"
    assert check_guess(100, 50) == "Too High"


def test_type_mismatch_raises_instead_of_comparing_text():
    """Bug 1, the other half: the original wrapped the comparison in a bare
    `except TypeError` that silently fell back to string comparison. Failing
    loudly is the intended behavior now. Against the old code, no error raised.
    """
    with pytest.raises(TypeError):
        check_guess(50, "50")


def test_wrong_guess_never_increases_score():
    """Bug 6: "Too High" returned +5 on even-numbered attempts, so a wrong guess
    could RAISE your score. Looping over attempt numbers because the bug was
    parity-dependent -- a single hardcoded attempt could pass by luck.
    Against the old code, attempts 2, 4, 6... returned +5.
    """
    for attempt in range(1, 11):
        assert update_score(0, "Too High", attempt) == -5
        assert update_score(0, "Too Low", attempt) == -5


def test_win_on_first_attempt_pays_full_points():
    """Bug 6: the old formula was `100 - 10 * (attempt_number + 1)`, charging
    for an attempt never taken. Against the old code this returned 80.
    """
    assert update_score(0, "Win", 1) == 100
