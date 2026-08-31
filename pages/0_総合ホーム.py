import streamlit as st
import streamlit.components.v1 as components

from site_navigation import render_site_navigation


st.set_page_config(
    page_title="MY AI BASEBALL｜総合ホーム",
    page_icon="⚾",
    layout="wide",
)

render_site_navigation(current="home")

st.markdown("# MY AI BASEBALL")
st.caption("試合・戦績・AI予測・予想結果・収支マップを一つの画面で確認")

components.iframe(
    "https://aibaseballgame.f-polaris.jp/",
    height=1100,
    scrolling=True,
)

st.info(
    "画面が表示されない場合は、ブラウザのサイト間コンテンツ制限を確認してください。"
)
