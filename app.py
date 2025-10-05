import os, json, time, random, datetime as dt
import pandas as pd
import streamlit as st

# =============== Page & Access =================
st.set_page_config(page_title="Darts Challenge", page_icon="🎯", layout="centered")

# Access code that works locally & on Streamlit Cloud
try:
    ACCESS_CODE = st.secrets["ACCESS_CODE"]
except Exception:
    ACCESS_CODE = os.getenv("ACCESS_CODE", "FREEPLAY2025")

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🎯 Welcome to Darts Challenge")
    st.caption("Enter the access code to play.")
    code = st.text_input("Access Code", type="password")
    if st.button("Enter"):
        if code.strip() == ACCESS_CODE:
            st.session_state.authed = True
            st.success("✅ Access granted!")
            st.rerun()
        else:
            st.error("❌ Invalid code. Try again.")
    st.stop()

# =============== Helpers =================
MAX_ROUNDS = 10
TARGETS = ["Single 20", "Single 19", "Double 16", "Double 20", "Treble 19", "Treble 18", "Bullseye"]

def simulate_bot_shots(level: int) -> int:
    """
    Simulate number of darts for a bot: lower is better.
    Level 1–20 (20 = strongest).
    """
    # Base around 3, adjust by level; add variability
    bias = max(0.8, 3.6 - (level * 0.12))   # ~3.6 at L1 -> ~1.2 at L20
    score = random.gauss(mu=bias, sigma=0.6)
    score = max(1, min(9, round(score)))
    return score

def leaderboard_df(scores_dict):
    rows = []
    for name, data in scores_dict.items():
        rows.append({"Player": name, "Total Darts": sum(data["history"]), "Rounds": len(data["history"])})
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Total Darts", "Rounds", "Player"], ascending=[True, False, True]).reset_index(drop=True)
        df.insert(0, "Rank", range(1, len(df)+1))
    return df

def reset_game(players, bot_count, bot_level):
    st.session_state.round_num = 1
    st.session_state.target = random.choice(TARGETS)
    st.session_state.scores = {p: {"history": []} for p in players}

    # Add bots if requested
    for i in range(bot_count):
        st.session_state.scores[f"Bot {i+1} (L{bot_level})"] = {"history": []}

    st.session_state.running = True
    st.session_state.highscores = st.session_state.get("highscores", [])
    st.session_state.last_saved_banner = time.time()

# =============== Sidebar Setup =================
st.sidebar.header("🛠 Setup")
st.sidebar.caption("Add players & options, then press **Start Game**.")

# Players (up to 4)
player_defaults = st.session_state.get("player_defaults", ["You", "", "", ""])
p1 = st.sidebar.text_input("Player 1", value=player_defaults[0])
p2 = st.sidebar.text_input("Player 2", value=player_defaults[1])
p3 = st.sidebar.text_input("Player 3", value=player_defaults[2])
p4 = st.sidebar.text_input("Player 4", value=player_defaults[3])

players = [p.strip() for p in [p1, p2, p3, p4] if p.strip()]

st.sidebar.markdown("---")
bot_count = st.sidebar.slider("Add AI opponents (bots)", 0, 3, 1)
bot_level = st.sidebar.slider("Bot difficulty", 1, 20, 12, help="1 = beginner, 20 = pro")

st.sidebar.markdown("---")
max_rounds = st.sidebar.slider("Rounds", 5, 30, MAX_ROUNDS)
st.sidebar.caption("Tip: You can change bot difficulty here any time before starting.")

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Start Game", type="primary", use_container_width=True):
        if not players:
            st.sidebar.error("Add at least one human player.")
        else:
            st.session_state.player_defaults = [p1, p2, p3, p4]
            reset_game(players, bot_count, bot_level)
            st.rerun()
with c2:
    if st.button("Reset All", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# =============== Main UI =================
st.title("🎯 Darts Challenge")

# Rules
with st.expander("📘 Game Rules"):
    st.markdown("""
- Up to **4 human players** + optional **AI opponents**.
- Each round shows a target (Single, Double, Treble, Bullseye).
- Enter **darts used** for each human each round. Bots are auto-scored.
- Fewer darts is better. **Lowest total** wins.
- **Leaderboard** updates live. **Top 10** results are kept across plays (this session).
    """)

# Restore defaults if first load
if "running" not in st.session_state:
    st.info("Add players on the left and press **Start Game**.")
    st.stop()

# Live header
st.subheader(f"🏁 Round {st.session_state.round_num} / {max_rounds} — Target: **{st.session_state.target}**")

# Inputs for human players
human_names = [n for n in st.session_state.scores.keys() if not n.startswith("Bot")]
bot_names   = [n for n in st.session_state.scores.keys() if n.startswith("Bot")]

cols = st.columns(min(4, len(st.session_state.scores)))
for idx, name in enumerate(human_names):
    with cols[idx % len(cols)]:
        default_val = 3
        shot = st.number_input(f"{name} — darts used", 1, 9, default_val, key=f"shot_{name}_{st.session_state.round_num}")
        if st.button(f"Save {name}", key=f"save_{name}_{st.session_state.round_num}"):
            st.session_state.scores[name]["history"].append(int(shot))
            st.success(f"Saved: {name} = {shot} darts")

# Bots auto-play (once per round)
if st.button("✅ Lock Round & Auto-play Bots"):
    # Fill any missing human entries with default 3
    for name in human_names:
        if len(st.session_state.scores[name]["history"]) < st.session_state.round_num:
            st.session_state.scores[name]["history"].append(3)

    # Score bots
    for bname in bot_names:
        # Extract level from name if present
        try:
            lvl = int(bname.split("(L")[1].split(")")[0])
        except:
            lvl = bot_level
        st.session_state.scores[bname]["history"].append(simulate_bot_shots(lvl))

    # Advance round or finish
    st.session_state.round_num += 1
    if st.session_state.round_num > max_rounds:
        st.session_state.running = False
    else:
        st.session_state.target = random.choice(TARGETS)
    st.rerun()

# Live leaderboard
st.subheader("📊 Live Leaderboard")
live_df = leaderboard_df(st.session_state.scores)
if not live_df.empty:
    st.dataframe(live_df, hide_index=True, use_container_width=True)
else:
    st.caption("No scores yet.")

# End of game: show final + save highscores
if not st.session_state.running:
    st.success("🏁 Game Finished — Final Results")
    final_df = leaderboard_df(st.session_state.scores)
    st.dataframe(final_df, hide_index=True, use_container_width=True)

    # Save highscores (Top 10 by best total)
    results = [{"Name": r["Player"], "Score": int(r["Total Darts"]), "Date": str(dt.date.today())}
               for _, r in final_df.iterrows()]
    # Merge into session highscores
    highs = st.session_state.get("highscores", [])
    highs.extend(results)
    highs = sorted(highs, key=lambda x: x["Score"])[:10]
    st.session_state.highscores = highs

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎮 Play Again"):
            # reset with same players & bots
            reset_game(players=human_names, bot_count=len(bot_names), bot_level=bot_level)
            st.rerun()
    with c2:
        if st.button("🧹 Clear Highscores"):
            st.session_state.highscores = []
            st.success("Highscores cleared (this session).")
            st.rerun()

# Highscores box (always visible)
st.subheader("🏅 Top 10 All-Time (this session)")
hs = st.session_state.get("highscores", [])
if hs:
    st.table(pd.DataFrame(hs))
else:
    st.caption("No highscores yet — finish a game to record results.")

st.caption("Made by @pauldartbrain — questforqschool.com")





