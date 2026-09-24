"""Pure game logic for the guessing game.

FIX (refactor): all four functions were moved here out of app.py using the AI
assistant in agent mode, one multi-step instruction: move the functions, fix
the high/low bug, update the imports. I reviewed the diff before accepting it
-- the one thing the AI could NOT copy across was check_guess's return type
(see below), and it flagged that itself rather than silently breaking the tests.


Nothing here imports streamlit. That is the point of the split: these
functions can be tested with plain pytest, without running the app.

Note that check_guess() returns only the outcome string ("Win" / "Too High" /
"Too Low"). The player-facing message lives in app.py, because wording is a
UI concern -- and because tests/test_game_logic.py asserts on the bare string.
"""


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    # FIX (input validation): the original checked `raw == ""`, so a
    # whitespace-only guess slipped through to int() and was reported as
    # "That is not a number." instead of "Enter a guess."
    if raw is None or raw.strip() == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except ValueError:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """Compare guess to secret and return one of "Win", "Too High", "Too Low"."""
    # FIX (bug 1): app.py's version wrapped this in `except TypeError`, which
    # swallowed the int-vs-str mismatch and fell back to comparing text. Letting
    # it raise is deliberate: tests/test_game_logic.py asserts that it does.
    if guess == secret:
        return "Win"

    if guess > secret:
        return "Too High"

    return "Too Low"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    # FIX (bug 6, scoring): "Too High" used to return +5 on even-numbered
    # attempts, so a wrong guess could RAISE your score, and the win formula's
    # `attempt_number + 1` charged for a guess never taken.
    if outcome == "Win":
        # Win on attempt 1 -> 100 points, losing 10 per extra attempt used,
        # never dropping below 10.
        points = max(10, 100 - 10 * (attempt_number - 1))
        return current_score + points

    if outcome in ("Too High", "Too Low"):
        # Every wrong guess costs the same, whichever direction it missed.
        return current_score - 5

    return current_score
