import streamlit as st
import pandas as pd

# Initialize data
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Email", "Project", "Tags"])

st.title("📨 Email & Invite Assistant")

# --- Section 1: Import Data ---
st.header("1. Import Data")
with st.form("add_email"):
    email = st.text_input("Email")
    project = st.text_input("Project")
    tags = st.text_input("Tags (comma-separated)")
    submitted = st.form_submit_button("Add Entry")
    if submitted and email:
        st.session_state.data = pd.concat([
            st.session_state.data,
            pd.DataFrame([{
                "Email": email.strip(),
                "Project": project.strip(),
                "Tags": tags.strip()
            }])
        ], ignore_index=True)

st.dataframe(st.session_state.data)
