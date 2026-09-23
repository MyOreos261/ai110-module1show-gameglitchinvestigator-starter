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

The game's purpose — what it is, the three difficulty ranges and attempt limits, and why the debug panel exists (it's what makes the game usable as a debugging exercise).

Bugs I found — a 7-row table pairing the symptom a player sees with the root cause in the code, plus severity. It ends with the point that the brief's claim ("the secret changes every Submit") is wrong — the value is stable, the type flips. That's a genuinely strong thing to have in a writeup: you read the code instead of trusting the bug report.

Fixes I applied — grouped by fix rather than by bug, since several bugs shared one fix. Includes the reasoning that mattered: deleting the TypeError fallback because it was hiding Bug 1, and consolidating state resets so a half-reset becomes impossible by construction.

It closes with the parse_guess out-of-range issue as a deliberate non-fix, flagged rather than silently widened.

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

 **Start the app** with `python -m streamlit run app.py`. The sidebar shows Difficulty
   "Normal", "Range: 1 to 100", and "Attempts allowed: 8". The main panel agrees:
   "Guess a number between 1 and 100. Attempts left: 8". Before the fix, this read
   "Attempts left: 7" on a fresh load, because the counter started at 1 instead of 0.

2. **Expand "Developer Debug Info"** to peek at the secret. In my run, it showed
   `Secret: 7`, `Attempts: 0`, `Score: 0`, `History: []`. The secret is drawn from the
   difficulty's range, so it is always reachable.

3. **Guess 50 and click "Submit Guess".** The hint reads **"📉 Go LOWER!"** — the correct
   direction, since 50 is above 7. Before the fix, this said "Go HIGHER!" for a guess that
   was already too high. The debug panel updates on *this* click, not the next one:
   `Attempts: 1`, `Score: -5`, `History: [50]`, and "Attempts left: 7".

4. **Follow the hint and guess 7.** The app shows "🎉 Correct!", fires the balloons, and
   reports **"You won! The secret was 7. Final score: 85"** — that is 90 points for winning
   on attempt 2, minus 5 for the one wrong guess. Wrong guesses now always cost 5 points;
   previously a too-high guess on an even-numbered attempt *added* 5.

5. **Click "New Game".** The round resets completely: a fresh secret, `Attempts: 0`,
   `Score: 0`, `History: []`, and the guess box is live again. Before the fix, this button
   left the game's status on "won", so the app answered every later click with
   "You already won. Start a new game to play again." — permanently unplayable until reload.

6. **Switch Difficulty to "Easy".** The sidebar changes to "Range: 1 to 20" and
   "Attempts allowed: 6", *and a new secret inside 1–20 is generated*. Before the fix, the
   labels changed, but the old secret survived, so Easy could hide a secret of 63 in a
   1–20 game — impossible to win.

7. **Run the tests** with `pytest tests/`. All three pass against `logic_utils.py`, which
   imports no Streamlit at all — the game logic can be tested without launching the app."""
   
**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
Shell cwd was reset to C:\Users\Ariana\Downloads\AI110\ai110-tinker-studysync-starter
```

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
