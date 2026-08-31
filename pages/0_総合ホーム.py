from datetime import datetime
import json
from pathlib import Path

import streamlit as st

from site_navigation import render_site_navigation


st.set_page_config(
    page_title="MY AI BASEBALL｜総合ホーム",
    page_icon="⚾",
    layout="wide",
)

render_site_navigation(current="home")


def data_file(name: str) -> Path:
    """Use the persistent production directory with a repository fallback."""
    production = Path("/app/data")
    if production.exists():
        return production / name
    return Path(__file__).resolve().parents[1] / "data" / name


def load_records(name: str) -> list:
    try:
        value = json.loads(data_file(name).read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except Exception:
        return []


history = load_records("game_history.json")
bets = load_records("bet_records.json")
settled = [bet for bet in bets if bet.get("status") == "final"]
total_profit = sum(int(bet.get("profit", 0) or 0) for bet in settled)
wins = sum(1 for bet in settled if bet.get("result") == "win")
losses = sum(1 for bet in settled if bet.get("result") == "loss")
decided = wins + losses
hit_rate = wins / decided * 100 if decided else None

st.markdown("# MY AI BASEBALL")
st.caption("試合分析・勝率予測・予想結果・BET収支を一つのサイトで確認")

m1, m2, m3, m4 = st.columns(4)
m1.metric("保存済み試合", f"{len(history)}試合")
m2.metric("確定BET", f"{len(settled)}試合")
m3.metric("的中率", f"{hit_rate:.1f}%" if hit_rate is not None else "-")
m4.metric("累積収支", f"{total_profit:+,}円")

st.markdown("## メニュー")
prediction, profit = st.columns(2)

with prediction:
    with st.container(border=True):
        st.markdown("### ◇ AI予測")
        st.write("先発投手、直近成績、対戦相性、球場特性、ハンデから勝率を計算します。")
        st.page_link("app.py", label="AI予測を開く", use_container_width=True)

with profit:
    with st.container(border=True):
        st.markdown("### ↗ 収支マップ")
        st.write("BETした試合、的中率、ROI、累積収支と試合ごとの詳細を確認します。")
        st.page_link("pages/収支マップ.py", label="収支マップを開く", use_container_width=True)

st.markdown("## 最近の予想結果")
if not history:
    st.info("保存済みの試合結果はまだありません。AI予測を実行するとここに反映されます。")
else:
    for game in history[:5]:
        date_value = str(game.get("date", "-"))
        opponent = game.get("opponent") or game.get("opponent_name") or "対戦相手"
        probability = game.get("pregame_probability", game.get("ai_probability"))
        score_home = game.get("hawks_score")
        score_away = game.get("opponent_score")
        probability_text = f"{float(probability):.1f}%" if probability is not None else "-"
        score_text = (
            f"{score_home} - {score_away}"
            if score_home is not None and score_away is not None
            else "結果待ち"
        )
        st.write(f"**{date_value} vs {opponent}**　AI勝率 {probability_text}　｜　{score_text}")

st.caption(f"最終表示更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
