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

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
