import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="Log Extractor Pro", layout="wide")

st.title("🚀 Log Extractor Pro Max")

# =========================
# PARSER (AUTO JSON + REGEX)
# =========================
def extract_json_from_line(line):
    try:
        start = line.find("{")
        end = line.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(line[start:end])
    except:
        return {}
    return {}

def extract_with_regex(line):
    patterns = {
        "vin": r'"vin":"(.*?)"',
        "deviceId": r'"deviceId":"(.*?)"',
        "modelCode": r'"modelCode":"(.*?)"',
        "sendDate": r'"sendDate":"(.*?)"',
    }

    data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, line)
        data[key] = match.group(1) if match else None

    return data

def parse_line(line):
    data = extract_json_from_line(line)
    if data:
        return data
    return extract_with_regex(line)

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("📂 Upload log file", type=["txt", "log", "json"])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    lines = content.splitlines()

    parsed_data = []
    for line in lines:
        parsed = parse_line(line)
        if parsed:
            parsed_data.append(parsed)

    if not parsed_data:
        st.warning("❌ No data extracted")
        st.stop()

    df = pd.DataFrame(parsed_data)

    # =========================
    # SIDEBAR FILTER
    # =========================
    st.sidebar.header("🔍 Filter")

    for col in df.columns:
        if df[col].dtype == "object":
            keyword = st.sidebar.text_input(f"{col}", "")
            if keyword:
                df = df[df[col].astype(str).str.contains(keyword, na=False)]

    # =========================
    # PREVIEW
    # =========================
    st.subheader("📊 Preview Data")
    st.dataframe(df, use_container_width=True)

    # =========================
    # COLUMN SELECTOR
    # =========================
    st.subheader("🎯 Select Columns")

    selected_columns = st.multiselect(
        "Choose columns to export",
        df.columns.tolist(),
        default=df.columns.tolist()
    )

    df_selected = df[selected_columns]

    st.subheader("📌 Filtered Preview")
    st.dataframe(df_selected, use_container_width=True)

    # =========================
    # EXPORT
    # =========================
    st.subheader("⬇️ Export")

    col1, col2 = st.columns(2)

    with col1:
        csv = df_selected.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            csv,
            "output.csv",
            "text/csv"
        )

    with col2:
        excel_file = "output.xlsx"
        df_selected.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
