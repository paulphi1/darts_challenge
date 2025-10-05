import os
import json
import random
import base64
import datetime as dt
import pandas as pd
import streamlit as st

# ====== App config ======
st.set_page_config(page_title="🎯 Darts Challenge", layout="centered")

# ====== Access code gate ======
try:
    ACCESS_CODE = st.secrets["ACCESS_CODE"]          # works on Streamlit Cloud
except Exception:
    ACCESS_CODE = os.getenv("ACCESS_CODE", "FREEPLAY2025")  # local fallback

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🎯 Welcome to Darts Challenge")
    st.write("Enter your unique access code below to play.")
    code = st.text_input("Access Code", type="password")
    if st.button("Enter"):
        if code.strip() == ACCESS_CODE:
            st.session_state.authed = True
            st.success("✅ Access granted. Welcome!")
            st.rerun()
        else:
            st.error("❌ Invalid access code.")
    st.stop()

# ====== Game State ======
if "scores" not in st.session_state:
    st.session_state.scores = []
if "players" not in st.session_state:
    st.session_state.players = ["Paul Philpot"]
if "highscores" not in st.session_state:
    st.session_state.highscores = []

# ====== Game Rules ======
with st.expander("📜 Game Rules"):
    st.markdown("""
    - Up to **4 human players** can play per session.  
    - Each round gives a random darts challenge target (single, double, treble, bullseye).  
    - Players enter the number of darts needed to hit the target.  
    - Fewer darts = better performance.  
    - The lowest cumulative score wins.  
    - After finishing a session, your best result is stored automatically in the **Top 10 Leaderboard**.
    """)

# ====== Add Players ======
st.header("👥 Add Human Players (up to 4)")
col1, col2 = st.columns(2)
with col1:
    for i in range(4):
        pname = st.text_input(f"Player {i+1} name", value=st.session_state.players[i] if i < len(st.session_state.players) else "")
        if pname and (i >= len(st.session_state.players)):
            st.session_state.players.append(pname)

# ====== Start Game ======
if st.button("Start Game"):
    st.session_state.scores = [
        {"name": p, "score": 0, "round": 1, "history": []}
        for p in st.session_state.players if p.strip()
    ]
    st.session_state.current_round = 1
    st.session_state.round_active = True
    st.rerun()

# ====== Play Rounds ======
if st.session_state.get("round_active", False):
    st.subheader(f"🎯 Round {st.session_state.current_round}")
    par = random.choice(["Single 20", "Double 16", "Treble 19", "Bullseye"])
    st.write(f"**Target:** {par}")

    for p in st.session_state.scores:
        darts = st.number_input(f"{p['name']} – darts used", 1, 9, 3, key=f"darts_{p['name']}")
        p["history"].append(darts)
        p["score"] += darts

    if st.button("Next Round"):
        st.session_state.current_round += 1
        if st.session_state.current_round > 10:
            st.session_state.round_active = False
        st.rerun()

# ====== End of Game ======
if not st.session_state.get("round_active", True) and st.session_state.get("scores"):
    st.success("🏁 Game Over!")
    df = pd.DataFrame(
        [{"Name": p["name"], "Total Darts": p["score"]} for p in st.session_state.scores]
    ).sort_values("Total Darts")
    st.dataframe(df, hide_index=True)

    # --- Save to highscores ---
    for _, row in df.iterrows():
        st.session_state.highscores.append({"Name": row["Name"], "Score": int(row["Total Darts"]), "Date": str(dt.date.today())})

    # Keep Top 10
    st.session_state.highscores = sorted(st.session_state.highscores, key=lambda x: x["Score"])[:10]
    st.session_state.scores = []  # clear current session

    st.balloons()
    st.write("Your score has been saved to the Top 10 Leaderboard!")

# ====== High-Scores Leaderboard ======
st.subheader("🏆 Top 10 High Scores")
if st.session_state.highscores:
    hs_df = pd.DataFrame(st.session_state.highscores)
    st.dataframe(hs_df, hide_index=True)
else:
    st.caption("No scores yet — play your first game!")

# ====== Save / Reset buttons ======
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 Save Data (local session)"):
        st.success("Scores saved for this browser session.")
with c2:
    if st.button("♻️ Reset All Data"):
        for k in ["scores", "players", "highscores", "round_active"]:
            st.session_state.pop(k, None)
        st.success("All data reset.")
        st.rerun()

st.caption("Access code can be updated anytime in your Streamlit Secrets.  Default: FREEPLAY2025")



