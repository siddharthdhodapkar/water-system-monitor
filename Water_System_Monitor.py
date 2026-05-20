import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import json
import os

st.set_page_config(page_title="Water System Stock Monitor", layout="wide")

st.title("💧 Water System Stock Monitor")

# -------------------------
# GOOGLE SHEET CONFIG
# -------------------------

SHEET_ID = "10Yj8d6Mgg8iQS6kwTBb2GJt7l2HEF7s47hkC9PSjYY0"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.duplicated()]
    return df

df = load_data()

# -------------------------
# EMAIL CONFIG (LOCAL TESTING)
# -------------------------

EMAIL_ADDRESS = "ms.siddharth2014@gmail.com"
EMAIL_PASSWORD = "srysdghkajpzsqsu"

def send_email(site_id, stock_value):
    msg = EmailMessage()
    msg["Subject"] = f"Low Stock Alert - Site {site_id}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = "siddharth.dhodapkar@eaiiadvisors.in"

    msg.set_content(
        f"""
        LOW STOCK ALERT

        Site ID: {site_id}
        Current Stock: {stock_value}

        Stock is below threshold (100).
        """
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# -------------------------
# DAILY EMAIL LIMIT (PERSISTENT)
# -------------------------

LOG_FILE = "email_log.json"

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_log(log_data):
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f)

# -------------------------
# SEARCH SECTION
# -------------------------

site_input = st.text_input("Enter Water System ID")

if site_input:

    result = df[df["Water System ID"].astype(str).str.strip() == site_input.strip()]

    if not result.empty:
        site = result.iloc[0]

        st.success("✅ Site Found")

        st.markdown("## 📍 Location Details")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**State:** {site.get('State', 'N/A')}")
            st.markdown(f"**District:** {site.get('District', 'N/A')}")
            st.markdown(f"**Block/Mandal:** {site.get('Block/Mandal', 'N/A')}")

        with col2:
            st.markdown(f"**GP:** {site.get('GP', 'N/A')}")
            st.markdown(f"**Village:** {site.get('Village', 'N/A')}")
            st.markdown(f"**Scheme Name:** {site.get('Scheme name', 'N/A')}")

        st.divider()

        st.markdown("## 📊 Stock Details")

        topup = site.get("Cumulative Top-up count till date", "0")
        consumption = site.get("Cumulative consumption", "0")
        stock = site.get("Stock", "0")

        col3, col4, col5 = st.columns(3)

        col3.metric("Top-up Count", topup)
        col4.metric("Cumulative Consumption", consumption)

        try:
            stock_value = float(stock)
        except:
            stock_value = 0

        # -------------------------
        # STOCK ALERT LOGIC
        # -------------------------

        if stock_value < 100:
            col5.metric("Stock", stock_value, delta="LOW", delta_color="inverse")
            st.error("⚠ Stock is below 100")

            log_data = load_log()
            today = datetime.now().strftime("%Y-%m-%d")

            last_sent_date = log_data.get(site_input)

            if last_sent_date != today:
                if st.button("Send Low Stock Alert Email"):
                    send_email(site_input, stock_value)
                    log_data[site_input] = today
                    save_log(log_data)
                    st.success("📧 Email sent successfully.")
            else:
                st.info("📩 Alert already sent today for this site.")

        else:
            col5.metric("Stock", stock_value)
            st.success("Stock level is sufficient")

    else:
        st.error("❌ No matching Site ID found")

else:
    st.info("🔎 Please enter a Water System ID")
