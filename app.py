import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="FDF Error Tool+", layout="wide")

st.title("🔥 FDF Error Tool (Enhanced)")

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
# PARSE FUNCTION (เหมือน repo)
# =========================
def extract(pattern, text):
    match = re.search(pattern, text)
    if match:
        return next((g for g in match.groups() if g), None)
    return None


def parse_log(lines):
    results = []

    current_req_id = None

    for line in lines:
        req_id = extract(REQ_ID_REGEX, line)
        if req_id:
            current_req_id = req_id

        data = {
            "datetime": extract(DATETIME_REGEX, line),
            "RequestID": current_req_id,
            "vin": extract(VIN_REGEX, line),
            "deviceId": extract(DEVICE_REGEX, line),
            "errorCode": extract(ERROR_CODE_REGEX, line),
            "errorMessage": extract(ERROR_MSG_REGEX, line),
            "raw": line.strip()
        }

        # เอาเฉพาะ line ที่มีข้อมูลจริง
        if any([data["vin"], data["deviceId"], data["errorCode"]]):
            results.append(data)

    return pd.DataFrame(results)


# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("📂 Upload log file", type=["txt", "log"])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    lines = content.splitlines()

    # 🔥 ใช้ logic แบบ repo
    df = parse_log(lines)

    if df.empty:
        st.warning("❌ No data found")
        st.stop()

    # =========================
    # TABLE เดิม (เหมือน repo)
    # =========================
    st.subheader("📊 Original Table (เหมือน repo)")
    st.dataframe(df, use_container_width=True)

    # =========================
    # 🎯 เพิ่ม Column Selector
    # =========================
    st.subheader("🎯 Select Columns")

    selected_cols = st.multiselect(
        "Choose columns",
        df.columns.tolist(),
        default=df.columns.tolist()
    )

    df_selected = df[selected_cols]

    # =========================
    # PREVIEW ใหม่
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
