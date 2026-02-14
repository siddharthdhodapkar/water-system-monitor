# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 12:10:34 2026

@author: siddharth.dhodapkar_
"""

import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os
import json

st.set_page_config(page_title="Water System Monitoring", layout="wide")

st.title("💧 Water System Monitoring Portal")

# ---------------------------------------------------
# GOOGLE SHEET CONFIG (READ ONLY)
# ---------------------------------------------------

SHEET_ID = "10Yj8d6Mgg8iQS6kwTBb2GJt7l2HEF7s47hkC9PSjYY0"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.duplicated()]
    return df

df = load_data()

# ---------------------------------------------------
# EMAIL CONFIG (LOCAL TESTING ONLY)
# ---------------------------------------------------

EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]

def send_email(subject, body, image_file=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = "siddharth.dhodapkar@eaiiadvisors.in"
    msg.set_content(body)

    if image_file is not None:
        img_bytes = image_file.read()
        msg.add_attachment(
            img_bytes,
            maintype="image",
            subtype=image_file.type.split("/")[-1],
            filename=image_file.name
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ---------------------------------------------------
# LOG FILE PATHS
# ---------------------------------------------------

STOCK_LOG_FILE = "stock_alert_log.csv"
ISSUE_LOG_FILE = "issue_log.csv"
DAILY_LIMIT_FILE = "daily_stock_alert_limit.json"

# ---------------------------------------------------
# LOG FUNCTIONS
# ---------------------------------------------------

def append_stock_log(site_id, stock_value):
    entry = {
        "Site ID": site_id,
        "Stock Level": stock_value,
        "Alert Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if os.path.exists(STOCK_LOG_FILE):
        df_log = pd.read_csv(STOCK_LOG_FILE)
        df_log = pd.concat([df_log, pd.DataFrame([entry])], ignore_index=True)
    else:
        df_log = pd.DataFrame([entry])

    df_log.to_csv(STOCK_LOG_FILE, index=False)


def append_issue_log(site_id, description):
    entry = {
        "Site ID": site_id,
        "Description": description,
        "Issue Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if os.path.exists(ISSUE_LOG_FILE):
        df_log = pd.read_csv(ISSUE_LOG_FILE)
        df_log = pd.concat([df_log, pd.DataFrame([entry])], ignore_index=True)
    else:
        df_log = pd.DataFrame([entry])

    df_log.to_csv(ISSUE_LOG_FILE, index=False)


def load_daily_limit():
    if os.path.exists(DAILY_LIMIT_FILE):
        with open(DAILY_LIMIT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_daily_limit(data):
    with open(DAILY_LIMIT_FILE, "w") as f:
        json.dump(data, f)

# ---------------------------------------------------
# SEARCH SECTION
# ---------------------------------------------------

site_input = st.text_input("Enter Water System ID")

if site_input:

    result = df[df["Water System ID"].astype(str).str.strip() == site_input.strip()]

    if not result.empty:
        site = result.iloc[0]
        st.success("✅ Site Found")

        # ---------------------------------------------------
        # LOCATION DETAILS
        # ---------------------------------------------------

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

        # ---------------------------------------------------
        # STOCK DETAILS
        # ---------------------------------------------------

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

        daily_limit = load_daily_limit()
        today = datetime.now().strftime("%Y-%m-%d")

        if stock_value < 100:
            col5.metric("Stock", stock_value, delta="LOW", delta_color="inverse")
            st.error("⚠ Stock is below 100")

            if daily_limit.get(site_input) != today:
                if st.button("Send Low Stock Alert Email"):
                    send_email(
                        f"Low Stock Alert - {site_input}",
                        f"Stock below 100.\nCurrent Stock: {stock_value}"
                    )

                    append_stock_log(site_input, stock_value)

                    daily_limit[site_input] = today
                    save_daily_limit(daily_limit)

                    st.success("📧 Alert Email Sent")
            else:
                st.info("Stock alert already sent today for this site.")

        else:
            col5.metric("Stock", stock_value)
            st.success("Stock level sufficient")

        st.divider()

        # ---------------------------------------------------
        # MAINTENANCE DETAILS
        # ---------------------------------------------------

        st.markdown("## 🛠 Maintenance Details")

        installation_date = site.get("Installation Date", "N/A")
        last_maintenance = site.get("Last maintenance done", "N/A")
        upcoming_maintenance = site.get("Upcoming maintenance date", "N/A")

        st.markdown(f"**Installation Date:** {installation_date}")
        st.markdown(f"**Last Maintenance Done:** {last_maintenance}")
        st.markdown(f"**Upcoming Maintenance Date:** {upcoming_maintenance}")

        try:
            upcoming_date = pd.to_datetime(upcoming_maintenance)
            today_dt = pd.Timestamp.now()
            days_remaining = (upcoming_date - today_dt).days

            if days_remaining < 0:
                st.error(f"⚠ Maintenance overdue by {abs(days_remaining)} days!")
            elif days_remaining < 10:
                st.warning(f"⚠ Upcoming maintenance in {days_remaining} days!")
            else:
                st.success(f"Maintenance due in {days_remaining} days")

        except:
            st.info("Maintenance date format not valid.")

        st.divider()

        # ---------------------------------------------------
        # RAISE ISSUE SECTION
        # ---------------------------------------------------

        st.markdown("## 🚨 Raise an Issue")

        issue_description = st.text_area("Describe the issue (max 100 words)")
        uploaded_file = st.file_uploader("Upload image (jpg/png)", type=["jpg", "jpeg", "png"])

        if st.button("Submit Issue"):
            if issue_description.strip() == "":
                st.error("Description cannot be empty.")
            elif len(issue_description.split()) > 100:
                st.error("Description must be under 100 words.")
            else:
                email_body = f"""
ISSUE RAISED

Site ID: {site_input}

Description:
{issue_description}
"""

                send_email(
                    f"Issue Raised - {site_input}",
                    email_body,
                    uploaded_file
                )

                append_issue_log(site_input, issue_description)

                st.success("✅ Issue submitted successfully.")

    else:
        st.error("❌ No matching Site ID found")

else:
    st.info("🔎 Please enter a Water System ID")
