import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
from ics import Calendar, Event
from datetime import datetime, timedelta

# --- Setup Google Sheets auth ---
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# --- Email validation helper ---
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email.strip()) is not None

# --- User login ---
import streamlit as st
import random
import yagmail

# --- SESSION STATE SETUP ---
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "email_input"
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "verification_code" not in st.session_state:
    st.session_state.verification_code = ""

# --- SIDEBAR LOGIN LOGIC ---
st.sidebar.header("🔐 Login")

if st.session_state.auth_step == "email_input":
    email_input = st.sidebar.text_input("Enter your email")

    if st.sidebar.button("Send Code"):
        if email_input:
            st.session_state.user_email = email_input
            st.session_state.verification_code = str(random.randint(100000, 999999))

            try:
                yag = yagmail.SMTP(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"])
                yag.send(
                    to=email_input,
                    subject="Your Login Code",
                    contents=f"Your Seka App login code is: {st.session_state.verification_code}"
                )
                st.session_state.auth_step = "code_input"
                st.sidebar.success(f"✅ Code sent to {email_input}")
            except Exception as e:
                st.sidebar.error("❌ Failed to send email. Check credentials.")

elif st.session_state.auth_step == "code_input":
    st.sidebar.write(f"Email: {st.session_state.user_email}")
    code_entered = st.sidebar.text_input("Enter the 6-digit code")

    if st.sidebar.button("Verify"):
        if code_entered == st.session_state.verification_code:
            st.session_state.auth_step = "authenticated"
            st.sidebar.success("✅ Login successful!")
        else:
            st.sidebar.error("❌ Invalid code. Try again.")

# --- STOP UNLESS AUTHENTICATED ---
if st.session_state.auth_step != "authenticated":
    st.stop()

# --- Now user is authenticated ---
user_email = st.session_state.user_email


# --- Connect to Google Sheet ---
gc = connect_to_gsheet()
sheet = gc.open_by_key("1gcryrWnWlEt2gN3v1cCWz7QXDJat0_qfkJB37kkm3Oc").sheet1
all_data = sheet.get_all_records()

# --- Filter only this user's data ---
df = pd.DataFrame(all_data)
if "UserID" in df.columns:
    user_df = df[df['UserID'] == user_email]
else:
    user_df = pd.DataFrame(columns=["UserID", "Email", "Project", "Tags", "Teams"])

# --- Display user data ---
st.subheader(f"Welcome, {user_email}")
st.write("Here’s your saved data:")
st.dataframe(user_df)

# --- Section 1: Add New Contacts ---
st.header("1. Add New Contacts")

st.markdown("""
💡 **Tips:**
- You can add multiple emails separated by commas  
- Projects, tags, and teams can also be comma-separated
""")

with st.form("add_entry"):
    emails_input = st.text_input("Email(s)")
    projects_input = st.text_input("Project(s)")
    tags_input = st.text_input("Tags")
    teams_input = st.text_input("Teams")
    submitted = st.form_submit_button("Add Entry")

    if submitted:
        emails = [e.strip() for e in emails_input.split(",") if e.strip()]
        projects = [p.strip() for p in projects_input.split(",") if p.strip()]
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        teams = [t.strip() for t in teams_input.split(",") if t.strip()]

        invalid_emails = [e for e in emails if not is_valid_email(e)]

        if invalid_emails:
            st.error(f"Invalid email(s): {', '.join(invalid_emails)}")
        elif not emails:
            st.warning("Please enter at least one valid email.")
        else:
            new_rows = [{
                "UserID": user_email,
                "Email": email,
                "Project": ", ".join(projects),
                "Tags": ", ".join(tags),
                "Teams": ", ".join(teams),
            } for email in emails]

            for row in new_rows:
                sheet.append_row(list(row.values()))
            st.success(f"Added {len(emails)} contact(s) to your Google Sheet.")

# --- Section 2: Filter Contacts ---
st.header("2. Filter Contacts")

if not user_df.empty:
    all_projects = sorted(set(
        p.strip()
        for p_list in user_df['Project'].dropna()
        for p in str(p_list).split(",")
    ))
    all_tags = sorted(set(
        t.strip()
        for t_list in user_df['Tags'].dropna()
        for t in str(t_list).split(",")
    ))
    all_teams = sorted(set(
        t.strip()
        for t_list in user_df['Teams'].dropna()
        for t in str(t_list).split(",")
    ))

    selected_projects = st.multiselect("Filter by Project(s)", options=all_projects)
    selected_tags = st.multiselect("Filter by Tag(s)", options=all_tags)
    selected_teams = st.multiselect("Filter by Team(s)", options=all_teams)

    def match_filter(row):
        matches_project = any(p.strip() in str(row['Project']) for p in selected_projects) if selected_projects else True
        matches_tag = any(t.strip() in str(row['Tags']) for t in selected_tags) if selected_tags else True
        matches_team = any(t.strip() in str(row['Teams']) for t in selected_teams) if selected_teams else True
        return matches_project and matches_tag and matches_team

    filtered_df = user_df[user_df.apply(match_filter, axis=1)]
else:
    filtered_df = pd.DataFrame(columns=["Email", "Project", "Tags", "Teams"])

# --- Show filtered results ---
st.subheader("Filtered Emails")
if filtered_df.empty:
    st.warning("⚠️ No matching contacts found for the selected filters.")
else:
    st.dataframe(filtered_df)

emails = filtered_df['Email'].tolist()

# --- Section 3: Action ---
st.header("3. Actions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✉️ Create Email Draft")
    subject = st.text_input("Email Subject", "Meeting Invite")
    body = st.text_area("Email Body", "Hi team,\n\nLet's schedule a sync.")
    if st.button("Open Email Draft"):
        mailto_link = f"mailto:{','.join(emails)}?subject={subject}&body={body.replace(' ', '%20').replace('\n', '%0D%0A')}"
        st.markdown(f"[Click to open email draft]({mailto_link})")

with col2:
    st.markdown("### 🗕️ Download Calendar Invite")
    title = st.text_input("Event Title", "Team Sync")
    location = st.text_input("Location", "Zoom or Office")
    start_date = st.date_input("Start Date")
    start_time = st.time_input("Start Time")
    duration = st.number_input("Duration (hours)", value=1.0)

    if st.button("Generate .ics File"):
        start_dt = datetime.combine(start_date, start_time)
        event = Event()
        event.name = title
        event.begin = start_dt
        event.duration = timedelta(hours=duration)
        event.location = location
        event.description = body
        event.attendees = emails

        cal = Calendar()
        cal.events.add(event)
        ics_file = cal.serialize()

        st.download_button("Download .ics file", data=ics_file, file_name="meeting.ics", mime="text/calendar")
