import pandas as pd
import pdfplumber
import re
import os
import sys

# ==========================================
# 1. DATABASE SETUP
# ==========================================
def ensure_database_exists():
    filename = "lab_data.csv"
    
    data = {
        "Medical Term": [
            "Glucose (Fasting)", 
            "Hemoglobin", "RBC Count", "Hematocrit (PCV)", "MCV", "MCH", "MCHC", 
            "RDW", "Total WBC", "Neutrophils", "Lymphocytes", "Monocytes", 
            "Eosinophils", "Basophils", "Platelets",
            "BUN", "Creatinine", "Blood Urea", "Calcium", "Phosphorus", "Uric Acid",
            "Total Cholesterol", "Triglycerides", "HDL Cholesterol", "VLDL Cholesterol", 
            "LDL Cholesterol", "Chol/HDL Ratio",
            "Total Bilirubin", "Direct Bilirubin", "Indirect Bilirubin", 
            "Total Protein", "Albumin", "Globulin", "A/G Ratio", 
            "SGOT (AST)", "SGPT (ALT)", "GGT", "Alkaline Phosphatase"
        ],
        "Simple English": [
            "Blood Sugar Level",
            "Oxygen Carrier Protein", "Red Blood Cell Count", "Packed Cell Volume", "Avg RBC Size", "Avg Hemoglobin Amount", "Avg Hemoglobin Concentration",
            "RBC Size Variation", "Total Immune Cells", "Bacterial Fighters", "Viral Fighters", "Cleanup Cells",
            "Allergy Fighters", "Inflammation Fighters", "Clotting Cells",
            "Blood Urea Nitrogen", "Kidney Waste Filter", "Nitrogen Waste", "Bone Mineral", "Bone Health Mineral", "Gout Marker",
            "Total Fat in Blood", "Fat from Calories", "Good Cholesterol", "Very Bad Cholesterol",
            "Bad Cholesterol", "Heart Risk Ratio",
            "Total Bile Pigment", "Processed Bile Pigment", "Unprocessed Bile Pigment",
            "Total Blood Proteins", "Liver Protein", "Immune Proteins", "Protein Balance",
            "Liver Enzyme (AST)", "Liver Enzyme (ALT)", "Bile Duct Enzyme", "Bone/Liver Enzyme"
        ],
        "Unit": [
            "mg/dL", 
            "g/dL", "mil/uL", "%", "fL", "pg", "g/dL", 
            "%", "cells/cumm", "/cumm", "/cumm", "/cumm", "/cumm", "/cumm", "/cumm", 
            "mg/dL", "mg/dL", "mg/dL", "mg/dL", "mg/dL", "mg/dL", 
            "mg/dL", "mg/dL", "mg/dL", "mg/dL", "mg/dL", "ratio", 
            "mg/dL", "mg/dL", "mg/dL", "g/dL", "g/dL", "g/dL", "ratio", 
            "U/L", "U/L", "U/L", "U/L"
        ],
        "Min": [
            70, 
            13.0, 4.5, 40.0, 83.0, 27.0, 31.5, 
            11.6, 4000, 2000, 1000, 200, 100, 0, 150000, 
            5.0, 0.7, 15.0, 8.4, 2.7, 3.0, 
            0, 0, 40, 2, 0, 0, 
            0.1, 0.0, 0.1, 6.0, 3.5, 2.0, 1.0, 
            5, 5, 5, 30
        ],
        "Max": [
            110, 
            17.0, 5.5, 50.0, 101.0, 32.0, 34.5, 
            14.0, 10000, 7000, 3000, 1000, 500, 100, 450000, 
            18.0, 1.2, 45.0, 10.2, 4.9, 7.0, 
            200, 150, 60, 30, 100, 5.0, 
            1.2, 0.3, 0.9, 8.0, 5.0, 3.5, 2.0, 
            40, 40, 50, 120
        ],
        "Explanation": [
            "Energy source. High = Diabetes risk.",
            "Carries oxygen. Low = Anemia.", "Number of red cells.", "Percentage of blood that is cells.", "Size of red cells. High = B12 deficiency.", "Weight of Hb in cells.", "Concentration of Hb.",
            "Variation in cell size. High = Mixed anemia.", "Overall immune strength.", "Fight bacteria. High = Bacterial infection.", "Fight viruses. High = Viral infection.", "Clear debris. High = Chronic infection.",
            "Fight parasites/allergies.", "Rare immune cells.", "Stop bleeding. Low = Bruising risk.",
            "Waste from protein. High = Kidney stress.", "Muscle waste filtered by kidneys. High = Kidney issues.", "Waste product.", "Crucial for bones/nerves.", "Works with calcium for bones.", "High levels cause Gout (joint pain).",
            "Overall cholesterol health.", "Fat from sugar/carbs.", "Protects heart. Higher is better.", "Carries fat to tissues. High = Risk.",
            "Clogs arteries. Lower is better.", "Ratio of bad to good cholesterol.",
            "Yellow pigment. High = Jaundice.", "Processed by liver.", "Not yet processed.",
            "Overall nutritional status.", "Main liver protein. Low = Liver disease.", "Immune system proteins.", "Balance of proteins.",
            "Released when liver cells damaged.", "Most specific liver enzyme.", "Bile duct damage marker.", "Bone or liver issue marker."
        ]
    }
    
    # Overwrite DB to ensure correctness
    pd.DataFrame(data).to_csv(filename, index=False)

ensure_database_exists()

# ==========================================
# 2. LOGIC ENGINE
# ==========================================
class MedicalInterpreter:
    def __init__(self):
        self.db = pd.read_csv("lab_data.csv")
    
    def get_known_tests(self):
        return self.db['Medical Term'].tolist()

    def analyze(self, term, value):
        record = self.db[self.db['Medical Term'] == term]
        if record.empty: return None
            
        row = record.iloc[0]
        min_val, max_val = float(row['Min']), float(row['Max'])
        
        if value < min_val:
            status = "LOW"
        elif value > max_val:
            status = "HIGH"
        else:
            status = "NORMAL"
            
        return {
            "simple_name": row['Simple English'],
            "explanation": row['Explanation'],
            "unit": row['Unit'],
            "status": status
        }

# ==========================================
# 3. PDF EXTRACTION
# ==========================================
def scan_pdf(pdf_path, tests_to_find):
    extracted = {}
    full_text = ""
    
    synonyms = {
        "Glucose (Fasting)": ["BLOOD SUGAR FASTING", "FASTING BLOOD SUGAR", "Glucose-F"],
        "Hemoglobin": ["HAEMOGLOBIN", "HB", "Hemoglobin"],
        "RBC Count": ["RED BLOOD CELL COUNT", "RBC"],
        "Hematocrit (PCV)": ["PACKED CELL VOLUME", "HCT", "PCV"],
        "MCV": ["MCV", "Mean Corpuscular Volume"],
        "MCH": ["MCH", "Mean Corpuscular Hb"],
        "MCHC": ["MCHC", "Mean Corpuscular Hb Concn"],
        "RDW": ["RDW CV", "Red Cell Distribution Width"],
        "Total WBC": ["TOTAL WBC COUNT", "Total Leucocyte Count", "TLC"],
        "Neutrophils": ["Absolute Neutrophils Count", "Neutrophils"],
        "Lymphocytes": ["Absolute Lymphocyte count", "Lymphocytes"],
        "Monocytes": ["Absolute Monocyte Count", "Monocytes"],
        "Eosinophils": ["Absolute Eosinophil count", "Eosinophils"],
        "Basophils": ["Absolute Basophil count", "Basophils"],
        "BUN": ["BLOOD UREA NITROGEN", "BUN"],
        "Creatinine": ["CREATININE", "S.Creatinine"],
        "Blood Urea": ["BLOOD UREA"],
        "Calcium": ["CALCIUM"],
        "Phosphorus": ["PHOSPHORUS"],
        "Uric Acid": ["URIC ACID"],
        "Total Cholesterol": ["CHOLESTEROL", "Total Cholesterol"],
        "Triglycerides": ["TRIGLYCERIDE", "Triglycerides"],
        "HDL Cholesterol": ["HDL-CHOLESTEROL", "HDL"],
        "VLDL Cholesterol": ["VLDL-CHOLESTEROL"],
        "LDL Cholesterol": ["LDL-CHOLESTEROL"],
        "Chol/HDL Ratio": ["CHOLESTEROL/HDL RATIO"],
        "Total Bilirubin": ["BILIRUBIN-TOTAL"],
        "Direct Bilirubin": ["BILIRUBIN-DIRECT"],
        "Indirect Bilirubin": ["BILIRUBIN-INDIRECT"],
        "Total Protein": ["PROTEIN TOTAL"],
        "Albumin": ["ALBUMIN"],
        "Globulin": ["GLOBULIN"],
        "A/G Ratio": ["ALBUMIN GLOBULIN RATIO", "A/G Ratio"],
        "SGOT (AST)": ["ASPARTATE AMINO TRANSFERASE", "SGOT", "AST"],
        "SGPT (ALT)": ["ALANINE AMINOTRANSFERASE", "SGPT", "ALT"],
        "GGT": ["GAMMA GLUTAMYL TRANSFERASE", "GGT"],
        "Alkaline Phosphatase": ["ALKALINE PHOSPHATASE", "ALP"]
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        
        full_text = re.sub(r'\s+', ' ', full_text)

        for test_name in tests_to_find:
            aliases = synonyms.get(test_name, [test_name])
            for alias in aliases:
                pattern = re.compile(re.escape(alias) + r".*?(\d+\.?\d*)", re.IGNORECASE)
                match = pattern.search(full_text)
                if match:
                    try:
                        extracted[test_name] = float(match.group(1))
                        break 
                    except:
                        pass
    except Exception as e:
        print(f"Error: {e}")
        
    return extracted

# ==========================================
# 4. MAIN TERMINAL APP
# ==========================================
if __name__ == "__main__":
    interpreter = MedicalInterpreter()
    
    # 1. Get PDF Path (Hardcoded for testing or Input)
    # You can simply change this string to your file path
    print("--- SmartLab AI Terminal ---")
    pdf_path = input("Enter path to PDF file: ").strip().strip("'").strip('"')
    
    if not os.path.exists(pdf_path):
        print("Error: File not found.")
        sys.exit()

    # 2. Extract Data
    print(f"\nScanning {pdf_path}...\n")
    known_tests = interpreter.get_known_tests()
    extracted_values = scan_pdf(pdf_path, known_tests)

    if not extracted_values:
        print("No medical data found in PDF.")
    
    # 3. Analyze and Print in Requested Format
    for term, value in extracted_values.items():
        res = interpreter.analyze(term, value)
        if res:
            # Exact format from your request
            print(f"{term} → \"{res['simple_name']}\"")
            print("Value")
            print(f"{value} {res['unit']}")
            print("Status")
            print(res['status'])
            print(res['explanation'])
            print("") # Empty line between entries
