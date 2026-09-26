# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

### The game's purpose

A single-player number guessing game built with Streamlit. The app picks a secret number
inside a range set by the difficulty (Easy 1–20, Normal 1–100, Hard 1–50), and the player
has a limited number of attempts to find it — 6, 8, and 5 respectively. After each guess
the game says whether to aim higher or lower, tracks a score, and keeps a history of the
guesses so far. A "Developer Debug Info" panel exposes the internal state, which is what
makes the game usable as a debugging exercise: you can see the secret while you play and
compare it against what the app claims.

### Bugs I found

I found seven. Four make the game unplayable or unwinnable; three make it lie to the player.

| # | Symptom the player sees | Root cause | Severity |
|---|---|---|---|
| 1 | Hints are wrong on some turns but not others | On even-numbered attempts the secret was cast to a string, so `"9" > "50"` compared alphabetically instead of numerically | Unwinnable-ish |
| 2 | "Go HIGHER!" after a guess that was already too high | The two hint messages were swapped in `check_guess` | Misleading |
| 3 | After finishing one round, "New Game" answers "You already won" forever | The reset set only `attempts` and `secret`, leaving `status` on `"won"`, which `st.stop()` then acted on | Unplayable |
| 4 | Sidebar promises 8 attempts, the game gives 7 | `attempts` initialized to 1 on load but 0 in New Game, and the loss check runs after the increment | Off-by-one |
| 5 | The debug panel and "Attempts left" lag one click behind | Streamlit reruns top to bottom; those values were drawn at lines 111–114, before the click was handled further down | Misleading |
| 6 | A wrong guess sometimes *raises* the score | `update_score` returned `+5` for "Too High" on even attempts, `-5` otherwise; the win formula's `100 - 10 * (attempt_number + 1)` also charged for an unused attempt | Wrong math |
| 7 | Switching to Easy leaves a secret of 63 in a 1–20 game | The state guards (`if "secret" not in st.session_state`) run once ever, so difficulty changes updated the labels but not the secret | Unwinnable |

Worth noting: the project brief says "the secret number changes every time you click Submit."
That is not what actually happens. The value is stable for the whole round — it is the
*type* that flips between `int` and `str`. The reported symptom and the real cause were
different things, which is why reading the code beat trusting the bug report.

### Fixes I applied

- **Bugs 1 and 2 — `check_guess`.** Removed the `attempts % 2` branch so the secret is
  always passed as an `int`, and swapped the two hint strings back. I also deleted the
  `except TypeError` fallback that used to wrap the comparison: with the type bug fixed it
  is unreachable, and it had been *hiding* bug 1 by silently catching the error instead of
  letting it surface.
- **Bugs 3 and 7 — one `reset_game()` function.** All five pieces of game state are now
  reset in one place, called both by the New Game button and whenever the difficulty
  changes. A half-reset is no longer possible, because no caller resets state directly.
- **Bug 4 — `attempts` starts at 0** on load, matching what New Game already did.
- **Bug 5 — `st.container()` placeholders.** The info line and debug panel reserve their
  position early but are painted at the end of the script by `paint_status()`, after the
  guess has been processed. `paint_status()` is called on the early-exit path too, so a
  finished game still shows its panels.
- **Bug 6 — `update_score`.** Every wrong guess now costs 5 points regardless of direction
  or attempt parity, and the win payout is `max(10, 100 - 10 * (attempt_number - 1))`, so
  winning on the first guess pays the full 100.
- **The refactor.** All four logic functions moved into `logic_utils.py`, which imports no
  Streamlit. `check_guess` returns only the outcome string, because that is what
  `tests/test_game_logic.py` asserts on; the emoji wording now lives in a `HINTS` dict in
  `app.py`, since phrasing is a UI concern.

One thing I decided *not* to fix: `parse_guess` accepts out-of-range numbers, so guessing
500 in Easy's 1–20 counts as a real attempt and costs 5 points. It is arguably a bug, but
it is a separate concern from the seven above, so I flagged it rather than widening the
change.

## 📸 Demo Walkthrough

1. **Start the app** with `python -m streamlit run app.py`. The sidebar shows Difficulty
   "Normal", "Range: 1 to 100", and "Attempts allowed: 8". The main panel agrees:
   "Guess a number between 1 and 100. Attempts left: 8". Before the fix this read
   "Attempts left: 7" on a fresh load, because the counter started at 1 instead of 0.

2. **Expand "Developer Debug Info"** to peek at the secret. In my run it showed
   `Secret: 7`, `Attempts: 0`, `Score: 0`, `History: []`. The secret is drawn from the
   difficulty's range, so it is always reachable.

3. **Guess 50 and click "Submit Guess".** The hint reads **"📉 Go LOWER!"** — the correct
   direction, since 50 is above 7. Before the fix this said "Go HIGHER!" for a guess that
   was already too high. The debug panel updates on *this* click, not the next one:
   `Attempts: 1`, `Score: -5`, `History: [50]`, and "Attempts left: 7".

4. **Follow the hint and guess 7.** The app shows "🎉 Correct!", fires the balloons, and
   reports **"You won! The secret was 7. Final score: 85"** — that is 90 points for winning
   on attempt 2, minus 5 for the one wrong guess. Wrong guesses now always cost 5 points;
   previously a too-high guess on an even-numbered attempt *added* 5.

5. **Click "New Game".** The round resets completely: a fresh secret, `Attempts: 0`,
   `Score: 0`, `History: []`, and the guess box is live again. Before the fix this button
   left the game's status on "won", so the app answered every later click with
   "You already won. Start a new game to play again." — permanently unplayable until reload.

6. **Switch Difficulty to "Easy".** The sidebar changes to "Range: 1 to 20" and
   "Attempts allowed: 6", *and a new secret inside 1–20 is generated*. Before the fix the
   labels changed but the old secret survived, so Easy could hide a secret of 63 in a
   1–20 game — impossible to win.

7. **Run the tests** with `pytest tests/`. All three pass against `logic_utils.py`, which
   imports no Streamlit at all — the game logic can be tested without launching the app.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
$ pytest tests/ -v

============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Ariana\Downloads\AI110\ai110-module1show-gameglitchinvestigator-starter\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Ariana\Downloads\AI110\ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.15.1
collecting ... collected 19 items

tests/test_edge_cases.py::test_parse_guess_rejects_empty_string PASSED   [  5%]
tests/test_edge_cases.py::test_parse_guess_rejects_whitespace_only PASSED [ 10%]
tests/test_edge_cases.py::test_parse_guess_rejects_non_numeric PASSED    [ 15%]
tests/test_edge_cases.py::test_parse_guess_truncates_decimals PASSED     [ 21%]
tests/test_edge_cases.py::test_parse_guess_rejects_scientific_notation PASSED [ 26%]
tests/test_edge_cases.py::test_parse_guess_accepts_negative_numbers PASSED [ 31%]
tests/test_edge_cases.py::test_parse_guess_accepts_out_of_range_number PASSED [ 36%]
tests/test_edge_cases.py::test_parse_guess_handles_very_large_number PASSED [ 42%]
tests/test_edge_cases.py::test_win_payout_has_a_floor_of_ten PASSED      [ 47%]
tests/test_edge_cases.py::test_unknown_outcome_leaves_score_untouched PASSED [ 52%]
tests/test_edge_cases.py::test_known_difficulties_have_expected_ranges PASSED [ 57%]
tests/test_edge_cases.py::test_unknown_difficulty_falls_back_to_normal PASSED [ 63%]
tests/test_game_logic.py::test_winning_guess PASSED                      [ 68%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [ 73%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 78%]
tests/test_game_logic.py::test_hint_is_not_affected_by_digit_count PASSED [ 84%]
tests/test_game_logic.py::test_type_mismatch_raises_instead_of_comparing_text PASSED [ 89%]
tests/test_game_logic.py::test_wrong_guess_never_increases_score PASSED  [ 94%]
tests/test_game_logic.py::test_win_on_first_attempt_pays_full_points PASSED [100%]

============================= 19 passed in 0.05s ==============================
```

19 tests: the 3 that ship with the starter, 4 regression tests in
`tests/test_game_logic.py` (one per bug fixed, each verified to fail against the original
code), and 12 input edge cases in `tests/test_edge_cases.py` from Optional Challenge 1.
The same output is committed as `test_results.txt`.

## 🚀 Stretch Features

**Challenge 1 — Advanced Edge-Case Testing.** `tests/test_edge_cases.py` adds 12 tests
covering inputs the game was never designed for: empty and whitespace-only strings,
non-numeric text, decimals, scientific notation, negative numbers, out-of-range numbers
and very large values, plus the score floor and the unknown-difficulty fallback. The
full run is in the Test Results section above.

**Challenge 3 — Professional Documentation and Linting.** Every function in
`logic_utils.py` carries a docstring, and flake8 now runs clean over `app.py`,
`logic_utils.py` and `tests/`. The four PEP 8 spacing findings were fixed; the eight
`E501` line-length findings were not, and `setup.cfg` records why.

**Challenge 5 — AI Model Comparison.** Bug 1 was given to Claude Opus 5 and Gemini 1.5
Pro with no hint about the cause; the comparison is in `ai_interactions.md`.

Prompts, linter output and the model comparison are all documented in
`ai_interactions.md`.
