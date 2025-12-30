# ============================================================
# SMARTLAB AI – ALL-IN-ONE STREAMLIT APP
# 30+ TESTS + SYMPTOMS + EMAIL REMINDER
# ============================================================

import streamlit as st
import pandas as pd
import os, re
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import pdfplumber
import smtplib
from email.message import EmailMessage

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

if "user_email" not in st.session_state:
    st.session_state.user_email = None

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
# SQLITE – HEALTH REMINDER
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
# SMARTLAB MEDICAL DATABASE (30+ TESTS + SYMPTOMS)
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
            "Carries oxygen in blood","Red blood cells count","Packed RBC volume","RBC size",
            "Hemoglobin per RBC","Hemoglobin concentration","RBC size variation",
            "Total immune cells","Bacterial defense","Viral defense","Cleanup cells",
            "Allergy response","Rare immune cells","Blood clotting",
            "Kidney waste","Kidney filter","Protein waste","Bone & nerve health",
            "Bone mineral","Gout indicator","Overall cholesterol","Blood fats",
            "Jaundice marker","Processed bilirubin","Unprocessed bilirubin",
            "Nutrition status","Liver protein","Immune protein","Protein balance",
            "Liver enzyme","Liver enzyme"
        ],
        "Low Symptoms": [
            "Fatigue, dizziness","Weakness","Anemia","Vitamin deficiency","Weakness",
            "Poor oxygen delivery","Anemia","Frequent infections","Low immunity","Weak immunity",
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
            match = re.search(a + r".{0,40}?(\d+\.?\d*)", text)
            if match:
                found[test] = float(match.group(1))
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
# LOGIN
# ------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🧠 SmartLab AI")

    t1, t2 = st.tabs(["Register","Login"])
    with t1:
        u = st.text_input("Username")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Register"):
            st.session_state.users_db[u] = {"password": p, "email": e}
            st.success("Registered")
    with t2:
        u = st.text_input("Username", key="l1")
        p = st.text_input("Password", type="password", key="l2")
        if st.button("Login"):
            user = st.session_state.users_db.get(u)
            if user and user["password"] == p:
                st.session_state.logged_in = True
                st.session_state.user_email = user["email"]
                st.rerun()
            else:
                st.error("Invalid login")
    st.stop()

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
page = st.sidebar.radio("Navigate",["SmartLab AI","Health Reminder","Logout"])

# ------------------------------------------------------------
# SMARTLAB AI PAGE
# ------------------------------------------------------------
if page == "SmartLab AI":
    st.title("🧪 SmartLab AI – Complete Lab Analysis")

    pdf = st.file_uploader("Upload Lab Report (PDF)", type=["pdf"])
    if pdf:
        with open("temp.pdf","wb") as f:
            f.write(pdf.read())

        extracted = scan_pdf("temp.pdf")
        interpreter = MedicalInterpreter()

        if not extracted:
            st.error("No test values detected.")
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
    db = get_db()

    with st.form("add"):
        name = st.text_input("Medicine / Vaccine")
        category = st.selectbox("Type",["Medicine","Vaccination"])
        time = st.datetime_input("Time")
        if st.form_submit_button("Add"):
            db.add(Record(name=name,category=category,scheduled_time=time))
            db.commit()
            st.success("Added")

    now = datetime.now()
    for r in db.query(Record).filter(
        Record.status=="Pending",
        Record.scheduled_time<=now
    ):
        send_email(
            st.session_state.user_email,
            "⏰ Health Reminder – SmartLab AI",
            f"Reminder: {r.name}"
        )
        r.status="Reminded"
        db.commit()

    for r in db.query(Record).all():
        st.write(f"{r.name} | {r.scheduled_time} | {r.status}")

    db.close()

# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
else:
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.rerun()
