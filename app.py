import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="FDF Error List", layout="wide")

st.title("📊 FDF Error List Tool")

# =========================
# REGEX (เหมือน repo เดิม)
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
# CORE LOGIC (เหมือน repo)
# =========================
def process_log(lines):
    results = []
    current_request_id = None

    for line in lines:
        # เก็บ RequestID แบบ context
        req_id = extract(REQ_ID_REGEX, line)
        if req_id:
            current_request_id = req_id

        row = {
            "datetime": extract(DATETIME_REGEX, line),
            "RequestID": current_request_id,
            "vin": extract(VIN_REGEX, line),
            "deviceId": extract(DEVICE_REGEX, line),
            "errorCode": extract(ERROR_CODE_REGEX, line),
            "errorMessage": extract(ERROR_MSG_REGEX, line),
            "raw_log": line.strip()
        }

        # เงื่อนไขเหมือน repo: เอาเฉพาะ line ที่มี data สำคัญ
        if any([row["vin"], row["deviceId"], row["errorCode"]]):
            results.append(row)

    df = pd.DataFrame(results)
    return df


# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("📂 Upload log file", type=["txt", "log"])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    lines = content.splitlines()

    # 🔥 ใช้ logic เดิม
    df = process_log(lines)

    if df.empty:
        st.warning("❌ No data found")
        st.stop()

    # =========================
    # ORIGINAL TABLE (เหมือน repo เป๊ะ)
    # =========================
    st.subheader("📊 Original Table")
    st.dataframe(df, use_container_width=True)

    # =========================
    # 🔥 เพิ่ม: COLUMN SELECTOR
    # =========================
    st.subheader("🎯 Select Columns")

    selected_columns = st.multiselect(
        "Choose columns to display/export",
        df.columns.tolist(),
        default=df.columns.tolist()
    )

    df_selected = df[selected_columns]

    # =========================
    # PREVIEW หลังเลือก
    # =========================
    st.subheader("📌 Preview (Selected Columns)")
    st.dataframe(df_selected, use_container_width=True)

    # =========================
    # EXPORT (เฉพาะ column ที่เลือก)
    # =========================
    st.subheader("⬇️ Export")

    col1, col2 = st.columns(2)

    with col1:
        csv = df_selected.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            csv,
            "fdf_error_list.csv",
            "text/csv"
        )

    with col2:
        df_selected.to_excel("fdf_error_list.xlsx", index=False)
        with open("fdf_error_list.xlsx", "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                "fdf_error_list.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
