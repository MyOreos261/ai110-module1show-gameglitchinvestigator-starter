import random

import streamlit as st

from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

# FIX (bug 2, hints inverted): the two messages below were swapped -- a guess
# that was too high told the player to go HIGHER. Found by playing with the
# debug panel open; AI confirmed the labels were right and only the wording
# was crossed. Wording is a UI concern, so it stays here, not in logic_utils.
HINTS = {
    "Win": "🎉 Correct!",
    "Too High": "📉 Go LOWER!",
    "Too Low": "📈 Go HIGHER!",
}

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")


# FIX (bugs 3, 4, 7): New Game used to reset only `attempts` and `secret`,
# leaving `status` on "won" so the app locked the player out forever. Extracting
# one reset function was the AI's suggestion; I took it because it makes a
# half-reset impossible by construction rather than by remembering to do it.
def reset_game():
    """Start a fresh round for the CURRENT difficulty.

    One function owns every piece of game state, so no caller can reset
    half of it -- which is what broke the New Game button.
    """
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []


# FIX (bug 7, stale secret across difficulties): the old `if "secret" not in
# st.session_state` guard ran once ever, so switching to Easy relabelled the
# range but kept a secret of 63 in a 1-20 game. Reproduced live before fixing.
if st.session_state.get("difficulty") != difficulty:
    reset_game()

st.subheader("Make a guess")

# FIX (bug 5, one-rerun-stale display): these used to be drawn here, above the
# buttons, so they showed the state from BEFORE the click. Reserve the spot now,
# paint at the end. The AI first proposed st.empty(); I changed it to
# st.container() because st.empty() rebuilt the expander and snapped it shut
# every rerun -- only visible by clicking through the app, not by reading it.
info_slot = st.container()
debug_slot = st.container()


def paint_status():
    """Fill the reserved slots with the CURRENT state. Called on every exit path."""
    info_slot.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {max(0, attempt_limit - st.session_state.attempts)}"
    )
    with debug_slot.expander("Developer Debug Info"):
        st.write("Secret:", st.session_state.secret)
        st.write("Attempts:", st.session_state.attempts)
        st.write("Score:", st.session_state.score)
        st.write("Difficulty:", difficulty)
        st.write("History:", st.session_state.history)


raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    reset_game()
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    paint_status()
    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        # FIX (bug 1, the state bug): an `if attempts % 2 == 0` branch used to
        # cast the secret to str here, making comparisons alphabetical ("9" >
        # "50"). The secret never changed value -- only its type.
        outcome = check_guess(guess_int, st.session_state.secret)
        message = HINTS[outcome]

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

paint_status()

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
