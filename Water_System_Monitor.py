# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 12:10:34 2026

@author: siddharth.dhodapkar_

Updated: Google Sheets auto-save for logs (stock alerts, issues, daily limits)
"""

import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Water System Monitoring", layout="wide")

st.title("💧 Water System Monitoring Portal")

# ---------------------------------------------------
# GOOGLE SHEET CONFIG (READ - Main Data)
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
# GOOGLE SHEETS WRITE CONFIG (For Logs)
# ---------------------------------------------------
# This connects to a SEPARATE Google Sheet for saving
# stock alerts, issue logs, and daily limit tracking.
#
# SETUP INSTRUCTIONS:
# 1. Go to https://console.cloud.google.com
# 2. Create a project → Enable "Google Sheets API" & "Google Drive API"
# 3. Create a Service Account → Download JSON key
# 4. Add the JSON key contents to Streamlit secrets (see below)
# 5. Create a NEW Google Sheet named "Water Monitor Logs"
# 6. Share that sheet with the service account email (Editor access)
# 7. Inside the sheet, create 3 tabs:
#      - "Stock Alerts"
#      - "Issue Log"
#      - "Daily Limit"
# ---------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- LOG SHEET ID ---
# This is the ID from your Google Sheet URL:
# https://docs.google.com/spreadsheets/d/<THIS_PART>/edit
LOG_SHEET_ID = "1Wleb4aTjGF5OV5PDNoI7GzqNyD4TXDMyb9B-xFF5vL0"


@st.cache_resource
def get_gspread_client():
    """Authenticate and return a gspread client using Streamlit secrets."""
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client


def get_log_sheet(tab_name):
    """Open a specific tab in the log spreadsheet."""
    client = get_gspread_client()
    spreadsheet = client.open_by_key(LOG_SHEET_ID)
    return spreadsheet.worksheet(tab_name)


# ---------------------------------------------------
# EMAIL CONFIG
# ---------------------------------------------------

EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
EMAIL_SENT = st.secrets["EMAIL_SENT"]

def send_email(subject, body, image_file=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_SENT
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
# LOG FUNCTIONS (Now saving to Google Sheets!)
# ---------------------------------------------------

def append_stock_log(site_id, stock_value):
    """Append a stock alert row to the 'Stock Alerts' tab."""
    try:
        sheet = get_log_sheet("Stock Alerts")

        # Add headers if sheet is empty
        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["Site ID", "Stock Level", "Alert Date"])

        row = [
            site_id,
            str(stock_value),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save stock alert to Google Sheet: {e}")
        return False


def append_issue_log(site_id, description):
    """Append an issue row to the 'Issue Log' tab."""
    try:
        sheet = get_log_sheet("Issue Log")

        # Add headers if sheet is empty
        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["Site ID", "Description", "Issue Date"])

        row = [
            site_id,
            description,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save issue to Google Sheet: {e}")
        return False


def load_daily_limit():
    """Load daily limit data from the 'Daily Limit' tab."""
    try:
        sheet = get_log_sheet("Daily Limit")
        records = sheet.get_all_records()

        # Convert list of dicts to {site_id: date} format
        limits = {}
        for row in records:
            limits[str(row.get("Site ID", ""))] = str(row.get("Last Alert Date", ""))
        return limits
    except Exception:
        return {}


def save_daily_limit(site_id, date_str):
    """Update or insert a daily limit entry in the 'Daily Limit' tab."""
    try:
        sheet = get_log_sheet("Daily Limit")

        # Add headers if sheet is empty
        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["Site ID", "Last Alert Date"])

        # Check if site_id already exists → update it
        all_values = sheet.get_all_values()
        for i, row in enumerate(all_values):
            if len(row) > 0 and str(row[0]).strip() == str(site_id).strip():
                # Found existing row → update column B (date)
                sheet.update_cell(i + 1, 2, date_str)
                return True

        # Not found → append new row
        sheet.append_row([site_id, date_str])
        return True
    except Exception as e:
        st.error(f"Failed to save daily limit to Google Sheet: {e}")
        return False


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
                    save_daily_limit(site_input, today)

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

                st.success("✅ Issue submitted")

    else:
        st.error("❌ No matching Site ID found")

else:
    st.info("🔎 Please enter a Water System ID")

