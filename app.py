import streamlit as st
import time
from sms_scam_detection import (
    extract_text_from_pdf,
    predict,
    train_naive_bayes,
    load_data,
    split_data,
    send_alert,
    log_alert,
    auto_response
)

# ✅ LOGGER IMPORT
from logger import update_logs, is_blocked, save_logs

# -----------------------------
# LOAD & TRAIN MODEL (CACHE)
# -----------------------------
@st.cache_data
def load_model():
    data = load_data("final_dataset.txt")
    train_data, _ = split_data(data)
    return train_naive_bayes(train_data)

spam_words, ham_words, spam_count, ham_count = load_model()

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Detectra AI",
    page_icon="🛡️",
    layout="centered"
)

# -----------------------------
# 🎨 CSS
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}
.card {
    background: #1e293b;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
    margin-bottom: 20px;
}
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
}
.stButton>button:hover {
    transform: scale(1.05);
}
h2, h3 {
    color: #38bdf8;
}
</style>
""", unsafe_allow_html=True)
# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div style="
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    padding:25px;
    border-radius:18px;
    text-align:center;
    color:white;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
">
    <h1 style="margin-bottom:5px;">🛡️ Detectra AI</h1>
    <p style="margin-top:0; font-size:15px; color:#e0e0e0;">
        Real-time Smishing Detection & Automated Response
    </p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.caption(" 🚀 AI-powered system to detect and prevent SMS & PDF-based smishing attacks.")
# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📩 SMS Detection", "📄 PDF Detection", "📊 Dashboard"])

# =============================
# 📩 SMS DETECTION
# =============================
with tab1:

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("📩 SMS Detection")
    message = st.text_area("Type your SMS here")
    site = st.text_input("Enter sender (phone / site)", value="unknown")

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Analyze Message"):

        if message.strip() == "":
            st.warning("⚠️ Please enter a message")

        else:
            with st.spinner("Analyzing..."):
                time.sleep(1)

            # 🟢 STEP 1: PREDICT FIRST
            result = predict(message, spam_words, ham_words, spam_count, ham_count)

            # 🔵 STEP 2: LOG EVERYTHING (IMPORTANT)
            update_logs(message, result, source="SMS", site=site)

            # 🔴 STEP 3: CHECK BLOCK
            if is_blocked(site):
                st.error("🚫 This source is blocked due to repeated spam activity")
                st.stop()   # ❗ stops further execution

            # -----------------------------
            # NORMAL FLOW
            # -----------------------------
            log_alert(result, message)
            response = auto_response(result)
            alert_msg = send_alert(result)

            st.divider()

            if result == "spam":
                st.error("Threat Level: HIGH 🚨")

                st.markdown(f"""
                <div class="card">
                    <b>⚠️ Response:</b> {response["message"]}<br><br>
                    <b>⚙️ Action:</b> {response.get("action", "Blocked")}
                </div>
                """, unsafe_allow_html=True)

                st.error(alert_msg)

                st.success("✅ Threat mitigated successfully")

            else:
                st.success("Threat Level: LOW ✅")
                st.success(alert_msg)

            # INCIDENT LOG
            st.markdown(f"""
            <div class="card">
                <h4>📊 Incident Log</h4>
                <p><b>Type:</b> {"Spam" if result=="spam" else "Safe"}</p>
                <p><b>Source:</b> {site}</p>
                <p><b>Time:</b> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            """, unsafe_allow_html=True)


# =============================
# 📄 PDF DETECTION (FINAL IMPROVED VERSION)
# =============================
with tab2:

    import hashlib
    import re
    import time

    # -----------------------------
    # 🔹 PREPROCESS FUNCTION
    # -----------------------------
    def preprocess_text(text):
        text = text.lower()
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"\d+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # -----------------------------
    # 🔹 STRUCTURE CHECK
    # -----------------------------
    def is_structured_document(text):
        lines = text.split('\n')
        if len(lines) == 0:
            return False

        short_lines = sum(1 for line in lines if len(line.strip()) < 60)
        return len(lines) > 20 and (short_lines / len(lines)) > 0.5

    # -----------------------------
    # 🔹 SPAM RATIO CHECK
    # -----------------------------
    def spam_ratio(text, spam_words):
        words = text.split()
        if len(words) == 0:
            return 0
        spam_count_local = sum(1 for w in words if w in spam_words)
        return spam_count_local / len(words)

    # -----------------------------
    # 🔹 REAL DOCUMENT DETECTOR
    # -----------------------------
    def is_real_document(text):
        indicators = [
            "name", "date", "address", "phone", "email",
            "id", "number", "code", "reference",
            "department", "university", "institute",
            "amount", "total", "payment", "transaction",
            "details", "information", "document"
        ]
        count = sum(1 for w in indicators if w in text)
        return count >= 3

    # -----------------------------
    # 🔹 REPETITION CHECK
    # -----------------------------
    def repetition_score(text):
        words = text.split()
        if len(words) == 0:
            return 0
        unique_words = len(set(words))
        return 1 - (unique_words / len(words))

    # -----------------------------
    # 🔹 STRONG SPAM KEYWORD DETECTOR (NEW)
    # -----------------------------
    def strong_spam_signal(text):
        keywords = [
            "urgent", "winner", "lottery", "claim", "prize",
            "click", "verify", "account", "bank", "offer"
        ]
        return sum(1 for w in keywords if w in text) >= 3

    # -----------------------------
    # UI
    # -----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("📄 PDF Detection")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:

        st.info(f"File: {uploaded_file.name}")

        with st.spinner("Scanning PDF..."):
            time.sleep(1)

        # -----------------------------
        # 🔹 FILE HASH
        # -----------------------------
        file_bytes = uploaded_file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        site = file_hash

        uploaded_file.seek(0)

        # -----------------------------
        # 🔹 TEXT EXTRACTION
        # -----------------------------
        text = extract_text_from_pdf(uploaded_file)

        if not text.strip():
            st.warning("⚠️ No readable text found")

        else:
            clean_text = preprocess_text(text)

            # -----------------------------
            # 🔥 BASE SIGNALS
            # -----------------------------
            ml_result = predict(
                clean_text,
                spam_words,
                ham_words,
                spam_count,
                ham_count
            )

            ratio = spam_ratio(clean_text, spam_words)
            structured = is_structured_document(text)
            real_doc = is_real_document(clean_text)
            repetition = repetition_score(clean_text)
            strong_signal = strong_spam_signal(clean_text)

            word_count = len(clean_text.split())

            # -----------------------------
            # 🔥 SMART ML HANDLING (FIXED)
            # -----------------------------
            if word_count > 120 and ratio < 0.25:
                ml_result = "ham"

            # -----------------------------
            # 🎯 FINAL DECISION ENGINE
            # -----------------------------

            # 🚨 HIGH SPAM (STRICT)
            if (
                ratio > 0.50 and
                ml_result == "spam" and
                not structured and
                not real_doc and
                repetition > 0.35
            ):
                prediction = "spam"
                reason = "Highly suspicious content pattern"

            # 🚨 STRONG SPAM OVERRIDE (NEW)
            elif (
                ml_result == "spam" and
                ratio > 0.45 and
                repetition > 0.35 and
                not real_doc
            ):
                prediction = "spam"
                reason = "Strong spam indicators (override)"

            # 🚨 KEYWORD BURST DETECTION (NEW)
            elif strong_signal and ratio > 0.40:
                prediction = "spam"
                reason = "High-risk scam keywords detected"

            # 🟢 REAL DOCUMENT
            elif real_doc:
                prediction = "ham"
                reason = "Detected as real-world document"

            # 🟢 STRUCTURED DOCUMENT
            elif structured and ratio < 0.35:
                prediction = "ham"
                reason = "Structured document format"

            # 🟡 SUSPICIOUS
            elif ratio > 0.30 or repetition > 0.40:
                prediction = "suspicious"
                reason = "Some unusual patterns detected"

            # 🟢 DEFAULT SAFE
            else:
                prediction = "ham"
                reason = "Normal document"

            # -----------------------------
            # 🔵 LOGGING
            # -----------------------------
            update_logs(clean_text, prediction, source="PDF", site=site)

            # -----------------------------
            # 🔴 BLOCK CHECK
            # -----------------------------
            if is_blocked(site):
                st.error("🚫 This PDF is blocked due to repeated spam activity")

            else:
                log_alert(prediction, clean_text)
                alert_msg = send_alert(prediction)

                # -----------------------------
                # 🎯 OUTPUT
                # -----------------------------
                st.metric("📊 Spam Ratio", round(ratio, 2))

                if prediction == "spam":
                    st.error("Threat Level: HIGH 🚨")
                    st.error(alert_msg)

                elif prediction == "suspicious":
                    st.warning("Threat Level: MEDIUM ⚠️")
                    st.warning(alert_msg)

                else:
                    st.success("Threat Level: LOW ✅")
                    st.success(alert_msg)

                st.caption(f"Reason: {reason}")


                # -----------------------------
                # 📊 INCIDENT LOG
                # -----------------------------
                st.markdown(f"""
                <div class="card">
                    <h4>📊 Incident Log</h4>
                    <p><b>Type:</b> {prediction}</p>
                    <p><b>Source:</b> PDF</p>
                    <p><b>Time:</b> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p><b>File ID:</b> {site}</p>
                    <p><b>Spam Ratio:</b> {round(ratio, 3)}</p>
                </div>
                """, unsafe_allow_html=True)
# =============================
# 📊 DASHBOARD
# =============================
with tab3:

    import json
    import pandas as pd
    from datetime import datetime

    st.subheader("📊 System Dashboard")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # -----------------------------
    # 📥 DOWNLOAD LOGS
    # -----------------------------
    st.markdown("### 📥 Download Logs")

    if st.button("🗑️ Clear Logs"):
        save_logs({"messages": [], "word_counts": {}, "blocked_sources": {}})
        st.success("Logs cleared!")


    try:
        with open("logs.json", "r") as f:
            log_data = json.load(f)

        json_str = json.dumps(log_data, indent=4)

        st.download_button(
            label="⬇️ Download logs.json",
            data=json_str,
            file_name="logs.json",
            mime="application/json"
        )

    except:
        st.warning("No logs available to download")

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    try:
        with open("logs.json", "r") as f:
            data = json.load(f)
    except:
        st.warning("No logs available yet")
        st.stop()

    # -----------------------------
    # 📩 MESSAGES TABLE
    # -----------------------------
    st.markdown("### 📩 Messages Log")

    messages = data.get("messages", [])

    if messages:
        df_messages = pd.DataFrame(messages)

        df_messages = df_messages.rename(columns={
            "text": "Message",
            "prediction": "Prediction",
            "site": "Source",
            "time": "Time"
        })

        st.dataframe(df_messages, use_container_width=True)
    else:
        st.info("No messages available")

    # -----------------------------
    # 📊 WORD COUNT TABLE (CLEANED)
    # -----------------------------
    st.markdown("### 📊 Word Frequency")

    word_counts = data.get("word_counts", {})

    if word_counts:
        df_words = pd.DataFrame(
            list(word_counts.items()),
            columns=["Word", "Count"]
        )

        # ✅ REMOVE SMALL/USELESS WORDS
        df_words = df_words[df_words["Word"].str.len() > 2]

        # ✅ SORT + LIMIT
        df_words = df_words.sort_values(by="Count", ascending=False).reset_index(drop=True)
        df_words = df_words.head(20)

        st.dataframe(df_words, use_container_width=True)
    else:
        st.info("No word data available")

    # -----------------------------
    # 🚫 BLOCKED SOURCES TABLE (FILTERED)
    # -----------------------------
    st.markdown("### 🚫 Blocked Sources")

    blocked = data.get("blocked_sources", {})

    if blocked:
        # ✅ ONLY SHOW BLOCKED (>=3)
        df_blocked = pd.DataFrame(
            [(site, count) for site, count in blocked.items() if count >= 3],
            columns=["Source", "Spam Count"]
        )

        if not df_blocked.empty:

            # ✅ SORT
            df_blocked = df_blocked.sort_values(by="Spam Count", ascending=False)

            # ✅ METRIC (COOL ADDITION)
            st.metric("🚫 Total Blocked Sources", len(df_blocked))

            st.dataframe(df_blocked, use_container_width=True)
        else:
            st.info("No sources reached blocking threshold yet")

    else:
        st.info("No blocked sources yet")