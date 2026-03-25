import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="ITOSE - Tools", layout="wide")

st.title("ITOSE Tools - FDF ERROR LIST")

uploaded_file = st.file_uploader(
    "📥 Upload Log File",
    type=["txt", "csv", "xlsx"]
)

# =========================
# REGEX
# =========================
REQ_ID_REGEX = r"Request ID:\s*([0-9a-fA-F\-]{36})"

# ดึง vin + deviceId เป็นคู่
PAIR_REGEX = r'"vin":"(.*?)".*?"deviceId":"(.*?)"'


# =========================
# READ FILE
# =========================
def read_file(file):
    filename = file.name.lower()

    if filename.endswith(".txt"):
        content = file.read().decode("utf-8", errors="ignore")
        return content.splitlines()

    elif filename.endswith(".csv"):
        df = pd.read_csv(file, dtype=str)
        return df.astype(str).apply(lambda x: " ".join(x), axis=1).tolist()

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(file, dtype=str)
        return df.astype(str).apply(lambda x: " ".join(x), axis=1).tolist()

    return []


# =========================
# EXTRACT
# =========================
def extract_data(lines):
    results = []
    no = 1

    for i in range(len(lines)):
        line = str(lines[i])

        if "ERROR" in line:

            # ===== หา Request ID =====
            request_id = None
            if i + 1 < len(lines):
                next_line = str(lines[i + 1])
                req_match = re.search(REQ_ID_REGEX, next_line)
                if req_match:
                    request_id = req_match.group(1)

            # ===== หา VIN + DeviceID (หลายตัว) =====
            pairs = re.findall(PAIR_REGEX, line)

            for vin, device in pairs:
                results.append({
                    "No.": no,
                    "Request ID": request_id,
                    "VIN": vin,
                    "DeviceID": device
                })
                no += 1

    return pd.DataFrame(results)


# =========================
# MAIN
# =========================
if uploaded_file:
    lines = read_file(uploaded_file)
    df = extract_data(lines)

    if df.empty:
        st.warning("❌ No data found")
        st.stop()

    st.success(f"✅ Extracted {len(df)} records")

    # =========================
    # ORIGINAL TABLE
    # =========================
    st.subheader("📊 Original Data")
    st.dataframe(df, use_container_width=True)

    # =========================
    # 🎯 SELECT COLUMNS (Checkbox)
    # =========================
    st.subheader("🎯 Select Columns")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Select All"):
            st.session_state.selected_cols = df.columns.tolist()

    with col2:
        if st.button("❌ Deselect All"):
            st.session_state.selected_cols = []

    # init state
    if "selected_cols" not in st.session_state:
        st.session_state.selected_cols = df.columns.tolist()

    selected_columns = []

    cols = st.columns(4)

    for i, col in enumerate(df.columns):
        with cols[i % 4]:
            checked = st.checkbox(
                col,
                value=col in st.session_state.selected_cols,
                key=f"col_{col}"
            )
            if checked:
                selected_columns.append(col)

    # update state
    st.session_state.selected_cols = selected_columns

    # กันเลือกว่าง
    if not selected_columns:
        st.warning("⚠️ Please select at least one column")
        st.stop()

    df_selected = df[selected_columns]

    # =========================
    # PREVIEW
    # =========================
    st.subheader("📌 Preview (Selected Columns)")
    st.dataframe(df_selected, use_container_width=True)

    # =========================
    # EXPORT
    # =========================

    # CSV
    csv = df_selected.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download CSV",
        csv,
        "fdferrorlist.csv"
    )

    # Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_selected.to_excel(writer, index=False)

    st.download_button(
        "📥 Download Excel",
        output.getvalue(),
        "fdferrorlist.xlsx"
    )
