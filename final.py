# ============================================================
# SMARTLAB AI – ALL-IN-ONE STREAMLIT APP
# ============================================================

import streamlit as st
import pandas as pd
import os
import re
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
# SMARTLAB DATABASE (AUTO-CREATED)
# ------------------------------------------------------------
def ensure_lab_database():
    if os.path.exists("lab_data.csv"):
        return

    data = {
        "Medical Term": [
            "Hemoglobin", "RBC Count", "Hematocrit (PCV)", "MCV", "MCH", "MCHC", "RDW",
            "Total WBC", "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils",
            "Platelets",
            "Blood Urea Nitrogen", "Creatinine", "Blood Urea", "Calcium",
            "Phosphorus", "Uric Acid",
            "Total Cholesterol", "Triglycerides",
            "Total Bilirubin", "Direct Bilirubin", "Indirect Bilirubin",
            "Total Protein", "Albumin", "Globulin", "A/G Ratio",
            "SGOT (AST)", "SGPT (ALT)"
        ],
        "Simple English": [
            "Oxygen Carrier", "Red Blood Cells", "Packed Cell Volume", "RBC Size",
            "Hemoglobin per RBC", "Hemoglobin Concentration", "RBC Size Variation",
            "White Blood Cells", "Bacterial Fighters", "Viral Fighters", "Cleanup Cells",
            "Allergy Cells", "Rare Immune Cells",
            "Clotting Cells",
            "Kidney Waste Marker", "Kidney Filter", "Nitrogen Waste", "Bone Mineral",
            "Bone Mineral", "Gout Marker",
            "Total Fat", "Blood Fats",
            "Jaundice Marker", "Processed Bilirubin", "Unprocessed Bilirubin",
            "Nutrition Status", "Liver Protein", "Immune Protein", "Protein Balance",
            "Liver Enzyme", "Liver Enzyme"
        ],
        "Unit": [
            "g/dL", "million/uL", "%", "fL", "pg", "g/dL", "%",
            "cells/cumm", "%", "%", "%", "%", "%",
            "cells/cumm",
            "mg/dL", "mg/dL", "mg/dL", "mg/dL",
            "mg/dL", "mg/dL",
            "mg/dL", "mg/dL",
            "mg/dL", "mg/dL", "mg/dL",
            "g/dL", "g/dL", "g/dL", "ratio",
            "U/L", "U/L"
        ],
        "Min": [
            13, 4.5, 40, 83, 27, 31.5, 11.6,
            4000, 40, 20, 2, 1, 0,
            150000,
            5, 0.7, 15, 8.4,
            2.7, 3,
            0, 0,
            0.1, 0, 0.1,
            6, 3.5, 2, 1,
            5, 5
        ],
        "Max": [
            17, 5.5, 50, 101, 32, 34.5, 14,
            10000, 80, 40, 10, 6, 1,
            450000,
            18, 1.2, 45, 10.2,
            4.9, 7,
            200, 150,
            1.2, 0.3, 0.9,
            8, 5, 3.5, 2,
            40, 40
        ],
        "Explanation": [""] * 31
    }

    pd.DataFrame(data).to_csv("lab_data.csv", index=False)

ensure_lab_database()

# ------------------------------------------------------------
# TEST SYNONYMS (OCR NOISE HANDLING)
# ------------------------------------------------------------
TEST_SYNONYMS = {
    "Hemoglobin": ["HB", "HAEMOGLOBIN", "HAEMOGLOBTN"],
    "RBC Count": ["RBC", "RED BLOOD CELL", "COT"],
    "Hematocrit (PCV)": ["PCV", "HCT", "PACKED CELL VOLUME"],
    "MCV": ["MCV"],
    "MCH": ["MCH"],
    "MCHC": ["MCHC", "ICHQ"],
    "RDW": ["RDW"],
    "Total WBC": ["TOTAL WBC", "LEUCOCYTES"],
    "Platelets": ["PLATELET"],
    "Blood Urea Nitrogen": ["BUN", "BLOOD UREA NITROGEN"],
    "Creatinine": ["CREATININE"],
    "Blood Urea": ["BLOOD UREA"],
    "Calcium": ["CALCIUM"],
    "Phosphorus": ["PHOSPHORUS"],
    "Uric Acid": ["URIC ACID"],
    "Total Cholesterol": ["CHOLESTEROL"],
    "Triglycerides": ["TRIGLYCERIDE"],
    "Total Bilirubin": ["BILIRUBIN-TOTAL"],
    "Direct Bilirubin": ["BILIRUBIN-DIRECT"],
    "Indirect Bilirubin": ["BILIRUBIN-INDIRECT"],
    "SGOT (AST)": ["SGOT", "AST"],
    "SGPT (ALT)": ["SGPT", "ALT"]
}

# ------------------------------------------------------------
# PDF PARSER (ROBUST)
# ------------------------------------------------------------
def scan_pdf(pdf_path):
    import pdfplumber

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + " "

    text = re.sub(r"\s+", " ", text.upper())
    results = {}

    for canonical, aliases in TEST_SYNONYMS.items():
        for alias in aliases:
            pattern = re.compile(
                re.escape(alias) + r".{0,50}?(\d+\.?\d*)",
                re.IGNORECASE
            )
            match = pattern.search(text)
            if match:
                results[canonical] = float(match.group(1))
                break

    return results

# ------------------------------------------------------------
# MEDICAL INTERPRETER
# ------------------------------------------------------------
class MedicalInterpreter:
    def __init__(self):
        self.db = pd.read_csv("lab_data.csv")

    def analyze(self, term, value):
        row = self.db[self.db["Medical Term"] == term]
        if row.empty:
            return None

        row = row.iloc[0]
        if value < row["Min"]:
            status = "LOW"
        elif value > row["Max"]:
            status = "HIGH"
        else:
            status = "NORMAL"

        return {
            "simple": row["Simple English"],
            "unit": row["Unit"],
            "status": status
        }

# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("SmartLab AI")

    t1, t2 = st.tabs(["Register", "Login"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Register"):
            st.session_state.users_db[u] = p
            st.success("Registered")

    with t2:
        u = st.text_input("Username", key="l1")
        p = st.text_input("Password", type="password", key="l2")
        if st.button("Login"):
            if st.session_state.users_db.get(u) == p:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid login")

    st.stop()

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
page = st.sidebar.radio("Navigate", ["SmartLab AI", "Health Reminder", "Logout"])

# ------------------------------------------------------------
# SMARTLAB AI PAGE
# ------------------------------------------------------------
if page == "SmartLab AI":
    st.title("🧪 SmartLab AI – Lab Report Analyzer")

    uploaded = st.file_uploader("Upload Lab PDF", type=["pdf"])
    if uploaded:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded.read())

        extracted = scan_pdf("temp.pdf")
        interpreter = MedicalInterpreter()

        if not extracted:
            st.error("No lab values detected")
        else:
            for term, value in extracted.items():
                res = interpreter.analyze(term, value)
                if res:
                    st.subheader(term)
                    st.write(f"Value: **{value} {res['unit']}**")
                    st.write(f"Status: **{res['status']}**")
                    st.write(res["simple"])
                    st.divider()

# ------------------------------------------------------------
# HEALTH REMINDER PAGE
# ------------------------------------------------------------
elif page == "Health Reminder":
    st.title("⏰ Health Reminder")

    db = get_db()
    with st.form("add"):
        name = st.text_input("Medicine / Vaccine")
        category = st.selectbox("Type", ["Medicine", "Vaccination"])
        time = st.datetime_input("Time")
        if st.form_submit_button("Add"):
            db.add(Record(name=name, category=category, scheduled_time=time))
            db.commit()
            st.success("Added")

    for r in db.query(Record).order_by(Record.scheduled_time).all():
        st.write(f"{r.name} – {r.scheduled_time} – {r.status}")

    db.close()

# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------
elif page == "Logout":
    st.session_state.logged_in = False
    st.rerun()
