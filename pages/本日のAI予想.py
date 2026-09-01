from pathlib import Path
import json

import requests
import streamlit as st

from site_navigation import render_site_navigation


st.set_page_config(page_title="本日のAI予想 | HAWKS AI", page_icon="⚾", layout="wide")
render_site_navigation(current="daily")

LOCAL_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "today_ai_predictions.json"
REMOTE_DATA_URL = (
    "https://raw.githubusercontent.com/"
    "JapanLiveBusiness/AI-BASEBALL2026/"
    "main-AI-BASEBALL/data/today_ai_predictions.json"
)


@st.cache_data(ttl=300, show_spinner=False)
def load_predictions():
    if LOCAL_DATA_FILE.exists():
        try:
            payload = json.loads(LOCAL_DATA_FILE.read_text(encoding="utf-8"))
            return payload, "HAWKS-AI local"
        except Exception:
            pass

    try:
        response = requests.get(
            REMOTE_DATA_URL,
            headers={"User-Agent": "HAWKS-AI/1.0"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json(), "AI-BASEBALL2026"
    except Exception:
        return None, None


st.title("⚾ 本日のAI予想")
st.caption("NPB全試合を勝率が高い順に表示します。")

payload, source = load_predictions()
if not payload:
    st.warning("本日の予想データを取得できませんでした。")
    st.stop()

games = sorted(
    payload.get("games", []),
    key=lambda game: game.get("rank", 999),
)

st.subheader(f"{payload.get('date', '')} NPB 全試合予想")
if payload.get("updated_at"):
    st.caption(f"更新: {payload.get('updated_at')} / データ元: {source}")

for game in games:
    rank = game.get("rank")
    home = game.get("home", "-")
    away = game.get("away", "-")
    pick = game.get("pick", "-")
    prob = game.get("win_probability", 0)
    score = game.get("predicted_score", "-")
    confidence = game.get("confidence", "-")

    if rank == 1:
        rank_label = "🥇"
    elif rank == 2:
        rank_label = "🥈"
    elif rank == 3:
        rank_label = "🥉"
    else:
        rank_label = f"{rank}位"

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([0.8, 2.8, 2.0, 1.4])
        with c1:
            st.markdown(f"### {rank_label}")
        with c2:
            st.markdown(f"**{home} vs {away}**")
            st.caption(f"予想スコア {score}")
        with c3:
            st.metric("勝利予想", pick, f"{prob}%")
        with c4:
            st.metric("信頼度", confidence)

        try:
            progress_value = max(0, min(100, int(prob))) / 100
        except (TypeError, ValueError):
            progress_value = 0
        st.progress(progress_value)

if games:
    best = games[0]
    st.success(
        f"本日の最上位予想：{best.get('pick')}　"
        f"推定勝率 {best.get('win_probability')}%　"
        f"予想スコア {best.get('predicted_score')}"
    )

st.caption("※AI予測値であり、試合結果を保証するものではありません。")
