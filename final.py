# ============================================================
# MEDI-MIND AI
# HEALTH & VACCINATION REMINDER (EMAIL AT LOGIN ONLY)
# FINAL VERSION
# ============================================================

import streamlit as st
from datetime import datetime, timezone
import pytz
import smtplib
from email.message import EmailMessage

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

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "users_db" not in st.session_state:
    st.session_state.users_db = {}  # username -> {password, email}

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
    scheduled_time = Column(DateTime)  # UTC
    status = Column(String(20), default="Pending")
    email = Column(String(200))

Base.metadata.create_all(engine)

def get_db():
    return SessionLocal()

# ------------------------------------------------------------
# EMAIL FUNCTION
# ------------------------------------------------------------
def send_email_reminder(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = st.secrets["EMAIL_ADDRESS"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(
            st.secrets["EMAIL_ADDRESS"],
            st.secrets["EMAIL_APP_PASSWORD"]
        )
        server.send_message(msg)

# ------------------------------------------------------------
# CHECK & SEND EMAIL REMINDERS
# ------------------------------------------------------------
def check_and_notify(db):
    now_utc = datetime.now(timezone.utc)

    due_tasks = db.query(Record).filter(
        Record.scheduled_time <= now_utc,
        Record.status == "Pending"
    ).all()

    for task in due_tasks:
        try:
            send_email_reminder(
                task.email,
                "⏰ Health Reminder – MediMind AI",
                f"""
Hello,

This is your health reminder.

Type: {task.category}
Name: {task.name}
Time: NOW

Please take the required action.

– MediMind AI
"""
            )
            task.status = "Reminded"
            db.commit()
            st.success(f"Email sent for: {task.name}")
        except Exception as e:
            st.error(f"Email failed: {e}")

# ------------------------------------------------------------
# LOGIN / REGISTER PAGE
# ------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🧠 MediMind AI")

    t1, t2 = st.tabs(["Register", "Login"])

    with t1:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if username in st.session_state.users_db:
                st.error("User already exists")
            else:
                st.session_state.users_db[username] = {
                    "password": password,
                    "email": email
                }
                st.success("Registered successfully")

    with t2:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            user = st.session_state.users_db.get(username)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = user["email"]
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
page = st.sidebar.radio(
    "Navigate",
    ["Health Reminder", "SmartLab AI", "Logout"]
)

# ------------------------------------------------------------
# HEALTH REMINDER PAGE
# ------------------------------------------------------------
if page == "Health Reminder":
    st.title("⏰ Health & Vaccination Reminder")

    st_autorefresh(interval=30 * 1000, key="reminder_refresh")

    db = get_db()

    with st.form("add_reminder"):
        name = st.text_input("Medicine / Vaccine Name")
        category = st.selectbox("Type", ["Medicine", "Vaccination"])
        local_time = st.datetime_input("Reminder Time (Your Local Time)")
        submitted = st.form_submit_button("Add Reminder")

        if submitted:
            local_tz = pytz.timezone("Asia/Kolkata")
            local_dt = local_tz.localize(local_time)
            utc_dt = local_dt.astimezone(timezone.utc)

            db.add(Record(
                name=name,
                category=category,
                scheduled_time=utc_dt,
                email=st.session_state.user_email
            ))
            db.commit()
            st.success("Reminder added")

    # 🔔 CHECK & SEND EMAIL
    check_and_notify(db)

    st.subheader("Scheduled Reminders")
    records = db.query(Record).order_by(Record.scheduled_time).all()

    st.table([{
        "Type": r.category,
        "Name": r.name,
        "Email": r.email,
        "Time (IST)": r.scheduled_time.astimezone(
            pytz.timezone("Asia/Kolkata")
        ).strftime("%Y-%m-%d %H:%M"),
        "Status": r.status
    } for r in records])

    db.close()

# ------------------------------------------------------------
# SMARTLAB AI PAGE
# ------------------------------------------------------------
elif page == "SmartLab AI":
    st.title("🧪 SmartLab AI")
    st.info("Lab analysis module integrated separately.")

# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
elif page == "Logout":
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.rerun()
