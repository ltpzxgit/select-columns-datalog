import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="FDF Error List", layout="wide")

st.title("🔥 FDF Error List Tool (All-in-One)")

# =========================
# REGEX (เหมือน repo)
# =========================
REQ_ID_REGEX = r'Request ID:\s*([0-9a-fA-F\-]{36})'
VIN_REGEX = r'"vin":"(.*?)"'
DEVICE_REGEX = r'"deviceId":"(.*?)"'
ERROR_CODE_REGEX = r'"errorCode":"(.*?)"|errorCode=(\w+)'
ERROR_MSG_REGEX = r'"errorMessage":"(.*?)"|errorMessage=(.*)'
DATETIME_REGEX = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'


# =========================
# HELPER
# =========================
def extract(pattern, text):
    match = re.search(pattern, text)
    if match:
        return next((g for g in match.groups() if g), None)
    return None


# =========================
# CORE LOGIC (context-aware)
# =========================
def process_log(lines):
    results = []

    current_request_id = None
    current_vin = None
    current_device = None

    for line in lines:

        # Request ID
        req_id = extract(REQ_ID_REGEX, line)
        if req_id:
            current_request_id = req_id
            current_vin = None
            current_device = None

        # VIN
        vin = extract(VIN_REGEX, line)
        if vin:
            current_vin = vin

        # Device ID
        device = extract(DEVICE_REGEX, line)
        if device:
            current_device = device

        # Error
        error_code = extract(ERROR_CODE_REGEX, line)
        error_msg = extract(ERROR_MSG_REGEX, line)

        if error_code or error_msg:
            row = {
                "datetime": extract(DATETIME_REGEX, line),
                "RequestID": current_request_id,
                "vin": current_vin,
                "deviceId": current_device,
                "errorCode": error_code,
                "errorMessage": error_msg,
                "raw_log": line.strip()
            }
            results.append(row)

    return pd.DataFrame(results)


# =========================
# READ FILE (smart detect)
# =========================
def read_file(uploaded_file):
    filename = uploaded_file.name.lower()

    # ===== LOG / TXT =====
    if filename.endswith((".txt", ".log")):
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        return content.splitlines(), "log"

    # ===== CSV =====
    elif filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        return df, "table"

    # ===== EXCEL =====
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
        return df, "table"

    # ===== JSON =====
    elif filename.endswith(".json"):
        try:
            data = json.load(uploaded_file)
            df = pd.json_normalize(data)
            return df, "table"
        except:
            return None, None

    return None, None


# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader(
    "📂 Upload file (.log / .txt / .csv / .xlsx / .json)",
    type=["txt", "log", "xlsx", "csv", "json"]
)

if uploaded_file:

    data, file_type = read_file(uploaded_file)

    if data is None:
        st.warning("❌ Unsupported or empty file")
        st.stop()

    # =========================
    # 🔥 HANDLE TYPE
    # =========================
    if file_type == "log":
        df = process_log(data)

    elif file_type == "table":
        df = data

    if df is None or df.empty:
        st.warning("❌ No data found")
        st.stop()

    # =========================
    # ORIGINAL TABLE
    # =========================
    st.subheader("📊 Original Data")
    st.dataframe(df, use_container_width=True)

    # =========================
    # 🎯 COLUMN SELECTOR
    # =========================
    st.subheader("🎯 Select Columns")

    selected_columns = st.multiselect(
        "Choose columns",
        df.columns.tolist(),
        default=df.columns.tolist()
    )

    df_selected = df[selected_columns]

    # =========================
    # PREVIEW
    # =========================
    st.subheader("📌 Preview (Selected Columns)")
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
            "fdf_output.csv",
            "text/csv"
        )

    with col2:
        df_selected.to_excel("fdf_output.xlsx", index=False)
        with open("fdf_output.xlsx", "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                "fdf_output.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
