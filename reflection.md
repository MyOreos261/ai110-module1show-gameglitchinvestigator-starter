# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The first run looked deceptively fine. The app loaded, the sidebar showed "Range: 1 to 100"
and "Attempts allowed: 8", and the guess box worked. Nothing crashed — there was no traceback
anywhere, which is what made this harder than a syntax-error bug hunt. Everything was a
*wrong answer*, not an error message.

The first thing that felt off was small: the sidebar promised 8 attempts but the main panel
said "Attempts left: 7" before I had guessed anything. The second was the one the project
description warns about — the hints were backwards. I opened the Developer Debug Info panel
to see the secret, guessed a number well above it, and the game told me to go HIGHER.

The third took longer to pin down, and it is the one I got wrong at first. Following the
hints sometimes worked and sometimes didn't, which felt like the secret was changing between
guesses. It wasn't. The secret held the same value all game — on even-numbered attempts the
code converted it to a *string*, so the comparison ran alphabetically instead of numerically.
`"9" > "50"` is True, because `9` sorts after `5`. Only guesses with a different digit count
than the secret broke, which is exactly why it felt random rather than consistently wrong.

**Bug Reproduction Log**

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| Secret 33, guess `80`, first attempt | Hint says "Go LOWER" | Hint said **"📈 Go HIGHER!"** | No error. `check_guess` returned the correct label `"Too High"` but was paired with the wrong message string. |
| Secret 50, guess `9`, on an **even-numbered** attempt | Outcome "Too Low" | Outcome **"Too High"** | No error — silently wrong. Reproduced outside Streamlit: `check_guess(9, "50")` → `"Too High"`, because `"9" > "50"` compares as text. |
| Fresh page load, Normal difficulty | "Attempts left: 8", matching the sidebar | "Attempts left: **7**" | No error. `attempts` initialized to `1` on load but to `0` in New Game — two code paths, two values. |
| Win a round, then click **New Game** | A fresh round starts | **"You already won. Start a new game to play again."** — permanently, until browser reload | No error. Debug panel showed the reset *had* half-happened: new secret, `Attempts: 0`, but `Score: 65` and `History: [80, 15]` carried over, and `status` was still `"won"`. |
| Secret 33, guess `80` (wrong), on attempt 2 | Score decreases | Score went **up to +5** | No error. `update_score` returned `+5` for `"Too High"` when `attempt_number % 2 == 0`. |
| Submit any guess, then read the debug panel | Panel shows the guess I just made | Panel showed `Attempts: 1`, `History: []` *after* submitting — one click behind | No error. Streamlit reruns top to bottom; the panel was drawn at line 114, the guess handled at line 147. |
| Mid-game, switch Difficulty from Normal to **Easy** | New secret inside 1–20 | Sidebar said "Range: 1 to 20" while the debug panel still showed **`Secret: 63`** — unwinnable | No error. The `if "secret" not in st.session_state` guard only ever runs once. |

Seven bugs total, and **not one of them produced a traceback**. That is the thing I would
tell someone starting this project: the console stays clean the whole way through, so the
debug panel and deliberately comparing expected-vs-actual are the only tools that find
anything.

One correction worth recording. The project brief says "the secret number seems to have
commitment issues" and asks *"Why does the secret number change every time you click
Submit?"* — but that is not what happens. The value never changes during a round; the type
flips between `int` and `str`. I initially believed the brief and went looking for a stray
`random.randint()` call inside the submit handler. There isn't one. Reading the code beat
trusting the bug report.

---

## 2. How did you use AI as a teammate?

I used **Claude Code** in agent mode — it could read the files, edit them, run `pytest`, and
drive a browser against the running Streamlit app. That last part mattered more than I
expected: several of these bugs are only visible by clicking through the UI, not by reading
the code.

**A suggestion I accepted: extract one `reset_game()` function.**

My instinct for bug 3 was to add the three missing lines to the New Game handler —
`score = 0`, `status = "playing"`, `history = []` — and move on. The AI argued for pulling
all five resets into a single `reset_game()` function called from both the New Game button
and the difficulty-change check. I took it, because it fixes the *class* of bug rather than
the instance: the original bug was somebody resetting only part of the state, and with one
function owning all of it, a partial reset is no longer something you can forget to do.

I verified it in the running app rather than by reading the diff. I won a round (score 85),
clicked New Game, and watched the Developer Debug panel: `Secret` changed, `Attempts: 0`,
`Score: 0`, `History: []`, and no "You already won" message. Then I switched difficulty
from Normal to Easy mid-game and confirmed the secret was re-rolled inside 1–20 instead of
stranding a 63.

**A suggestion I did not accept as written: `st.empty()` for the stale display.**

For bug 5 the AI proposed reserving the info line and debug panel with `st.empty()` at the
top of the script and filling them at the bottom, after the guess is handled. The core idea
was right and I kept it. Two things about the specific implementation were not.

First, it would have broken a path it wasn't looking at. `st.stop()` fires earlier for a
finished game, so after a win the script never reaches the filling code and both panels
would have rendered blank. That got fixed by extracting a `paint_status()` function and
calling it on the early-exit path too.

Second — and this one only showed up by clicking — `st.empty()` *replaces* its contents
every rerun, which rebuilds the expander from scratch, so the debug panel snapped shut
after every single guess. The code looked completely fine. Switching to `st.container()`,
which appends rather than replaces, preserved the widget's open state.

I verified the corrected version the same way I found the problem: submitted a guess with
the panel open, confirmed it stayed open *and* that "Attempts left" dropped from 8 to 7 on
that same click rather than the next one.

---

## 3. Debugging and testing your fixes

The rule I settled on: **reproduce it first, or you cannot claim to have fixed it.** For
every bug I got the wrong behavior to happen on demand before changing any code, then ran
the exact same steps afterward. Without that, "I changed something and the symptom went
away" is a guess.

For bug 1 the reproduction ran outside Streamlit. I imported `app.py` with the `streamlit`
module stubbed out and printed a table comparing each guess against an `int` secret and a
`str` secret:

```
 guess |     truth |  odd attempt (int) | even attempt (str)
     9 |     lower |            Too Low |           Too High  <-- WRONG
    40 |     lower |            Too Low |            Too Low
    50 |   correct |                Win |                Win
    60 |    higher |           Too High |           Too High
   100 |    higher |           Too High |            Too Low  <-- WRONG
```

That table is what corrected my understanding of the bug. My first theory — and the AI's
first explanation — was that the string cast made the game impossible to win on even
attempts. The table shows `50` still returns `Win`, because the `except TypeError` fallback
stringified the *guess* too, so `"50" == "50"` matched. The real damage was narrower: only
guesses with a different digit count than the secret were inverted. I would have written a
false claim in this reflection if I had trusted the explanation instead of running it.

**The most useful test: `test_wrong_guess_never_increases_score`.**

```python
for attempt in range(1, 11):
    assert update_score(0, "Too High", attempt) == -5
    assert update_score(0, "Too Low", attempt) == -5
```

The loop is the point. Bug 6 was *parity*-dependent — `+5` on even attempts, `-5` on odd —
so a test hardcoding a single attempt number had a 50% chance of passing against broken
code. Testing a range makes that impossible.

**Proving the regression tests were real.** A regression test that passes tells you nothing
by itself; it might be asserting something that was never broken. So I re-created the three
original buggy functions in a scratch script and ran the new assertions against them. All
three failed, with exactly the wrong values I expected: `+5` instead of `-5`, `80` instead
of `100`, and no `TypeError` raised at all. That is the step that turns a test into
evidence.

**Did AI help design the tests?** Yes, and it was genuinely good at the mechanical part —
it suggested `pytest.raises(TypeError)` for the swallowed-exception case, and the loop over
attempt numbers rather than a single value. What it could not do was tell me whether the
tests were meaningful, because it wrote both the fixes and the tests for them. All 19 passed
on the first run, which sounds like success but is weak evidence: a suite that only ever
agrees with its author is not an independent check. The three failures against the *old*
code are the only results in this project that came from code the assistant did not write.

---

## 4. What did you learn about Streamlit and state?

Here is how I would put it. Most apps are event-driven: you click a button, and a function
runs that handles the click. Streamlit does not work that way. **Every interaction re-runs
your entire script from line 1 to the last line.** Click a button, move a slider, type in a
box — the whole file executes again, top to bottom.

That means every ordinary Python variable resets on every click. The button itself isn't
"pressed" in any lasting sense; `st.button(...)` simply returns `True` during the one rerun
that follows the click, and `False` on every other run. So `count = 0` followed by
`count += 1` can never reach 2 — the `count = 0` line runs again first.

`st.session_state` is the escape hatch: a dictionary that survives reruns. Anything that
needs to outlive a click — the secret number, the score, the attempt count — goes in there,
and you initialize it with a guard (`if "secret" not in st.session_state`) so the
initialization doesn't clobber the value on the next rerun.

This project had a bug at each end of that idea:

- **Bug 3** was state that persisted when it shouldn't have. `status` stayed `"won"` because
  the New Game handler never reset it, and `st.stop()` acted on the leftover value forever.
- **Bug 7** was the *guard* being too effective. `if "secret" not in st.session_state` runs
  exactly once in the session's lifetime, so changing difficulty updated every label but
  never the secret it described.

And **bug 5** is the part I genuinely did not anticipate: top-to-bottom execution means
**order on the page is order in time.** The debug panel was written at line 114 and the
guess was handled at line 147, so the panel was painted with state from *before* the click
every single time. Nothing was stale in the data — it was stale in the script. The fix was
to reserve the spot early with `st.container()` and fill it at the end, once the state had
actually changed.

The mental model I'd hand a friend: *the script is the event handler, and it runs in full
every time. If a value must survive, put it in session_state. If a value must be displayed
accurately, draw it after you change it, not before.*

---

## 5. Looking ahead: your developer habits

**The habit I'm keeping: prove the test fails before trusting that it passes.** Writing a
regression test against already-fixed code is nearly free and nearly worthless — it will
pass whether or not it is checking anything real. Taking the extra two minutes to run those
three assertions against the original buggy functions, and watching them fail with the exact
wrong values, is what turned "19 passed" from a nice number into actual evidence. I want
that to be reflexive: *if I can't make it fail, I don't know what it's testing.*

A close second: reproduce before repairing. Every bug here got demonstrated on demand first.
That is also what caught my own wrong explanation of bug 1.

**What I'd do differently: commit as I go.** The project says commit history is graded, and
mine is honest but reconstructed — I did the investigation, the fixes, and the documentation
in one long session and then split the work into three commits at the end. The commits are
real and each one stands on its own, but I was assembling a history rather than recording
one. The practical cost is that I had no checkpoint to roll back to. When the `st.empty()`
fix turned out to break the finished-game path, I was editing forward out of a half-broken
state instead of reverting to a known-good commit. Next time: commit after each bug is
reproduced and each bug is fixed.

**How this changed how I think about AI-generated code.** The failure mode I expected was
code that crashes; the failure mode I got was code that runs perfectly and is quietly wrong
— seven bugs, zero tracebacks, and a `except TypeError` that existed specifically to keep
one of them from surfacing. What I did not expect is that the same thing applies to the AI's
*explanations*: it described bug 1 confidently and incorrectly until I made it run the code,
and its fix for bug 5 broke a path it hadn't looked at. I now treat AI output — code and
reasoning alike — as a fast draft that is only worth what I can independently verify, and
I'd rather have one claim I've reproduced than five I've been told.
