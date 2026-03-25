import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="FDF Log Analyzer", layout="wide")

st.title("🔥 FDF Log Analyzer (Pro Version)")

# =========================
# CONFIG (อ้างอิง repo logic)
# =========================
ERROR_PATTERNS = {
    "errorCode": r'"errorCode":"(.*?)"|errorCode=(\w+)',
    "errorMessage": r'"errorMessage":"(.*?)"|errorMessage=(.*)',
    "vin": r'"vin":"(.*?)"',
    "deviceId": r'"deviceId":"(.*?)"',
    "modelCode": r'"modelCode":"(.*?)"',
    "sendDate": r'"sendDate":"(.*?)"',
    "RequestID": r'Request ID:\s*([0-9a-fA-F\-]{36})',
}

DATETIME_PATTERN = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'

# =========================
# PARSER
# =========================
def extract_datetime(line):
    match = re.search(DATETIME_PATTERN, line)
    return match.group(0) if match else None

def extract_json(line):
    try:
        start = line.find("{")
        end = line.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(line[start:end])
    except:
        return {}
    return {}

def extract_by_patterns(line):
    data = {}
    for key, pattern in ERROR_PATTERNS.items():
        match = re.search(pattern, line)
        if match:
            data[key] = next((g for g in match.groups() if g), None)
        else:
            data[key] = None
    return data

def parse_line(line):
    data = extract_json(line)

    # fallback regex
    if not data:
        data = extract_by_patterns(line)

    # add datetime
    data["log_datetime"] = extract_datetime(line)

    # detect error level
    if "ERROR" in line.upper():
        data["level"] = "ERROR"
    elif "WARN" in line.upper():
        data["level"] = "WARN"
    else:
        data["level"] = "INFO"

    return data

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
        if any(parsed.values()):
            parsed_data.append(parsed)

    if not parsed_data:
        st.warning("❌ No data extracted")
        st.stop()

    df = pd.DataFrame(parsed_data)

    # =========================
    # CLEAN DATA
    # =========================
    df = df.dropna(how="all")
    df = df.fillna("")

    # =========================
    # SIDEBAR FILTER
    # =========================
    st.sidebar.header("🔍 Filter")

    for col in df.columns:
        if df[col].dtype == "object":
            keyword = st.sidebar.text_input(f"{col}", "")
            if keyword:
                df = df[df[col].astype(str).str.contains(keyword, case=False, na=False)]

    # =========================
    # ERROR SUMMARY (เพิ่มจาก repo idea)
    # =========================
    st.subheader("📊 Error Summary")

    if "errorCode" in df.columns:
        error_summary = df["errorCode"].value_counts().reset_index()
        error_summary.columns = ["errorCode", "count"]
        st.dataframe(error_summary, use_container_width=True)

    # =========================
    # PREVIEW
    # =========================
    st.subheader("📄 Preview Data")
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
