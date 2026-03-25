import streamlit as st
import pandas as pd

# 🔥 import logic จาก repo เดิม
# สมมติชื่อไฟล์เดิม: parser.py
from app import ltpzxgit/fdf-error-list  # <-- เปลี่ยนชื่อให้ตรง repo จริง

st.set_page_config(page_title="FDF Tool+", layout="wide")

st.title("🚀 FDF Tool (Enhanced Version)")

# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload log file")

if uploaded_file:
    # =========================
    # ใช้ logic เดิม 100%
    # =========================
    df = process_log_file(uploaded_file)

    if df is None or df.empty:
        st.warning("No data")
        st.stop()

    # =========================
    # PREVIEW (เพิ่มเข้าไป)
    # =========================
    st.subheader("📊 Original Table")
    st.dataframe(df, use_container_width=True)

    # =========================
    # 🎯 COLUMN SELECTOR (ของใหม่)
    # =========================
    st.subheader("🎯 Select Columns")

    selected_columns = st.multiselect(
        "Choose columns",
        df.columns.tolist(),
        default=df.columns.tolist()
    )

    df_selected = df[selected_columns]

    # =========================
    # FILTER (optional เพิ่มเข้าไป)
    # =========================
    st.subheader("🔍 Filter")

    col_filter = st.selectbox("Select column to filter", df_selected.columns)

    keyword = st.text_input("Keyword")

    if keyword:
        df_selected = df_selected[
            df_selected[col_filter].astype(str).str.contains(keyword, case=False, na=False)
        ]

    # =========================
    # FINAL PREVIEW
    # =========================
    st.subheader("📌 Final Preview")
    st.dataframe(df_selected, use_container_width=True)

    # =========================
    # EXPORT
    # =========================
    st.subheader("⬇️ Export")

    col1, col2 = st.columns(2)

    with col1:
        csv = df_selected.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "output.csv")

    with col2:
        df_selected.to_excel("output.xlsx", index=False)

        with open("output.xlsx", "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                "output.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
