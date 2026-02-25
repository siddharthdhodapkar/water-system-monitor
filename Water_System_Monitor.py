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

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

LOG_SHEET_ID = "1Wleb4aTjGF5OV5PDNoI7GzqNyD4TXDMyb9B-xFF5vL0"

GCP_CREDENTIALS = {
    "type": "service_account",
    "project_id": "water-monitor-system-488307",
    "private_key_id": "1da946b9a0feb705d183c49e2d10006e825bd8a6",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDKDWVAAi8HrixB\nl6ESloZXZy2kBuZEPrPz4gEkgM/l057yWqsIkKoFCMqCetRdwQb89vRT7bJkx93X\n/1qDEmQ52sTTnLPDejFhUheTn26QuI6yQ59HDRYcp0glr8k/5LjtjcbRs7hgWowS\nmPcQiDUU7xfsJyNFo+OEPvJroJkrjIQs+jyunftawHpKzpwV4f/vBJ4ksB1qeUHi\n41T3u6l+b5vFhNlZxCQLvu8CS0sK02osd9novHIhBaMLdrfMOlREsPQJYVB7TAey\nvKSkgIcyX976RThz6cPHcb0GKDu1vA68SOxVxwOvRqfIT5dnQs9dJqIufB32AshZ\nt4/SUB0BAgMBAAECggEAJ6EU+Mb03nbE62CIERNA6ieshf1scHoz5WOwga5aGGO3\nSyWJYjatgitFPO5GdNUFP9xX85YtZSLmWhUVdZvH2KkV7cNQZsiyorntMeEVWIE6\nS7CDrvXcHmaY+ftOZ5++vakPE9ZCFXPtAUDLRIzSjHaQpJrQijoox6lo9r8bC7U8\ncW6zInahPsfbnbabdurAd+z8JoQEYfCLtq30z46yWDJ6dWGFgAHu7FXbTZPUCLnT\nYs5zcXXsOqIRuf454SqqaOzRWCnCxkLlxINz60fARi2xNKGcwtp7EY5vszvCf56M\n5uHC0hJEnmMLLyTDaD5VNyZ27UY6DXu+M5FgLJzk2QKBgQDt1NUy389GBNLAPdpc\nxKAYnD49OFVoYcHrIEcyv3VzPCDWs9LsyUHk/jDEIByI0wVENHCwZEOLTUSGJHfX\nM9gQ6dzjYk30W7Wou9zqDOMekkxcYC+0aEPqT9pWWJnn/ADKSXzrHQ0HHoAzuQUy\nhS060ol+DXW6Bpm4r2lx+rfqPwKBgQDZfNjUF1icxWV0J3AZ7LeeiW9shjjK0q9/\nuQ6KjKXuGwRZw76IhBetYdMBHG8st7Ve4EqXu/iHib2ZvASTabrRZ1na8Isn3Qjj\nI3YgMGCDtmH9y7LI03XGG6tKwyfYQkEsCvEYINhxvPSgjF0vDNREQCJq1f+XrsRm\n82e70OGovwKBgQCa3qEGQ9+BRNrH/H8ZMaDe5b9RtkFHe4D/T0GNtkcRBvKLXQXY\n0yVprGytCgwKvP8M7ukCtAeXynT4tP6k0Em+mcsQ9o60tJOSkOLGNiYfXj0DWk82\nNz8icWVIHOH7wonxL/F8WKqHHEF3bOAJidduGnMV9kXXIT0wmmkbo5vnmQKBgEEE\nWa3N7Oew+0tmHtUhNyNl4rGGzqOTqHN+VyKEOXadDQfoxKT7GDj07ad/YJz1rnrW\ngnYp83pRayTyWEvZZ8gCJZKWJoOcSHPevgmRbMjzVQgSRThUPvkifGq1PMwhwmnw\nO3MDHrGh01/Llm/iXfKpWaCmqOonjP9Z9MDpCQzxAoGBALxELn1Lc15+YA/WBe7Q\nEVUtvZMdo7sVDGedopaEA4xZpKgwuf+uk3cbzMkgpzvCsCXZtnF4q+N6zQcO2Ogt\nYTg6Pg93b3lkpIRwcXcVIlGtXQOISCjuLbeRTXBZj4mLdZpBY1yCSeFaOav/R0x5\neMlIxFJKyDJNPJvPTDPHG6UI\n-----END PRIVATE KEY-----\n",
    "client_email": "water-monitoring-app@water-monitor-system-488307.iam.gserviceaccount.com",
    "client_id": "101213988596292556070",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/water-monitoring-app%40water-monitor-system-488307.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}


@st.cache_resource
def get_gspread_client():
    """Authenticate and return a gspread client."""
    creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=SCOPES)
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
# LOG FUNCTIONS (Saving to Google Sheets)
# ---------------------------------------------------

def append_stock_log(site_id, stock_value):
    """Append a stock alert row to the 'Stock Alerts' tab."""
    try:
        sheet = get_log_sheet("Stock Alerts")

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

        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["Site ID", "Last Alert Date"])

        all_values = sheet.get_all_values()
        for i, row in enumerate(all_values):
            if len(row) > 0 and str(row[0]).strip() == str(site_id).strip():
                sheet.update_cell(i + 1, 2, date_str)
                return True

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

                    st.success("📧 Alert Email Sent & Saved to Google Sheet")
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

                st.success("✅ Issue submitted & saved to Google Sheet.")

    else:
        st.error("❌ No matching Site ID found")

else:
    st.info("🔎 Please enter a Water System ID")
