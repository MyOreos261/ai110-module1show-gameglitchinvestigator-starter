# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

Tool used: **Claude Code** (agent mode, running in a terminal with file-edit and
browser-automation access).

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
The agent flagged it and did not fix it, on the grounds that it was outside the seven bugs
in scope. I agreed, but that was my call to make, not its.

**Takeaway:** the agent was fastest at the mechanical parts — inventorying bugs with line
numbers, applying edits, running the suite. It was least reliable when explaining *why*
something broke without having executed it first. Every claim it made that I checked against
real output either held up or got corrected; the ones that were wrong were wrong
confidently.

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

The starter ships three tests, all covering the happy path of `check_guess()`. I asked
Claude for edge cases beyond that, with one prompt for the batch and follow-ups per case.
The results are split across two files: the four **regression** tests (one per bug fixed)
live in `tests/test_game_logic.py`, and the twelve **input edge cases** live in
`tests/test_edge_cases.py`. Full suite: **19 passed** — see `test_results.txt`.

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

**The thing that should make me suspicious.** All 19 tests passed on the first run. That
sounds like a good result, but the same assistant wrote both the fixes and the tests for
them, so agreement between the two proves less than it looks — a test suite that only ever
confirms its author is a weak check. That is exactly why I re-ran the regression tests
against the *original* buggy code: those three failures came from code the assistant did
not write, so they are the only results in this project that constitute independent
evidence. The rest document behavior; they do not independently verify it.

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

Docstrings came first: every function in `logic_utils.py` (and the module itself) was
given one during the Phase 2 refactor, so this pass was only about style enforcement.
No linter was installed in the venv, so step one was picking one and getting a baseline.

**Prompt used:**

```
Install a linter in the venv and run it over app.py, logic_utils.py and tests/.
Show me the output BEFORE changing anything, then apply the PEP 8 fixes and
re-run so I can see it clean. Tell me which suggestions you did not apply and why
-- I do not want churn in working code just to satisfy a default setting.
```

The last sentence was deliberate. Asking only "make it PEP 8 compliant" invites an
assistant to rewrite whatever the tool complains about; asking it to *justify* what it
skipped keeps the judgment call with me.

**Linting output before:**

```
$ python -m flake8 app.py logic_utils.py tests/
app.py:51:1: E302 expected 2 blank lines, found 1
app.py:95:1: E305 expected 2 blank lines after class or function definition, found 1
tests/test_game_logic.py:22:1: E302 expected 2 blank lines, found 1
tests/test_game_logic.py:27:1: E302 expected 2 blank lines, found 1
```

At flake8's default width of 79 columns there were 8 more, all `E501 line too long`,
the longest being 84 characters:

```
5  E501 line too long (80 > 79 characters)
3  E302 expected 2 blank lines, found 1
1  E501 line too long (84 > 79 characters)
1  E501 line too long (82 > 79 characters)
1  E501 line too long (81 > 79 characters)
1  E305 expected 2 blank lines after class or function definition, found 1
```

**Changes applied:**

- **All 4 spacing findings fixed.** Two blank lines before `reset_game()`'s comment block
  and before the `raw_guess` statement in `app.py`, and before the second and third
  starter tests in `tests/test_game_logic.py`. These are real PEP 8 rules and the fix
  costs nothing.
- **The 8 `E501` findings: not applied.** Instead I set `max-line-length = 100` in a new
  `setup.cfg`. The over-long lines are comment prose explaining the bug fixes, already
  wrapped at roughly 88 columns and consistent with each other. Rewrapping them to 79
  would have reflowed paragraphs of working commentary to satisfy a terminal width no one
  uses, and it would have churned the diff on lines that have nothing to do with the bugs.
  Black defaults to 88 for the same reason. Configuring the limit is an honest choice; it
  is recorded in `setup.cfg` with the reasoning next to it, not hidden behind a
  `# noqa`.
- **Nothing was renamed.** The linter flagged no naming issues, and I did not go looking
  for cosmetic renames that would break the imports in `app.py` and the tests.

**Linting output after:**

```
$ python -m flake8 app.py logic_utils.py tests/
$ echo $?
0
$ python -m pytest tests/ -q
...................                                                      [100%]
19 passed in 0.04s
```

Clean, and the suite still passes -- worth checking, because blank-line edits are exactly
the kind of "safe" change that can silently break an indentation-sensitive language.

---

## Model Comparison (SF11)

> Compare two AI models on the same task.


**Task given to both models:**

Both models were given the original Bug 1 code from `app.py` and asked to diagnose and fix
it, with no hint about what was wrong:

```
This is from a Streamlit number-guessing game. Players report that the
"higher/lower" hints are wrong on some turns but correct on others.
What is the bug, and how would you fix it?

    if st.session_state.attempts % 2 == 0:
        secret = str(st.session_state.secret)
    else:
        secret = st.session_state.secret

    outcome, message = check_guess(guess_int, secret)

And check_guess:

    def check_guess(guess, secret):
        try:
            if guess == secret:
                return "Win", "Correct!"
            if guess > secret:
                return "Too High", "Go HIGHER!"
            return "Too Low", "Go LOWER!"
        except TypeError:
            return check_guess(str(guess), str(secret))
```

This bug was chosen because it has a trap in it: the `except TypeError` fallback means the
code does not crash, so a model that only skims will call it safe. The real symptom is
narrower than it looks -- only guesses with a different digit count than the secret get
inverted hints, because `"9" > "50"` compares alphabetically.

| | Model A | Model B |
|-|---------|---------|
| **Model name** | Claude Opus 5 (Claude Code, agent mode) | Gemini 1.5 Pro |
| **Response summary** | Found the string cast and the swapped hint strings. Also flagged the `except TypeError` as actively harmful -- it was *hiding* the type error rather than handling it -- and deleted it, then added a regression test asserting the comparison now raises. Initially overstated the severity, claiming the game was unwinnable on even attempts; running the code disproved that and it corrected itself. | Correctly identified that secret was being cast to a string on even attempts, causing string-based lexicographical comparison (e.g., "9" > "50" evaluates to True). It recommended removing the conditional string cast in app.py to ensure both arguments remain integers. It noted that the hints "Go HIGHER!" and "Go LOWER!" were inverted relative to "Too High" and "Too Low". However, it treated except TypeError as an acceptable fallback and suggested keeping str() conversion inside check_guess rather than letting it fail early. |
| **More Pythonic?** | Mostly yes, and by subtraction. The fix deleted code rather than adding it: the attempts % 2 branch and the bare except TypeError both went, leaving three guard-clause returns and no else. It refused to catch TypeError, arguing that the exception carried real information and swallowing it allowed the bug to hide for so long. EAFP isn't a license to catch and continue. It also split the outcome from its wording (check_guess returns "Win" / "Too High" / "Too Low"; the emoji strings live in a HINTS dict at app.py:16), which is what made the function testable without importing Streamlit. Where it is not especially Pythonic: those three outcomes are bare string literals passed between modules and compared with ==. An Enum or even module constants would be the idiomatic choice, and it did not suggest one — it matched the starter's existing string contract instead, which was the right call for the assignment but is not the right call for real code. | Less so, because its fix was *additive*. It kept the `except TypeError`, kept a `str()` coercion inside `check_guess`, and corrected only the cast at the call site. That leaves the function quietly accepting two types and deciding what to do about them -- the opposite of "explicit is better than implicit" -- and it preserves the exact construct that hid the bug for so long. The code it wrote was clean and its diagnosis was right; it just treated the safety net as something to tidy rather than something to remove. |
| **Clearer explanation?** | Clear, but only on the second pass — and the gap is the interesting part. The mechanical explanation was genuinely good: it said why "9" > "50" is True (character-by-character comparison, '9' outranks '5', so the length of the number never enters into it) rather than just asserting the comparison was wrong, and that is the detail that makes the "wrong on some turns but not others" symptom finally make sense. But its first account of the impact was confidently wrong — it claimed the game was unwinnable on even-numbered attempts, when the except TypeError fallback stringified both sides so "50" == "50" still won. It only corrected that after running the code. So: strong at explaining the mechanism it could read, unreliable at predicting the behavior until it executed something. The explanation I'd actually trust is the one that arrived with output attached — tests/test_game_logic.py:47, which asserts the comparison now raises instead of silently comparing text. | Model B gave a clearer, more immediate explanation of why string comparisons fail (lexicographical sorting where "9" comes after "50"), without overstating the bug or incorrectly claiming the game was impossible to win. |

**Which did you prefer and why?**
Model A (with reservations).

While Model B gave a clearer initial explanation of lexicographical string comparison without overstating the issue, Model A provided a far superior engineering fix. Model A recognized that swallowing TypeError in check_guess was an anti-pattern hiding bugs, removed the dangerous try/except block, and wrote a regression test asserting that passing mismatched types explicitly raises an error. Model A required execution to correct its initial explanation, but its resulting refactored code and test coverage were significantly higher quality.
