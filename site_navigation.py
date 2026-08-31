"""Shared navigation for the unified HAWKS AI site."""

import streamlit as st


_PAGES = (
    ("home", "⌂ 総合ホーム", "pages/0_総合ホーム.py"),
    ("prediction", "◇ AI予測", "app.py"),
    ("profit", "↗ 収支マップ", "pages/収支マップ.py"),
)


def render_site_navigation(*, current: str) -> None:
    """Render every primary feature as one native site navigation."""
    columns = st.columns([1.2, 1.2, 1.2, 4.8])

    for column, (page_id, label, path) in zip(columns, _PAGES):
        with column:
            if current == page_id:
                st.button(label, disabled=True, use_container_width=True)
            else:
                st.page_link(path, label=label, use_container_width=True)

    st.caption(
        "試合分析・AI予測・予想履歴・BET収支を、"
        "HAWKS AI の一つのサイトで管理できます。"
    )
