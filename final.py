# ============================================================
# MEDIMIND AI
# SMARTLAB AI + HEALTH REMINDER WITH EMAIL ALERT
# FINAL ALL-IN-ONE STREAMLIT APP
# ============================================================

import streamlit as st
import pandas as pd
import os, re
from datetime import datetime, timezone
import pytz
import smtplib
from email.message import EmailMessage
import pdfplumber

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
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ------------------------------------------------------------
# EMAIL FUNCTION
# ------------------------------------------------------------
def send_email(to_email, subject, body):
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
# DATABASE – REMINDERS
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
# SMARTLAB DATABASE (30+ TESTS + SYMPTOMS)
# ------------------------------------------------------------
def ensure_lab_database():
    if os.path.exists("lab_data.csv"):
        return

    data = {
        "Medical Term": [
            "Hemoglobin","RBC Count","Hematocrit (PCV)","MCV","MCH","MCHC","RDW",
            "Total WBC","Neutrophils","Lymphocytes","Monocytes","Eosinophils","Basophils",
            "Platelets",
            "Blood Urea Nitrogen","Creatinine","Blood Urea","Calcium","Phosphorus","Uric Acid",
            "Total Cholesterol","Triglycerides",
            "Total Bilirubin","Direct Bilirubin","Indirect Bilirubin",
            "Total Protein","Albumin","Globulin","A/G Ratio",
            "SGOT (AST)","SGPT (ALT)"
        ],
        "Unit": [
            "g/dL","million/uL","%","fL","pg","g/dL","%",
            "cells/cumm","%","%","%","%","%",
            "cells/cumm",
            "mg/dL","mg/dL","mg/dL","mg/dL","mg/dL","mg/dL",
            "mg/dL","mg/dL",
            "mg/dL","mg/dL","mg/dL",
            "g/dL","g/dL","g/dL","ratio",
            "U/L","U/L"
        ],
        "Min": [
            13,4.5,40,83,27,31.5,11.6,
            4000,40,20,2,1,0,
            150000,
            5,0.7,15,8.4,2.7,3,
            0,0,
            0.1,0,0.1,
            6,3.5,2,1,
            5,5
        ],
        "Max": [
            17,5.5,50,101,32,34.5,14,
            10000,80,40,10,6,1,
            450000,
            18,1.2,45,10.2,4.9,7,
            200,150,
            1.2,0.3,0.9,
            8,5,3.5,2,
            40,40
        ],
        "Meaning": [
            "Carries oxygen","Red blood cells","Packed cell volume","RBC size","Hb per RBC",
            "Hb concentration","RBC variation","Immune cells","Bacterial defense",
            "Viral defense","Cleanup cells","Allergy response","Rare immune cells",
            "Clotting cells","Kidney waste","Kidney filter","Protein waste",
            "Bone health","Bone mineral","Gout marker",
            "Cholesterol","Blood fats",
            "Jaundice marker","Processed bilirubin","Unprocessed bilirubin",
            "Nutrition","Liver protein","Immune protein","Protein balance",
            "Liver enzyme","Liver enzyme"
        ],
        "Low Symptoms": [
            "Fatigue, dizziness","Weakness","Anemia","Vitamin deficiency","Weakness",
            "Low oxygen","Anemia","Frequent infections","Low immunity","Weak immunity",
            "Poor cleanup","Low allergy response","Rare","Bleeding risk",
            "Kidney failure","Muscle loss","Malnutrition","Bone weakness",
            "Bone issues","Rare","Usually normal","Usually normal",
            "Rare","Rare","Rare",
            "Malnutrition","Liver disease","Immune issues","Protein imbalance",
            "Rare","Rare"
        ],
        "High Symptoms": [
            "Thick blood","Dehydration","Polycythemia","B12 deficiency","Iron overload",
            "Blood disorders","Inflammation","Infection","Bacterial infection",
            "Viral infection","Chronic inflammation","Allergies","Rare","Clot risk",
            "Kidney stress","Kidney disease","Dehydration","Hypercalcemia",
            "Bone disease","Gout pain","Heart disease","Pancreatitis",
            "Jaundice","Liver blockage","Liver disease",
            "Dehydration","Chronic inflammation","Infection","Liver disease",
            "Hepatitis","Liver damage"
        ]
    }

    pd.DataFrame(data).to_csv("lab_data.csv", index=False)

ensure_lab_database()

# ------------------------------------------------------------
# TEST SYNONYMS
# ------------------------------------------------------------
TEST_SYNONYMS = {
    "Hemoglobin":["HB","HAEMOGLOBIN","HAEMOGLOBTN"],
    "RBC Count":["RBC","RED BLOOD CELL"],
    "Hematocrit (PCV)":["PCV","HCT"],
    "MCV":["MCV"],
    "MCH":["MCH"],
    "MCHC":["MCHC"],
    "RDW":["RDW"],
    "Total WBC":["TOTAL WBC","LEUCOCYTES"],
    "Platelets":["PLATELET"],
    "Blood Urea Nitrogen":["BUN"],
    "Creatinine":["CREATININE"],
    "Blood Urea":["BLOOD UREA"],
    "Calcium":["CALCIUM"],
    "Phosphorus":["PHOSPHORUS"],
    "Uric Acid":["URIC ACID"],
    "Total Cholesterol":["CHOLESTEROL"],
    "Triglycerides":["TRIGLYCERIDE"],
    "Total Bilirubin":["BILIRUBIN-TOTAL"],
    "Direct Bilirubin":["BILIRUBIN-DIRECT"],
    "Indirect Bilirubin":["BILIRUBIN-INDIRECT"],
    "SGOT (AST)":["SGOT","AST"],
    "SGPT (ALT)":["SGPT","ALT"]
}

# ------------------------------------------------------------
# PDF SCANNER
# ------------------------------------------------------------
def scan_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + " "

    text = re.sub(r"\s+", " ", text.upper())
    found = {}

    for test, aliases in TEST_SYNONYMS.items():
        for a in aliases:
            m = re.search(a + r".{0,40}?(\d+\.?\d*)", text)
            if m:
                found[test] = float(m.group(1))
                break
    return found

# ------------------------------------------------------------
# INTERPRETER
# ------------------------------------------------------------
class MedicalInterpreter:
    def __init__(self):
        self.db = pd.read_csv("lab_data.csv")

    def analyze(self, term, value):
        row = self.db[self.db["Medical Term"] == term].iloc[0]
        if value < row["Min"]:
            return row, "LOW", row["Low Symptoms"]
        elif value > row["Max"]:
            return row, "HIGH", row["High Symptoms"]
        return row, "NORMAL", "Within healthy range"

# ------------------------------------------------------------
# LOGIN / REGISTER
# ------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🧠 MediMind AI")

    tab1, tab2 = st.tabs(["Register", "Login"])

    with tab1:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if username in st.session_state.users_db:
                st.error("User already exists")
            elif not email:
                st.error("Email required")
            else:
                st.session_state.users_db[username] = {
                    "password": password,
                    "email": email
                }
                st.success("Registered successfully. Please login.")

    with tab2:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            user = st.session_state.users_db.get(username)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = {
                    "username": username,
                    "email": user["email"]
                }
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
page = st.sidebar.radio("Navigate", ["SmartLab AI", "Health Reminder", "Logout"])

# ------------------------------------------------------------
# SMARTLAB AI
# ------------------------------------------------------------
if page == "SmartLab AI":
    st.title("🧪 SmartLab AI – Lab Report Analysis")

    pdf = st.file_uploader("Upload Lab Report (PDF)", type=["pdf"])
    if pdf:
        with open("temp.pdf", "wb") as f:
            f.write(pdf.read())

        extracted = scan_pdf("temp.pdf")
        interpreter = MedicalInterpreter()

        if not extracted:
            st.error("No lab values detected")
        else:
            for test, val in extracted.items():
                row, status, symptom = interpreter.analyze(test, val)
                st.subheader(test)
                st.write(f"**Value:** {val} {row['Unit']}")
                st.write(f"**Status:** {status}")
                st.write(f"**Meaning:** {row['Meaning']}")
                st.write(f"**Possible symptoms:** {symptom}")
                st.divider()

# ------------------------------------------------------------
# HEALTH REMINDER (EMAIL)
# ------------------------------------------------------------
elif page == "Health Reminder":
    st.title("⏰ Health Reminder")

    st_autorefresh(interval=30 * 1000, key="refresh")

    db = get_db()
    user_email = st.session_state.current_user["email"]

    with st.form("add"):
        name = st.text_input("Medicine / Vaccine")
        category = st.selectbox("Type", ["Medicine", "Vaccination"])
        local_time = st.datetime_input("Reminder Time")
        if st.form_submit_button("Add"):
            ist = pytz.timezone("Asia/Kolkata")
            utc = ist.localize(local_time).astimezone(timezone.utc)

            db.add(Record(
                name=name,
                category=category,
                scheduled_time=utc,
                email=user_email
            ))
            db.commit()
            st.success("Reminder added")

    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    for r in db.query(Record).filter(
        Record.status == "Pending",
        Record.scheduled_time <= now
    ):
        send_email(
            r.email,
            "⏰ Health Reminder – MediMind AI",
            f"Reminder: {r.name}"
        )
        r.status = "Reminded"
        db.commit()

    for r in db.query(Record).all():
        ist = pytz.timezone("Asia/Kolkata")
        display_time = r.scheduled_time.astimezone(ist).strftime("%Y-%m-%d %H:%M")

        st.write(f"{r.name} | {display_time} | {r.status}")


    db.close()

# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
else:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()
