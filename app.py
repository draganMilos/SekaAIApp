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
