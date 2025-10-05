import os, io, json, time, random, sys, traceback
import pandas as pd
import streamlit as st

# ==============================================================
# 🎯 DARTS CHALLENGE — Streamlit Version
# Supports local + Streamlit Cloud with secure Access Code
# ==============================================================

# ---------- Access Code (works both locally & in cloud) ----------
try:
    ACCESS_CODE = st.secrets["ACCESS_CODE"]
except Exception:
    ACCESS_CODE = os.getenv("ACCESS_CODE", "FREEPLAY2025")  # fallback for local dev

# ---------- Page Setup ----------
st.set_page_config(page_title="Darts Challenge", page_icon="🎯", layout="centered")

# ---------- Access Gate ----------
if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🎯 Welcome to Darts Challenge")
    st.caption("Enter your unique access code below to play.")
    code = st.text_input("Access Code", type="password")
    if st.button("Enter"):
        if code.strip() == ACCESS_CODE:
            st.session_state.authed = True
            st.success("✅ Access granted. Welcome!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid access code. Please try again.")
    st.stop()

# ==============================================================
# MAIN GAME SECTION
# ==============================================================

st.title("🎯 Darts Challenge")

# ---------- Rules Popup ----------
with st.expander("📘 Game Rules (click to expand)"):
    st.markdown("""
    **How to Play:**
    - Up to **4 human players** can join each game.
    - Each round has a random target (Single, Double, Treble, Bullseye).
    - The goal is to hit the target in as few darts as possible.
    - Each player's score adds up across 30 rounds.
    - After each game, the top scores are stored automatically.

    **Scoring Summary:**
    - Fewer darts = better score.
    - Lowest total wins.

    **Pro Tip:** Practice often — consistency pays off 🎯
    """)

# ---------- High Scores ----------
HIGHSCORE_FILE = "highscores.json"

def load_highscores():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            return json.load(open(HIGHSCORE_FILE, "r", encoding="utf-8"))
        except:
            return []
    return []

def save_highscores(data):
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

highscores = load_highscores()

# ---------- Player Setup ----------
st.header("👥 Add Human Players (up to 4)")
col1, col2, col3, col4 = st.columns(4)
players = []
for i, c in enumerate([col1, col2, col3, col4], start=1):
    name = c.text_input(f"Player {i} name", value=f"Player {i}" if i == 1 else "")
    if name.strip():
        players.append(name.strip())

if len(players) == 0:
    st.warning("Please enter at least one player name.")
    st.stop()

# ---------- Start Game ----------
if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.round_num = 0
    st.session_state.scores = {p: [] for p in players}

if st.button("Start Game"):
    st.session_state.game_started = True
    st.session_state.round_num = 1
    st.session_state.scores = {p: [] for p in players}
    st.success("🎯 Game started! Good luck.")
    st.experimental_rerun()

# ---------- Game Logic ----------
if st.session_state.game_started:
    st.header(f"🏁 Round {st.session_state.round_num}/30")

    # Random target type
    target_type = random.choice(["Single", "Double", "Treble", "Bullseye"])
    st.subheader(f"🎯 Target: {target_type}")

    for player in players:
        hits = st.number_input(f"{player} - Darts used:", 1, 9, 3, key=f"{player}_{st.session_state.round_num}")

        # Store result
        if st.button(f"✅ Submit for {player}", key=f"submit_{player}_{st.session_state.round_num}"):
            st.session_state.scores[player].append(hits)
            st.success(f"Saved score for {player} — {hits} darts")

    # Advance round
    if st.button("➡️ Next Round"):
        st.session_state.round_num += 1
        if st.session_state.round_num > 30:
            st.session_state.game_started = False
            st.success("🏁 Game complete! Showing results...")
            st.experimental_rerun()
        else:
            st.experimental_rerun()

# ---------- Results ----------
if not st.session_state.game_started and st.session_state.round_num > 0:
    st.header("🏆 Final Results")

    results = []
    for p in players:
        total = sum(st.session_state.scores[p])
        results.append((p, total))
    results.sort(key=lambda x: x[1])

    df = pd.DataFrame(results, columns=["Player", "Total Darts"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Save highscores
    for name, total in results:
        highscores.append({"Name": name, "Score": total, "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
    highscores = sorted(highscores, key=lambda x: x["Score"])[:10]
    save_highscores(highscores)

    st.subheader("🏅 Top 10 All-Time Scores")
    st.table(pd.DataFrame(highscores)[:10])

    if st.button("🔄 Reset Game"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

    if st.button("🗑 Reset All Data (Clear High Scores)"):
        if os.path.exists(HIGHSCORE_FILE):
            os.remove(HIGHSCORE_FILE)
        st.success("All data cleared.")
        st.experimental_rerun()

st.caption("Darts Challenge © 2025 | FreePlay Edition | Made with ❤️ by Paul Philpot")


