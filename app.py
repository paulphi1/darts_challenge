import os, json, random, base64, datetime as dt
import pandas as pd
import streamlit as st

# ===== App config =====
st.set_page_config(page_title="Darts Challenge", layout="centered")

# ===== Passcode gate (override with env var on hosts) =====
PASSCODE = os.getenv("PASSCODE", "TEST123")
if "authed" not in st.session_state:
    st.session_state.authed = False
if not st.session_state.authed:
    st.title("🔑 Access Required")
    pw = st.text_input("Passcode", type="password")
    if st.button("Unlock"):
        if pw.strip() == PASSCODE:
            st.session_state.authed = True
            st.toast("Access granted — have fun!", icon="✅")
            st.rerun()
        else:
            st.error("Invalid passcode.")
    st.stop()

# ===== Title row with Rules button =====
c_title, c_rules = st.columns([1, 0.38])
with c_title:
    st.title("🎯 Darts Challenge: 40-Round Showdown")
with c_rules:
    if "show_rules" not in st.session_state:
        st.session_state.show_rules = False
    if st.button("📖 How to Play / Rules"):
        st.session_state.show_rules = not st.session_state.show_rules

# ===== Rules panel =====
if st.session_state.show_rules:
    with st.expander("📖 Game Rules & Tips", expanded=True):
        st.markdown(
            """
**Objective**  
Score as many points as possible over **40 rounds**. Highest total wins.

**Rounds & Targets**  
- Targets cycle every round: **20 → 19 → 18 → Bullseye → repeat**.  
- Each human player enters their **9-dart total** for the shown target.  
  - Max per round: **27** (20/19/18), **18** (Bullseye).

**Players**  
- Up to **4 human players** can play in the same match.  
- **80 simulated opponents** (bots) compete alongside you.  
- Bot skill is set by **Difficulty** (1=Beginner, 20=Pro).

**Entering Scores**  
1) For each round, enter all humans’ 9-dart totals.  
2) Click **Submit Round** (bots are simulated automatically).  

**Leaderboard**  
- Shows the top 10 by total score.  
- Individual human ranks also display under the table.

**Save / Load (mobile-friendly)**  
- At game end we auto-generate a **Save Code** you can **copy/paste** (no files).  
- You can also make a Save Code at any time in **Save / Load**.  
- Paste a code to **Load** later on any device.

**High Scores**  
- We keep a **Top 10 (per player name)** based on your finished games this session.  
- Use **Export High Scores** to copy them as a code; **Import** to restore later.

**New Match / Change Players**  
- Use **🧑‍🤝‍🧑 Change players / New match** in the sidebar to return to player entry.

**Game End**  
- The game ends after **40 rounds**. 🎉

**Fair Play**  
- Enter honest totals for the displayed target to keep it fun!
            """
        )

# ===== Helpers =====
def get_target(round_num: int):
    """Cycle 20 → 19 → 18 → Bullseye, then repeat."""
    return {0: 20, 1: 19, 2: 18, 3: "Bullseye"}[(round_num - 1) % 4]

def scaled_mean(level: int, min_mean: float, max_mean: float) -> float:
    return min_mean + (level - 1) * (max_mean - min_mean) / 19.0

def simulate_bot_score(level: int, target):
    if target == "Bullseye":
        mean = scaled_mean(level, 2, 16); sd = 2.2; max_score = 18
    else:
        mean = scaled_mean(level, 3, 24); sd = 3.0; max_score = 27
    score = random.gauss(mean, sd)
    return max(0, min(max_score, int(round(score))))

def b64_encode(obj: dict) -> str:
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")

def b64_decode(s: str) -> dict:
    raw = base64.urlsafe_b64decode(s.encode("ascii"))
    return json.loads(raw.decode("utf-8"))

# ===== Fictional darts-style names (80) =====
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

# ===== First-time state =====
if "round" not in st.session_state:
    st.session_state.round = 0
    st.session_state.bot_scores = [0] * 80
    st.session_state.bot_levels = []
    st.session_state.bot_names = random.sample(FICTIONAL_NAMES, 80)
    st.session_state.humans = {}  # {name: [scores]}
    st.session_state.user_level = 10
    # "Persistent" (per session) high scores and last save code
    st.session_state.highscores = {}  # {player_name: best_total}
    st.session_state.last_save_code = ""

# Sidebar quick reset
if st.sidebar.button("🧑‍🤝‍🧑 Change players / New match"):
    st.session_state.humans = {}
    st.session_state.round = 0
    st.rerun()

# ===== Save / Load (file-free, mobile-friendly “codes”) =====
def build_save_payload():
    return {
        "round": st.session_state.round,
        "bot_scores": st.session_state.bot_scores,
        "bot_levels": st.session_state.bot_levels,
        "bot_names": st.session_state.bot_names,
        "user_level": st.session_state.user_level,
        "humans": st.session_state.humans,
        "ts": int(dt.datetime.utcnow().timestamp()),
        "v": 1,
    }

def apply_save_payload(payload: dict):
    need = ["round","bot_scores","bot_levels","bot_names","user_level","humans"]
    for k in need:
        if k not in payload: raise ValueError(f"Save code missing: {k}")
    st.session_state.round = int(payload["round"])
    st.session_state.bot_scores = list(map(int, payload["bot_scores"]))
    st.session_state.bot_levels = list(map(int, payload["bot_levels"]))
    st.session_state.bot_names = list(map(str, payload["bot_names"]))
    st.session_state.user_level = int(payload["user_level"])
    # humans: {name: [scores]}
    humans = {}
    for n, scores in payload["humans"].items():
        humans[str(n)] = [int(s) for s in scores]
    st.session_state.humans = humans

with st.expander("💾 Save / Load (Mobile-friendly codes)"):
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Make Save Code now"):
            code = b64_encode(build_save_payload())
            st.session_state.last_save_code = code
            st.success("Save Code created below. Copy it to Notes/Chat/etc.")
        if st.session_state.last_save_code:
            st.text_area("Your latest Save Code", st.session_state.last_save_code, height=80)
    with c2:
        code_in = st.text_area("Paste a Save Code to Load", height=80, key="code_in")
        if st.button("Load from Code"):
            try:
                payload = b64_decode(st.session_state.code_in.strip())
                apply_save_payload(payload)
                st.success("Loaded. Resuming…")
                st.rerun()
            except Exception as e:
                st.error(f"Could not load code: {e}")
    with c3:
        if st.button("🔁 Hard Reset (all state)"):
            st.session_state.clear()
            st.rerun()

# ===== Player setup (1–4 humans) =====
if not st.session_state.humans:
    st.subheader("👥 Add Human Players (up to 4)")
    names = [st.text_input(f"Player {i+1} name", key=f"name_{i}") for i in range(4)]
    if st.button("Start Game"):
        humans = {n.strip(): [] for n in names if n.strip()}
        if not humans:
            st.error("Please enter at least one player name.")
        else:
            st.session_state.humans = humans
            st.session_state.round = 1
            st.rerun()
    st.stop()

# ===== Level selection (applies to all bots) =====
st.session_state.user_level = st.selectbox(
    "Choose difficulty (bots) — 1=Beginner, 20=Pro",
    list(range(1,21)), index=st.session_state.user_level-1
)
st.session_state.bot_levels = [st.session_state.user_level] * 80  # keep bots aligned to chosen difficulty

# ===== Round UI =====
round_num = st.session_state.round
target = get_target(round_num)
st.header(f"Round {round_num} — Target: {target}")

# hint band
if target == "Bullseye":
    hint_mean = scaled_mean(st.session_state.user_level, 2, 16)
    st.caption(f"Guide: typical total ≈ **{int(round(hint_mean))}** (range 0–18).")
else:
    hint_mean = scaled_mean(st.session_state.user_level, 3, 24)
    st.caption(f"Guide: typical total ≈ **{int(round(hint_mean))}** (range 0–27).")

# inputs for all humans
inputs = {}
for name in st.session_state.humans:
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
        st.session_state.bot_scores[i] += simulate_bot_score(
            st.session_state.bot_levels[i], target
        )
    st.session_state.round += 1
    st.rerun()

# ===== Leaderboard =====
if st.session_state.round > 1:
    human_totals = {n: sum(scores) for n, scores in st.session_state.humans.items()}
    all_rows = []
    # bots
    for name, lvl, score in zip(st.session_state.bot_names, st.session_state.bot_levels, st.session_state.bot_scores):
        all_rows.append({"Player": f"{name} (L{lvl})", "Score": score})
    # humans
    for name, score in human_totals.items():
        all_rows.append({"Player": f"{name} (Human)", "Score": score})
    df = pd.DataFrame(all_rows).sort_values("Score", ascending=False).reset_index(drop=True)
    st.subheader("📊 Leaderboard (Top 10)")
    st.dataframe(df.head(10), use_container_width=True)
    # show ranks for humans
    scores_sorted = sorted([r["Score"] for r in all_rows], reverse=True)
    for name, score in human_totals.items():
        rank = scores_sorted.index(score) + 1
        st.write(f"**{name}** — Total: {score}, Rank: {rank}/{len(all_rows)}")

# ===== End of game: auto-save + update High Scores =====
def update_highscores_from_totals(human_totals: dict):
    # st.session_state.highscores: {name: best_total}
    hs = st.session_state.get("highscores", {})
    for n, total in human_totals.items():
        prev = hs.get(n, 0)
        if total > prev:
            hs[n] = total
    st.session_state.highscores = hs

def maybe_auto_save_summary(human_totals: dict):
    # Make a compact code of the finished game (so players can keep it)
    payload = build_save_payload()
    payload["round"] = 41  # mark finished
    payload["summary"] = {"humans": human_totals, "ended": int(dt.datetime.utcnow().timestamp())}
    code = b64_encode(payload)
    st.session_state.last_save_code = code

if st.session_state.round > 40:
    st.success("🎉 Game Over! Thanks for playing.")
    # Compute totals and update highscores once per end-state
    totals = {n: sum(scores) for n, scores in st.session_state.humans.items()}
    update_highscores_from_totals(totals)
    maybe_auto_save_summary(totals)
    st.info("Auto-saved a **Save Code** below in the *Save / Load* section.")
    st.balloons()

# ===== High Scores (per session, exportable/importable via code) =====
st.subheader("🏆 Top 10 High Scores (this device/session)")
hs_dict = st.session_state.get("highscores", {})
if hs_dict:
    hs_df = pd.DataFrame(
        sorted(hs_dict.items(), key=lambda kv: kv[1], reverse=True),
        columns=["Player", "Best Total"]
    ).head(10)
    st.dataframe(hs_df, use_container_width=True, hide_index=True)
else:
    st.caption("No finished games yet — play a match to populate your high scores.")

with st.expander("High Scores — Export / Import / Reset"):
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Export High Scores"):
            code = b64_encode({"v": 1, "highscores": st.session_state.get("highscores", {}), "ts": int(dt.datetime.utcnow().timestamp())})
            st.text_area("Copy this High Scores Code", code, height=80)
    with c2:
        hs_in = st.text_area("Paste High Scores Code to Import", height=80, key="hs_code_in")
        if st.button("Import High Scores"):
            try:
                payload = b64_decode(st.session_state.hs_code_in.strip())
                if "highscores" not in payload:
                    raise ValueError("No highscores in code.")
                hs = payload["highscores"]
                # keep max per name
                cur = st.session_state.get("highscores", {})
                for k, v in hs.items():
                    cur[k] = max(int(v), int(cur.get(k, 0)))
                st.session_state.highscores = cur
                st.success("High scores imported.")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
    with c3:
        if st.button("Reset ALL data (match + highscores)"):
            st.session_state.clear()
            st.rerun()


