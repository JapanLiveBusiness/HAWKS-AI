from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import time
import urllib.request
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
import streamlit as st

from site_navigation import render_site_navigation


st.set_page_config(
    page_title="MY AI BASEBALL｜リアルタイム試合詳細",
    page_icon="⚾",
    layout="wide",
)

render_site_navigation(current="live")

JST = ZoneInfo("Asia/Tokyo")
HAWKS_NAMES = ("ソフトバンク", "福岡ソフトバンク", "ホークス")


def data_file(name: str) -> Path:
    production = Path("/app/data")
    if production.exists():
        return production / name
    return Path(__file__).resolve().parents[1] / "data" / name


def load_today_data() -> dict:
    try:
        value = json.loads(data_file("npb_today.json").read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def find_hawks_game(payload: dict) -> dict | None:
    games = payload.get("games", []) if isinstance(payload, dict) else []
    for game in games:
        home = str(game.get("home", ""))
        away = str(game.get("away", ""))
        if any(name in home for name in HAWKS_NAMES) or any(name in away for name in HAWKS_NAMES):
            return game
    return None


def parse_start_at(game: dict) -> datetime | None:
    try:
        return datetime.strptime(
            f"{game.get('date')} {game.get('time')}",
            "%Y-%m-%d %H:%M",
        ).replace(tzinfo=JST)
    except Exception:
        return None


def in_live_probe_window(game: dict, now: datetime) -> bool:
    start_at = parse_start_at(game)
    if start_at is None or start_at.date() != now.date():
        return False
    return start_at - timedelta(minutes=10) <= now <= start_at + timedelta(hours=6)


def score_from_row(cells: list[str], total_index: int | None) -> int | None:
    if total_index is None or total_index >= len(cells):
        return None
    try:
        return int(cells[total_index])
    except Exception:
        return None


@st.cache_data(ttl=15, show_spinner=False)
def fetch_live_detail(official_url: str) -> dict:
    result = {
        "ok": False,
        "status": "取得中",
        "hawks_score": None,
        "opp_score": None,
        "inning": None,
        "half": None,
        "attacking_team": None,
        "outs": None,
        "base1": False,
        "base2": False,
        "base3": False,
        "batter": None,
        "count": None,
        "last_result": None,
        "box_url": None,
        "play_url": None,
        "updated_at": datetime.now(JST).strftime("%H:%M:%S"),
    }

    if not official_url:
        result["status"] = "速報URL待ち"
        return result

    base = official_url.rstrip("/") + "/"
    box_url = urljoin(base, "box.html")
    play_url = urljoin(base, "playbyplay.html")
    result["box_url"] = box_url
    result["play_url"] = play_url
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        req = urllib.request.Request(box_url, headers=headers)
        box_html = urllib.request.urlopen(req, timeout=8).read()
        box_soup = BeautifulSoup(box_html, "html.parser")
        box_text = box_soup.get_text(" ", strip=True)

        if "試合終了" in box_text:
            result["status"] = "試合終了"
        elif "試合開始前" in box_text:
            result["status"] = "試合開始前"
        else:
            result["status"] = "試合中"

        score_table = None
        for table in box_soup.find_all("table"):
            text = table.get_text(" ", strip=True)
            if "ソフトバンク" in text:
                score_table = table
                break

        if score_table is not None:
            rows = score_table.find_all("tr")
            if len(rows) >= 3:
                header_cells = [
                    c.get_text(" ", strip=True)
                    for c in rows[0].find_all(["th", "td"])
                ]
                total_index = None
                for label in ("計", "R"):
                    if label in header_cells:
                        total_index = header_cells.index(label)
                        break

                row1 = [c.get_text(" ", strip=True) for c in rows[1].find_all(["th", "td"])]
                row2 = [c.get_text(" ", strip=True) for c in rows[2].find_all(["th", "td"])]

                if row1 and "ソフトバンク" in row1[0]:
                    hawks_cells, opp_cells = row1, row2
                else:
                    hawks_cells, opp_cells = row2, row1

                if total_index is None:
                    total_index = 10 if len(hawks_cells) > 10 else len(hawks_cells) - 1

                result["hawks_score"] = score_from_row(hawks_cells, total_index)
                result["opp_score"] = score_from_row(opp_cells, total_index)

        # プレイ・バイ・プレイは試合中だけ取得する。
        if result["status"] != "試合中":
            result["ok"] = True
            return result

        req = urllib.request.Request(play_url, headers=headers)
        play_html = urllib.request.urlopen(req, timeout=8).read()
        play_soup = BeautifulSoup(play_html, "html.parser")

        inning_pattern = re.compile(r"(\d+)回(表|裏)（([^）]+)の攻撃）")
        inning_headers = []
        for tag in play_soup.find_all(["h3", "h4", "h5", "h6"]):
            heading = tag.get_text(" ", strip=True)
            match = inning_pattern.search(heading)
            if match:
                inning_headers.append((tag, match))

        if inning_headers:
            current_heading, match = inning_headers[-1]
            result["inning"] = int(match.group(1))
            result["half"] = match.group(2)
            result["attacking_team"] = match.group(3)

            play_rows: list[list[str]] = []
            cursor = current_heading.find_next()
            while cursor is not None:
                if cursor.name in ("h3", "h4", "h5", "h6"):
                    if inning_pattern.search(cursor.get_text(" ", strip=True)):
                        break

                if cursor.name == "tr":
                    cells = [
                        c.get_text(" ", strip=True)
                        for c in cursor.find_all(["th", "td"])
                    ]
                    if len(cells) >= 5 and re.match(r"^[0-2]アウト$", cells[0]):
                        play_rows.append(cells)

                cursor = cursor.find_next()

            current_row = None
            for cells in reversed(play_rows):
                batter = cells[2].strip() if len(cells) > 2 else ""
                outcome = cells[4].strip() if len(cells) > 4 else ""
                if batter and outcome == "":
                    current_row = cells
                    break

            if current_row is None and play_rows:
                current_row = play_rows[-1]

            if current_row is not None:
                outs_text = current_row[0]
                bases_text = current_row[1]
                out_match = re.search(r"([0-2])アウト", outs_text)
                if out_match:
                    result["outs"] = int(out_match.group(1))

                if "満塁" in bases_text:
                    result["base1"] = result["base2"] = result["base3"] = True
                else:
                    result["base1"] = "1塁" in bases_text
                    result["base2"] = "2塁" in bases_text
                    result["base3"] = "3塁" in bases_text

                result["batter"] = current_row[2] if len(current_row) > 2 else None
                result["count"] = current_row[3] if len(current_row) > 3 else None
                result["last_result"] = current_row[4] if len(current_row) > 4 else None

            for cells in reversed(play_rows):
                if len(cells) > 4 and cells[4].strip():
                    result["last_result"] = cells[4].strip()
                    break

        result["ok"] = True
    except Exception as exc:
        result["status"] = "取得失敗"
        result["error"] = str(exc)

    return result


def static_score(game: dict) -> tuple[int | None, int | None]:
    home = str(game.get("home", ""))
    hawks_home = "ソフトバンク" in home
    home_score = game.get("home_score")
    away_score = game.get("away_score")
    if hawks_home:
        return home_score, away_score
    return away_score, home_score


def runner_text(live: dict) -> str:
    occupied = []
    if live.get("base1"):
        occupied.append("1塁")
    if live.get("base2"):
        occupied.append("2塁")
    if live.get("base3"):
        occupied.append("3塁")
    return "・".join(occupied) if occupied else "走者なし"


payload = load_today_data()
game = find_hawks_game(payload)
now = datetime.now(JST)

st.markdown("# リアルタイム試合詳細")
st.caption("NPB公式速報を利用し、試合中だけ15秒間隔で詳細データを同期します。試合前・終了後の自動同期は停止します。")

if game is None:
    st.info("本日のホークス戦は確認できません。試合が登録されるまでリアルタイム同期は行いません。")
    st.stop()

home = str(game.get("home", "-"))
away = str(game.get("away", "-"))
venue = str(game.get("venue", "-"))
game_time = str(game.get("time", "-"))
source_status = str(game.get("status", "scheduled"))
official_url = str(game.get("official_url", "") or "")

is_local_final = source_status == "final"
probe_window = in_live_probe_window(game, now)
should_probe = probe_window and not is_local_final and bool(official_url)

if should_probe:
    live = fetch_live_detail(official_url)
else:
    hawks_static, opp_static = static_score(game)
    live = {
        "ok": True,
        "status": "試合終了" if is_local_final else "試合開始前",
        "hawks_score": hawks_static,
        "opp_score": opp_static,
        "inning": None,
        "half": None,
        "attacking_team": None,
        "outs": None,
        "base1": False,
        "base2": False,
        "base3": False,
        "batter": None,
        "count": None,
        "last_result": None,
        "updated_at": str(payload.get("updated_at", "-")),
        "box_url": urljoin(official_url.rstrip("/") + "/", "box.html") if official_url else None,
    }

status = str(live.get("status", "取得中"))
status_icon = "🔴" if status == "試合中" else "✅" if status == "試合終了" else "⏳"

with st.container(border=True):
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("状態", f"{status_icon} {status}")
    top2.metric("開始", game_time)
    top3.metric("球場", venue)
    top4.metric("同期", "15秒" if status == "試合中" else "停止")

    st.markdown(f"### {away}  vs  {home}")

    hawks_score = live.get("hawks_score")
    opp_score = live.get("opp_score")
    score_text = "-"
    if hawks_score is not None and opp_score is not None:
        score_text = f"ホークス {hawks_score} - {opp_score} 相手"
    st.markdown(f"## {score_text}")

if status == "試合中":
    inning = live.get("inning")
    half = live.get("half")
    inning_text = f"{inning}回{half}" if inning else "LIVE"
    attack = str(live.get("attacking_team") or "-")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("イニング", inning_text)
    d2.metric("攻撃", attack)
    d3.metric("アウト", f"{live.get('outs')}アウト" if live.get("outs") is not None else "-")
    d4.metric("走者", runner_text(live))

    with st.container(border=True):
        st.markdown("### 現在の打席")
        c1, c2, c3 = st.columns(3)
        c1.metric("打者", str(live.get("batter") or "-"))
        c2.metric("カウント", str(live.get("count") or "-"))
        c3.metric("直近結果", str(live.get("last_result") or "-"))

    st.success("試合中のためリアルタイム同期を実行中です。次回更新は約15秒後です。")
elif status == "試合終了":
    st.success("試合終了を確認しました。自動同期を停止しています。")
else:
    start_at = parse_start_at(game)
    if start_at and now < start_at:
        minutes = max(0, int((start_at - now).total_seconds() // 60))
        st.info(f"試合開始前です。自動同期は停止中です。開始予定まで約{minutes}分。")
    else:
        st.info("現在は自動同期の対象外です。試合中になった時点で15秒同期に切り替わります。")

controls = st.columns([1, 1, 3])
with controls[0]:
    if should_probe and st.button("今すぐ更新", use_container_width=True):
        fetch_live_detail.clear()
        st.rerun()
with controls[1]:
    if live.get("box_url"):
        st.link_button("NPB公式速報", live["box_url"], use_container_width=True)

st.caption(f"最終確認: {live.get('updated_at', '-')} ｜ データ元: NPB公式 / npb_today.json")

if status == "試合中":
    time.sleep(15)
    st.rerun()
