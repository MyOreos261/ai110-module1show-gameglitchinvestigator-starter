"""Edge-case tests (Optional Challenge 1: Advanced Edge-Case Testing).

These cover unusual INPUTS rather than the fixed bugs -- the regression tests
live in test_game_logic.py. Several of these assert behavior I consider
imperfect; they are here to make the gap visible rather than to endorse it.
"""

from logic_utils import get_range_for_difficulty, parse_guess, update_score


# --- parse_guess: unusual input --------------------------------------------

def test_parse_guess_rejects_empty_string():
    assert parse_guess("") == (False, None, "Enter a guess.")


def test_parse_guess_rejects_whitespace_only():
    # Chosen because a space is not an empty string: the original `raw == ""`
    # check missed it and reported "That is not a number." instead.
    assert parse_guess("   ") == (False, None, "Enter a guess.")


def test_parse_guess_rejects_non_numeric():
    assert parse_guess("abc") == (False, None, "That is not a number.")


def test_parse_guess_truncates_decimals():
    # Chosen because the intuitive answer is 8. int(float("7.9")) truncates to
    # 7, so this documents actual behavior rather than expected behavior.
    assert parse_guess("7.9") == (True, 7, None)


def test_parse_guess_rejects_scientific_notation():
    # Chosen because it is inconsistent: float("1e3") is 1000.0, but "1e3" has
    # no ".", so it takes the int() branch and is rejected.
    ok, value, err = parse_guess("1e3")
    assert ok is False


def test_parse_guess_accepts_negative_numbers():
    # Chosen because no range check exists: -5 is a "valid" guess in a 1-100 game.
    assert parse_guess("-5") == (True, -5, None)


def test_parse_guess_accepts_out_of_range_number():
    # KNOWN GAP, asserted deliberately: parse_guess does not know the
    # difficulty range, so 500 is accepted in Easy (1-20) and burns an attempt.
    assert parse_guess("500") == (True, 500, None)


def test_parse_guess_handles_very_large_number():
    # Chosen because Python ints are unbounded -- no overflow, just a huge int.
    ok, value, err = parse_guess("9" * 50)
    assert ok is True and value == int("9" * 50)


# --- update_score: boundary values -----------------------------------------

def test_win_payout_has_a_floor_of_ten():
    assert update_score(0, "Win", 50) == 10


def test_unknown_outcome_leaves_score_untouched():
    assert update_score(42, "Banana", 3) == 42


# --- get_range_for_difficulty ----------------------------------------------

def test_known_difficulties_have_expected_ranges():
    assert get_range_for_difficulty("Easy") == (1, 20)
    assert get_range_for_difficulty("Normal") == (1, 100)
    assert get_range_for_difficulty("Hard") == (1, 50)


def test_unknown_difficulty_falls_back_to_normal():
    assert get_range_for_difficulty("Impossible") == (1, 100)
