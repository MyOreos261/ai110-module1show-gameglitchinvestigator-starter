# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked it to walk me through fixing the game one bug at a time, rather than handing me a
finished repo. The constraint mattered: I wanted to see each symptom reproduced *before*
the fix and verified *after* it, so I could tell the difference between "the code changed"
and "the bug is gone." It worked through the four required tasks in order — find the state
bug, fix the hints, refactor into `logic_utils.py`, get `pytest` green — and I approved
each step before it moved on.

**What did the agent do?**

- Read `app.py`, `logic_utils.py`, `tests/test_game_logic.py` and the README, then produced
  an inventory of 7 bugs with line references before editing anything.
- Ran the test suite first to establish a baseline: 3 failures, all `NotImplementedError`.
- Created the virtual environment and installed `requirements.txt`.
- For each bug: reproduced the symptom, explained the root cause, applied the edit, then
  re-verified. Two bugs it proved with throwaway Python scripts that imported `app.py` with
  `streamlit` stubbed out; the other five it demonstrated in the running app by driving a
  browser — reading the secret out of the Developer Debug panel, submitting guesses, and
  reading the result back.
- Moved the four logic functions into `logic_utils.py`, rewired `app.py` to import them,
  and got the suite to 3 passed.
- Filled in the README's Demo Walkthrough and Document Your Experience sections.

**What did you have to verify or fix manually?**

Three things needed correcting, and all three were caught by *running* the code rather than
reading the agent's explanation:

1. **It overstated the first bug.** Its initial write-up said the string-cast bug made the
   game impossible to win on even-numbered attempts. Running it showed that was wrong: the
   `except TypeError` fallback stringified the guess too, so `"50" == "50"` still won. The
   real damage was narrower and stranger — only guesses with a different digit count than
   the secret got inverted hints. The agent corrected itself once it had actual output, but
   the confident wrong explanation came first, and if I had pasted it straight into my
   reflection it would have been a false claim.

2. **Its first fix for the stale-display bug broke a different path.** It used `st.empty()`
   placeholders painted at the end of the script — but `st.stop()` fires earlier on a
   finished game, so the panels would have rendered blank after a win. It caught this
   itself while re-reading, and restructured into a `paint_status()` function called on
   both exit paths.

3. **That same fix introduced a small UI regression.** With `st.empty()`, the debug expander
   snapped shut on every rerun, because the placeholder rebuilt the widget from scratch each
   time. Only visible by actually clicking through the app — the code looked fine. Switching
   to `st.container()` fixed it.

I also had to ratify a judgment call it deliberately left open: `parse_guess` accepts
out-of-range numbers, so guessing 500 in Easy's 1–20 burns an attempt and costs 5 points.
The agent flagged it and did not fix it, because it was outside the seven bugs
in scope. I agreed, but that was my call to make, not its.

**Takeaway:** the agent was fastest at the mechanical parts — inventorying bugs with line
numbers, applying edits, running the suite. It was least reliable when explaining *why*
something broke without having executed it first. Every claim it made that I checked against
real output either held up or got corrected; the wrong ones were wrong
confidently."""

The starter ships three tests, all covering the happy path of `check_guess()`. I asked
Claude for edge cases beyond that, with one prompt for the batch and follow-ups per case.
The results live in `tests/test_edge_cases.py` (14 tests). Full suite: **17 passed**.

**Base prompt:** *"Look at logic_utils.py. What edge cases do the existing three tests miss?
Suggest pytest tests for them. Include regression tests for the bugs we just fixed, so they
can't come back silently."*

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |
|-----------|-------------|-------------------|--------------|----------------|
| Whitespace-only input `"   "` | Base prompt | `assert parse_guess("   ") == (False, None, "Enter a guess.")` | ✅ Passed | Accepted. The original `raw == ""` check missed this — a space fell through to `int("   ")` and got reported as *"That is not a number."*, which is technically a rejection but the wrong message. The test pins the clearer one. |
| Decimal input `"7.9"` | Base prompt | `assert parse_guess("7.9") == (True, 7, None)` | ✅ Passed | Accepted. Worth a test because the intuitive answer is 8 — `int(float("7.9"))` truncates rather than rounds, so a reader who assumes rounding is wrong. The test documents actual behavior, not wished-for behavior. |
| Out-of-range guess `"500"` in Easy (1–20) | *"Does parse_guess know about the difficulty range?"* | `assert parse_guess("500") == (True, 500, None)` | ✅ Passed | Accepted **as a marker, not an endorsement**. The test asserts behavior I think is wrong — 500 is accepted and burns an attempt. I kept it so the gap is visible in the suite instead of forgotten, with a `KNOWN GAP` comment. |
| Mismatched types `check_guess(50, "50")` | *"Write a regression test for the string-cast bug"* | `with pytest.raises(TypeError): check_guess(50, "50")` | ✅ Passed on fixed code; **fails on the original** (no error raised) | Accepted, and the most valuable one. The original swallowed this in `except TypeError` and silently compared text. Asserting that it now *raises* locks in "fail loudly" as the intended behavior. |
| Wrong guess on an even attempt | *"Write a regression test for the scoring bug"* | `for a in range(1, 11): assert update_score(0, "Too High", a) == -5` | ✅ Passed on fixed code; **fails on the original** (returns `+5` on even attempts) | Accepted. I asked for the loop rather than a single case, because the bug was *parity*-dependent — one hardcoded attempt number could have passed by luck. |
| Winning on the very first guess | Base prompt | `assert update_score(0, "Win", 1) == 100` | ✅ Passed on fixed code; **fails on the original** (returns `80`) | Accepted. The old `100 - 10 * (attempt_number + 1)` charged for an attempt never taken. |
| Scientific notation `"1e3"` | *"What other numeric strings might break parse_guess?"* | `ok, value, err = parse_guess("1e3"); assert ok is False` | ✅ Passed | Accepted as documentation. This surprised me: `float("1e3")` is 1000.0, but since `"1e3"` contains no `"."` it takes the `int()` branch and is rejected. Inconsistent, but out of scope — the test records it. |
| Unknown difficulty string | Base prompt | `assert get_range_for_difficulty("Impossible") == (1, 100)` | ✅ Passed | Accepted. The fallback was already correct; the test stops a future edit from removing it. |

**How I verified the regression tests were real.** A regression test that passes tells you
nothing on its own — it might be asserting something that was never broken. I re-created the
three original buggy functions in a scratch script and ran the new assertions against them.
All three failed, with the exact wrong values (`+5` instead of `-5`, `80` instead of `100`,
and no `TypeError` at all). That is what makes them regression tests rather than decoration.

**The thing that should make me suspicious.** All 14 tests passed on the first run. That
sounds like a good result, but the same assistant wrote both the fixes and the tests for
them, so agreement between the two proves less than it looks — a test suite that only ever
confirms its author is a weak check. That is exactly why I re-ran the regression tests
against the *original* buggy code: those three failures came from code the assistant did
not write, so they are the only results in this table that constitute independent evidence.
The remaining eleven tests document behavior; they do not independently verify it.

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

**Prompt used:**

```
<!-- Paste the prompt you gave the AI -->
```

**Linting output before:**

```
<!-- Paste relevant linter warnings/errors -->
```

**Changes applied:**

<!-- Describe what you changed based on the AI's suggestions -->

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

<!-- Describe what you asked each model to do -->

| | Model A | Model B |
|-|---------|---------|
| **Model name** | | |
| **Response summary** | | |
| **More Pythonic?** | | |
| **Clearer explanation?** | | |

**Which did you prefer and why?**

<!-- Your conclusion -->
