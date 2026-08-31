"""Shared navigation for the unified HAWKS AI site."""

import streamlit as st


def render_site_navigation(*, current: str) -> None:
    """Render the two primary entry points without duplicating page logic."""
    home_col, prediction_col, spacer = st.columns([1.15, 1.15, 5.7])

    with home_col:
        if current == "home":
            st.button("⌂ 総合ホーム", disabled=True, use_container_width=True)
        else:
            st.page_link(
                "pages/0_総合ホーム.py",
                label="⌂ 総合ホーム",
                use_container_width=True,
            )

    with prediction_col:
        if current == "prediction":
            st.button("◇ AI予測", disabled=True, use_container_width=True)
        else:
            st.page_link("app.py", label="◇ AI予測", use_container_width=True)

    st.caption(
        "MY AI BASEBALL の総合機能と HAWKS AI の詳細予測を、"
        "このサイトからまとめて利用できます。"
    )
