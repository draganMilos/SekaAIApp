import streamlit as st
import pandas as pd
import re

# --- Email validation helper ---
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email.strip()) is not None

# --- Initialize session state ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Email", "Project", "Tags", "Teams"])

st.title("📨 Email & Invite Assistant")

# --- Section 1: Import Data ---
st.header("1. Import Data")

st.markdown("""
💡 **Tips:**
- To add multiple emails, projects, tags, or teams, separate them with commas  
- Example Emails: `alice@mail.com, bob@mail.com`  
- Example Tags: `design, remote`  
- Example Teams: `backend, frontend`
""")

with st.form("add_email"):
    emails_input = st.text_input("Email(s)")
    projects_input = st.text_input("Project(s)")
    tags_input = st.text_input("Tag(s)")
    teams_input = st.text_input("Team(s)")
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
            for email in emails:
                st.session_state.data = pd.concat([
                    st.session_state.data,
                    pd.DataFrame([{
                        "Email": email,
                        "Project": ", ".join(projects),
                        "Tags": ", ".join(tags),
                        "Teams": ", ".join(teams),
                    }])
                ], ignore_index=True)
            st.success(f"Added {len(emails)} contact(s).")

# --- Display Data Table ---
st.subheader("Current Data")
st.dataframe(st.session_state.data, use_container_width=True)



# ---sections 2 and 3 amend data and send files---

# --- Section 2: Alter / Filter Data ---
st.header("2. Filter Contacts")

all_projects = sorted(set(p.strip() for p_list in st.session_state.data['Project'].dropna() for p in p_list.split(",")))
all_tags = sorted(set(t.strip() for t_list in st.session_state.data['Tags'].dropna() for t in t_list.split(",")))
all_teams = sorted(set(t.strip() for t_list in st.session_state.data['Teams'].dropna() for t in t_list.split(",")))

selected_projects = st.multiselect("Filter by Project(s)", options=all_projects)
selected_tags = st.multiselect("Filter by Tag(s)", options=all_tags)
selected_teams = st.multiselect("Filter by Team(s)", options=all_teams)

def match_filter(row):
    matches_project = any(p.strip() in row['Project'] for p in selected_projects) if selected_projects else True
    matches_tag = any(t.strip() in row['Tags'] for t in selected_tags) if selected_tags else True
    matches_team = any(t.strip() in row['Teams'] for t in selected_teams) if selected_teams else True
    return matches_project and matches_tag and matches_team

filtered_df = st.session_state.data[st.session_state.data.apply(match_filter, axis=1)]

st.subheader("Filtered Emails")
st.write(filtered_df)

emails = filtered_df['Email'].tolist()
email_list_str = ", ".join(emails)

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
    st.markdown("### 📅 Download Calendar Invite")
    from ics import Calendar, Event
    from datetime import datetime, timedelta

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


