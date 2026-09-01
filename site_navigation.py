"""Shared navigation for the unified HAWKS AI site."""

import streamlit as st


_PAGES = (
    ("home", "⌂ 総合ホーム", "pages/0_総合ホーム.py"),
    ("daily", "⚾ 本日のAI予想", "pages/本日のAI予想.py"),
    ("live", "🔴 リアルタイム", "pages/リアルタイム試合詳細.py"),
    ("prediction", "◇ HAWKS AI予測", "app.py"),
    ("profit", "↗ 収支マップ", "pages/収支マップ.py"),
)


def render_site_navigation(*, current: str) -> None:
    """Render every primary feature as one native site navigation."""
    columns = st.columns([1.15, 1.35, 1.35, 1.4, 1.2, 3.2])

    for column, (page_id, label, path) in zip(columns, _PAGES):
        with column:
            if current == page_id:
                st.button(label, disabled=True, use_container_width=True)
            else:
                st.page_link(path, label=label, use_container_width=True)

    st.caption(
        "本日のNPB全試合予想・リアルタイム試合詳細・HAWKS試合分析・"
        "予想履歴・BET収支を、HAWKS AI の一つのサイトで管理できます。"
    )
