import os, json, random, base64, datetime as dt
import pandas as pd
import streamlit as st

# =========================
# DARTS CHALLENGE — 40 ROUNDS (fixed)
# =========================
st.set_page_config(page_title="Darts Challenge", page_icon="🎯", layout="centered")

# ----- Access Code (Cloud + local) -----
try:
    ACCESS_CODE = st.secrets["ACCESS_CODE"]
except Exception:
    ACCESS_CODE = os.getenv("ACCESS_CODE", "FREEPLAY2025")  # fallback

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("🎯 Darts Challenge")
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

# ----- Google Analytics (GA4) -----
GA_MEASUREMENT_ID = None
try:
    GA_MEASUREMENT_ID = st.secrets.get("GA_MEASUREMENT_ID")
except Exception:
    GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID")

if GA_MEASUREMENT_ID:
    st.markdown(
        f"""
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{GA_MEASUREMENT_ID}');
        </script>
        """,
        unsafe_allow_html=True,
    )

# ====== Constants ======
TOTAL_ROUNDS = 40
HUMAN_MAX_PLAYERS = 4
TARGET_CYCLE = {0: 20, 1: 19, 2: 18, 3: "Bullseye"}  # cycles every 4 rounds

# ====== Bot simulation ======
def get_target(round_num: int):
    return TARGET_CYCLE[(round_num - 1) % 4]

def scaled_mean(level: int, min_mean: float, max_mean: float) -> float:
    # linearly scale mean from min_mean (level 1) to max_mean (level 20)
    return min_mean + (level - 1) * (max_mean - min_mean) / 19.0

def simulate_bot_score(level: int, target):
    if target == "Bullseye":
        mean = scaled_mean(level, 2, 16); sd = 2.2; max_score = 18
    else:
        mean = scaled_mean(level, 3, 24); sd = 3.0; max_score = 27
    score = random.gauss(mean, sd)
    return max(0, min(max_score, int(round(score))))

# ====== 80 fictional bot names ======
FICTIONAL_NAMES = [
    "Alfie Johnson","Barry Latham","Cal Doyle","Darren Smales","Eddie Cooper",
    "Frankie Marshall","Gavin Pike","Harry Bolton","Ian Cutler","Jamie Rowntree",
    "Kyle Hargreaves","Lewis Danton","Mason Ridley","Nate Colburn","Owen Tranter",
    "Pete Holloway","Quinn Harker","Ricky Dawes","Sam Pritchard","Toby Wilcox",
    "Vince Archer","Will Keating","Xander Brooke","Yuri Koval","Zack Morton",
    "Shane O'Rourke","Paddy Molloy","Liam Burke","Connor Flynn","Declan Reddin",
    "Aiden McCaffrey","Sean Donnelly","Rory Hanlon","Brendan Kelleher","Noel Tiernan",
    "Gregor Van Drunen","Jan Kromhout","Sjoerd Verbeek","Hugo Schenk","Sven Arvidsson",
    "Karl Drexler","Lukas Steiner","Marek Novak","Tomasz Zielak","Niko Saarinen",
    "Matteo Ruggieri","Alvaro Ceballos","Diego Lamela","Rafael Domingues","Luis Arevalo",
    "Andy Buckfield","Colin Sparks","Mick Daniels","Nicky Pratt","Jason Craddock",
    "Dylan Cartwright","Stuart Kettering","Glen Everly","Martin Browning","Howard Clegg",
    "Ray Kendall","Billy Squires","Tony Mather","Steve Riddick","Terry McBain",
    "Gareth Plummer","Ben Jarrett","Callum Haines","Reece Mallory","Joel Partridge",
    "Ollie Bannister","Spencer Crowe","Morgan Tate","Felix Wainwright","Harvey North",
    "Miles Whitcombe","Ewan Carver","Kieron Ashdown","Leon Sayer","Rhys Penbury",
    "Jasper Longden","Trent Maybury","Wes Crampton","Dale Henshaw","Byron Loxley"
]

# ====== Save/Load (copy/paste codes) ======
def b64_encode(obj: dict) -> str:
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")

def b64_decode(s: str) -> dict:
    raw = base64.urlsafe_b64decode(s.encode("ascii"))
    return json.loads(raw.decode("utf-8"))

# ====== First-time state ======
if "round" not in st.session_state:
    st.session_state.round = 0
    st.session_state.bot_totals = [0] * 80
    st.session_state.bot_level = 10
    st.session_state.bot_names = random.sample(FICTIONAL_NAMES, 80)
    st.session_state.humans = {}  # {name: [scores]}
    st.session_state.highscores = []  # [{Name, Score, Date}]
    st.session_state.last_save_code = ""

# Sidebar: quick reset to player-entry
if st.sidebar.button("🧑‍🤝‍🧑 Change players / New match"):
    st.session_state.humans = {}
    st.session_state.round = 0
    st.rerun()

# ====== Rules ======
with st.expander("📘 Game Rules & How to Play", expanded=False):
    st.markdown(
        """
**Objective**  
Score as many points as possible over **40 rounds**. Highest total wins.

**Rounds & Targets**  
- Targets cycle: **20 → 19 → 18 → Bullseye → repeat**.  
- Enter your **9-dart total** for the shown target.  
  - Max per round: **27** (20/19/18) • **18** (Bullseye).

**Players**  
- Up to **4 human players**.  
- **80 AI opponents** compete alongside you.  
- **Difficulty 1–20** controls bot strength (applies to all bots).

**Leaderboard**  
- Shows the **Top 10** after each round.  
- Always shows each human’s **rank + total**, even if outside Top 10.

**Save / Load (mobile-friendly)**  
- Generate a **Save Code** (text) to copy/paste—no files needed.  
- Paste the code later to **resume** on any device.

**New Match**  
- Use **Change players / New match** in the sidebar to restart the 40-round cycle.
        """
    )

# ====== Save / Load (codes) ======
with st.expander("💾 Save / Load (copy/paste code)"):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Make Save Code"):
            payload = {
                "round": st.session_state.round,
                "bot_totals": st.session_state.bot_totals,
                "bot_level": st.session_state.bot_level,
                "bot_names": st.session_state.bot_names,
                "humans": st.session_state.humans,
                "ts": int(dt.datetime.utcnow().timestamp()),
                "v": 1,
            }
            st.session_state.last_save_code = b64_encode(payload)
        st.text_area("Latest Save Code", st.session_state.last_save_code, height=90)
    with c2:
        code_in = st.text_area("Paste Save Code to Load", height=90, key="code_in")
        if st.button("Load from Code"):
            try:
                data = b64_decode(st.session_state.code_in.strip())
                st.session_state.round = int(data["round"])
                st.session_state.bot_totals = list(map(int, data["bot_totals"]))
                st.session_state.bot_level = int(data["bot_level"])
                st.session_state.bot_names = list(map(str, data["bot_names"]))
                st.session_state.humans = {str(k): [int(x) for x in v] for k, v in data["humans"].items()}
                st.success("Save loaded.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not load: {e}")
    with c3:
        if st.button("🔁 Hard Reset (everything)"):
            st.session_state.clear()
            st.rerun()

# ====== Player setup (fixed 40 rounds) ======
if not st.session_state.humans:
    st.subheader("👥 Add Human Players (up to 4)")
    names = [st.text_input(f"Player {i+1} name", key=f"name_{i}") for i in range(HUMAN_MAX_PLAYERS)]
    st.session_state.bot_level = st.selectbox("Bot Difficulty (1–20)", list(range(1,21)), index=st.session_state.bot_level-1)
    if st.button("Start 40-Round Game", type="primary"):
        humans = {n.strip(): [] for n in names if n and n.strip()}
        if not humans:
            st.error("Please enter at least one player name.")
        else:
            st.session_state.humans = humans
            st.session_state.round = 1
            st.rerun()
    st.stop()

# ====== Difficulty (fixed during match, visible) ======
st.write(f"**Bot difficulty (1–20):** {st.session_state.bot_level}")

# ====== Current round ======
round_num = st.session_state.round
target = get_target(round_num)
st.header(f"Round {round_num} / {TOTAL_ROUNDS} — Target: **{target}**")

# Helper hint band
if target == "Bullseye":
    hint = scaled_mean(st.session_state.bot_level, 2, 16)
    st.caption(f"Guide: typical total ≈ **{int(round(hint))}** (range 0–18).")
else:
    hint = scaled_mean(st.session_state.bot_level, 3, 24)
    st.caption(f"Guide: typical total ≈ **{int(round(hint))}** (range 0–27).")

# Inputs for all humans
inputs = {}
cols = st.columns(min(len(st.session_state.humans), 4) or 1)
for idx, name in enumerate(st.session_state.humans.keys()):
    with cols[idx % len(cols)]:
        inputs[name] = st.number_input(
            f"{name}'s score (9 darts)",
            min_value=0,
            max_value=18 if target == "Bullseye" else 27,
            step=1,
            key=f"score_{name}_{round_num}"
        )

if st.button("Submit Round"):
    # store human scores
    for name, score in inputs.items():
        st.session_state.humans[name].append(int(score))
    # simulate bots
    for i in range(80):
        st.session_state.bot_totals[i] += simulate_bot_score(st.session_state.bot_level, target)
    # advance
    st.session_state.round += 1
    st.rerun()

# ====== Leaderboard: Top 10 + each human’s rank ======
def build_leaderboard():
    rows = []
    # bots
    for name, lvl, score in zip(st.session_state.bot_names,
                                [st.session_state.bot_level]*len(st.session_state.bot_names),
                                st.session_state.bot_totals):
        rows.append({"Player": f"{name} (L{lvl})", "Score": int(score), "Type": "Bot"})
    # humans
    for name, scores in st.session_state.humans.items():
        rows.append({"Player": f"{name} (Human)", "Score": int(sum(scores)), "Type": "Human"})
    df = pd.DataFrame(rows)
    if df.empty: 
        return df, {}
    # HIGHER score is better
    df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df)+1))
    # map human ranks
    human_ranks = {}
    for name, scores in st.session_state.humans.items():
        label = f"{name} (Human)"
        pos = df.index[df["Player"]==label]
        if len(pos):
            rank = int(df.loc[pos[0], "Rank"])
            total = int(df.loc[pos[0], "Score"])
            human_ranks[name] = (rank, total, len(df))
    return df, human_ranks

if st.session_state.round >= 1:
    df, human_ranks = build_leaderboard()
    if not df.empty:
        st.subheader("📊 Leaderboard — Top 10")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
        # Humans’ positions always visible
        for name, (rank, total, field) in human_ranks.items():
            st.write(f"**{name}** — Total: {total}, Rank: **{rank}/{field}**")

# ====== End of Game (after round 40) ======
if st.session_state.round > TOTAL_ROUNDS:
    st.success("🎉 Game Over! Thanks for playing.")
    # Build final and save highscores
    df, human_ranks = build_leaderboard()
    # save each human’s final total into highscores (Top 10 by highest total)
    for name, (rank, total, field) in human_ranks.items():
        st.session_state.highscores.append({"Name": name, "Score": int(total), "Date": str(dt.date.today())})
    st.session_state.highscores = sorted(st.session_state.highscores, key=lambda x: x["Score"], reverse=True)[:10]
    st.balloons()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎮 Play Again (same players)"):
            # reset state for a new 40-round match
            st.session_state.round = 1
            st.session_state.bot_totals = [0] * 80
            for k in list(st.session_state.humans.keys()):
                st.session_state.humans[k] = []
            st.rerun()
    with c2:
        if st.button("🧹 Reset Everything"):
            st.session_state.clear()
            st.rerun()

# ====== High Scores (Top 10 across finished games this session) ======
st.subheader("🏅 Top 10 High Scores (this session)")
if st.session_state.highscores:
    hs_df = pd.DataFrame(st.session_state.highscores)
    hs_df = hs_df.sort_values("Score", ascending=False)
    st.table(hs_df)
else:
    st.caption("No finished games yet — complete a 40-round match to record results.")

st.caption("Made by @pauldartbrain • questforqschool.com")









