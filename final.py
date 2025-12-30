# ============================================================
# MEDI-MIND AI (formerly SmartLab AI)
# HEALTH & VACCINATION REMINDER
# FINAL STABLE VERSION
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import pytz

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from streamlit_autorefresh import st_autorefresh

# ------------------------------------------------------------
# STREAMLIT CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="MediMind AI", layout="centered")

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users_db" not in st.session_state:
    st.session_state.users_db = {}

# ------------------------------------------------------------
# DATABASE (SQLITE)
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
    scheduled_time = Column(DateTime)  # STORED IN UTC
    status = Column(String(20), default="Pending")

Base.metadata.create_all(engine)

def get_db():
    return SessionLocal()

# ------------------------------------------------------------
# REMINDER CHECK + NOTIFICATION (UTC SAFE)
# ------------------------------------------------------------
def check_and_notify(db):
    now_utc = datetime.now(timezone.utc)

    due_tasks = db.query(Record).filter(
        Record.scheduled_time <= now_utc,
        Record.status == "Pending"
    ).all()

    for task in due_tasks:
        st.error(f"⏰ REMINDER DUE: {task.category} – {task.name}")

        # 🔊 SAFE AUDIO (WORKS ON SAFARI + STREAMLIT CLOUD)
        st.audio(
            "https://www.soundjay.com/buttons/sounds/beep-07.mp3",
            autoplay=True
        )

        task.status = "Reminded"
        db.commit()

# ------------------------------------------------------------
# LOGIN PAGE
# ------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🧠 MediMind AI")

    t1, t2 = st.tabs(["Register", "Login"])

    with t1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            st.session_state.users_db[username] = password
            st.success("Registered successfully")

    with t2:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if st.session_state.users_db.get(username) == password:
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
# HEALTH REMINDER PAGE (AUTO-REFRESH ENABLED)
# ------------------------------------------------------------
if page == "Health Reminder":
    st.title("⏰ Health & Vaccination Reminder")

    # 🔁 AUTO-REFRESH EVERY 30 SECONDS
    st_autorefresh(interval=30 * 1000, key="reminder_refresh")

    db = get_db()

    with st.form("add_reminder"):
        name = st.text_input("Medicine / Vaccine Name")
        category = st.selectbox("Type", ["Medicine", "Vaccination"])
        local_time = st.datetime_input("Reminder Time (Your Local Time)")
        submitted = st.form_submit_button("Add Reminder")

        if submitted:
            # 🌍 CONVERT IST → UTC (CRITICAL FIX)
            local_tz = pytz.timezone("Asia/Kolkata")
            local_dt = local_tz.localize(local_time)
            utc_dt = local_dt.astimezone(timezone.utc)

            db.add(Record(
                name=name,
                category=category,
                scheduled_time=utc_dt
            ))
            db.commit()
            st.success("Reminder added")

    # 🔔 CHECK & NOTIFY (RUNS EVERY AUTO-REFRESH)
    check_and_notify(db)

    st.subheader("Scheduled Reminders")
    records = db.query(Record).order_by(Record.scheduled_time).all()

    st.table([{
        "Type": r.category,
        "Name": r.name,
        "Time (IST)": r.scheduled_time.astimezone(
            pytz.timezone("Asia/Kolkata")
        ).strftime("%Y-%m-%d %H:%M"),
        "Status": r.status
    } for r in records])

    db.close()

# ------------------------------------------------------------
# SMARTLAB AI PAGE (PLACEHOLDER)
# ------------------------------------------------------------
elif page == "SmartLab AI":
    st.title("🧪 SmartLab AI")
    st.info("Lab report analysis module integrated separately.")

# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
elif page == "Logout":
    st.session_state.logged_in = False
    st.rerun()
