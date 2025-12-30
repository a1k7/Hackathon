# ============================================================
# SMARTLAB AI – STREAMLIT APP (WITH DUE REMINDER ALERT + SOUND)
# ============================================================

import streamlit as st
import pandas as pd
import os
import re
import base64
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ------------------------------------------------------------
# STREAMLIT CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="SmartLab AI", layout="centered")

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users_db" not in st.session_state:
    st.session_state.users_db = {}

# ------------------------------------------------------------
# SQLITE – HEALTH REMINDER DB
# ------------------------------------------------------------
engine = create_engine(
    "sqlite:///health_tracker.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True)
    category = Column(String(20))
    name = Column(String(100))
    scheduled_time = Column(DateTime)
    status = Column(String(20), default="Pending")

Base.metadata.create_all(engine)

def get_db():
    return SessionLocal()

# ------------------------------------------------------------
# SOUND ALERT (BEEP)
# ------------------------------------------------------------
def play_alert_sound():
    beep = """
    <audio autoplay>
    <source src="data:audio/wav;base64,
    UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA="
    type="audio/wav">
    </audio>
    """
    st.markdown(beep, unsafe_allow_html=True)

# ------------------------------------------------------------
# CHECK & NOTIFY DUE REMINDERS
# ------------------------------------------------------------
def check_and_notify(db):
    now = datetime.now()
    due_tasks = db.query(Record).filter(
        Record.scheduled_time <= now,
        Record.status == "Pending"
    ).all()

    for task in due_tasks:
        st.error(f"⏰ REMINDER DUE: {task.category} – {task.name}")
        play_alert_sound()
        task.status = "Reminded"
        db.commit()

# ------------------------------------------------------------
# LOGIN PAGE
# ------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("SmartLab AI")

    t1, t2 = st.tabs(["Register", "Login"])

    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Register"):
            st.session_state.users_db[u] = p
            st.success("Registered successfully")

    with t2:
        u = st.text_input("Username", key="l1")
        p = st.text_input("Password", type="password", key="l2")
        if st.button("Login"):
            if st.session_state.users_db.get(u) == p:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ------------------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------------------
page = st.sidebar.radio(
    "Navigate",
    ["Health Reminder", "SmartLab AI", "Logout"]
)

# ------------------------------------------------------------
# HEALTH REMINDER PAGE (WITH ALERT)
# ------------------------------------------------------------
if page == "Health Reminder":
    st.title("⏰ Health & Vaccination Reminder")

    db = get_db()

    with st.form("add_reminder"):
        name = st.text_input("Medicine / Vaccine Name")
        category = st.selectbox("Type", ["Medicine", "Vaccination"])
        time = st.datetime_input("Reminder Time")
        if st.form_submit_button("Add Reminder"):
            db.add(Record(
                name=name,
                category=category,
                scheduled_time=time
            ))
            db.commit()
            st.success("Reminder added")

    # 🔔 CHECK DUE REMINDERS (AUTO)
    check_and_notify(db)

    st.subheader("Scheduled Reminders")
    records = db.query(Record).order_by(Record.scheduled_time).all()

    st.table([{
        "Type": r.category,
        "Name": r.name,
        "Time": r.scheduled_time.strftime("%Y-%m-%d %H:%M"),
        "Status": r.status
    } for r in records])

    db.close()

# ------------------------------------------------------------
# SMARTLAB AI PAGE (PLACEHOLDER – OPTIONAL)
# ------------------------------------------------------------
elif page == "SmartLab AI":
    st.title("🧪 SmartLab AI")
    st.info("Lab report analysis module is active in your main build.")

# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
elif page == "Logout":
    st.session_state.logged_in = False
    st.rerun()
