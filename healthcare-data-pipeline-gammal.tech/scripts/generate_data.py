"""
Healthcare Synthetic Data Generator & Anonymizer
------------------------------------------------
Author: Data Engineering Candidate
Standard: HIPAA Compliance (21 CFR Part 11 & Privacy Rule)
Description: Generates high-fidelity, anonymized synthetic healthcare datasets 
             using Salted SHA-256 Hashes and Data Masking for Star Schema DWH ingestion.
"""

import os
import csv
import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from faker import Faker
import pandas as pd

# ------------------------------------------------------------------------------
# 1. Configuration & Global Constants
# ------------------------------------------------------------------------------
FAKER_SEED = 2026
RANDOM_SEED = 2026

fake = Faker('en_US')
Faker.seed(FAKER_SEED)
random.seed(RANDOM_SEED)

# Cryptographic Salt for Securing Hash Integrity (Environment Variable or Dynamic Fallback)
SECRET_SALT = os.getenv("APP_DATA_SALT", "gammal_tech_enterprise_salted_key_2026").encode('utf-8')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ------------------------------------------------------------------------------
# 2. Advanced Security & Anonymization Engine
# ------------------------------------------------------------------------------
class SecurityEngine:
    """Handles Data Masking and HMAC/Salted Hashing for PII/PHI compliance."""

    @staticmethod
    def generate_salted_hash(raw_identifier: str) -> str:
        """Generates a cryptographically secure 16-character SHA-256 Salted Hash."""
        hasher = hashlib.sha256()
        hasher.update(SECRET_SALT)
        hasher.update(raw_identifier.encode('utf-8'))
        return hasher.hexdigest()[:16]

    @staticmethod
    def mask_phone_number(phone: str) -> str:
        """Applies Partial Masking to Phone Numbers preserving last 4 digits."""
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) >= 10:
            return f"+1-XXX-XXX-{digits[-4:]}"
        return "+1-XXX-XXX-0000"

    @staticmethod
    def mask_email(email: str) -> str:
        """Masks email username while retaining the domain for demographic analysis."""
        try:
            domain = email.split('@')[1]
            return f"anon_patient_***@{domain}"
        except IndexError:
            return "anon_patient_***@healthportal.org"


# ------------------------------------------------------------------------------
# 3. Synthetic Data Generation Engine
# ------------------------------------------------------------------------------
class HealthcareDataGenerator:
    """Generates synthetic relational entity data (Patients, Doctors, Visits)."""

    DIAGNOSES_CATALOG: List[Dict] = [
        {"id": 1, "name": "Hypertension", "category": "Cardiovascular", "base_cost": 250.0, "max_cost": 1200.0, "stay_risk": 0.1},
        {"id": 2, "name": "Type 2 Diabetes", "category": "Endocrine", "base_cost": 300.0, "max_cost": 1500.0, "stay_risk": 0.15},
        {"id": 3, "name": "Acute Bronchitis", "category": "Respiratory", "base_cost": 150.0, "max_cost": 800.0, "stay_risk": 0.05},
        {"id": 4, "name": "Migraine", "category": "Neurological", "base_cost": 100.0, "max_cost": 600.0, "stay_risk": 0.02},
        {"id": 5, "name": "Myocardial Infarction", "category": "Cardiovascular", "base_cost": 3500.0, "max_cost": 15000.0, "stay_risk": 0.85},
        {"id": 6, "name": "Femur Fracture", "category": "Orthopedics", "base_cost": 2000.0, "max_cost": 8500.0, "stay_risk": 0.90},
    ]

    SPECIALTIES: List[str] = [
        "Cardiology", "Neurology", "Pediatrics", "Orthopedics", 
        "Oncology", "Emergency Medicine", "Internal Medicine"
    ]

    def __init__(self, num_patients: int = 1000, num_doctors: int = 50, num_visits: int = 10000):
        self.num_patients = num_patients
        self.num_doctors = num_doctors
        self.num_visits = num_visits

    def generate_patients(self) -> pd.DataFrame:
        """Generates anonymized Patients Dimension Data (dim_patients)."""
        patients = []
        for pat_id in range(1, self.num_patients + 1):
            raw_name = fake.name()
            raw_phone = fake.phone_number()
            raw_ssn = fake.ssn()
            
            # Generating Salted Hash ID based on SSN & Patient ID
            hash_id = SecurityEngine.generate_salted_hash(f"{raw_ssn}_{pat_id}")
            masked_phone = SecurityEngine.mask_phone_number(raw_phone)
            
            patients.append({
                "patient_id": pat_id,
                "patient_hash_id": hash_id,
                "masked_phone": masked_phone,
                "gender": random.choice(["Male", "Female"]),
                "age": random.choices(
                    population=[random.randint(18, 40), random.randint(41, 65), random.randint(66, 90)],
                    weights=[0.3, 0.45, 0.25]
                )[0],
                "blood_type": random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
                "state": fake.state_abbr(),
                "created_at": datetime.now().isoformat()
            })
        return pd.DataFrame(patients)

    def generate_doctors(self) -> pd.DataFrame:
        """Generates Doctors Dimension Data (dim_doctors)."""
        doctors = []
        for doc_id in range(1, self.num_doctors + 1):
            doctors.append({
                "doctor_id": doc_id,
                "doctor_name": f"Dr. {fake.name()}",
                "specialty": random.choice(self.SPECIALTIES),
                "years_of_experience": random.randint(2, 38),
                "hospital_branch": f"{fake.city()} Medical Center",
                "created_at": datetime.now().isoformat()
            })
        return pd.DataFrame(doctors)

    def generate_visits(self, df_patients: pd.DataFrame, df_doctors: pd.DataFrame) -> pd.DataFrame:
        """Generates Fact Visits Data with logical distribution (fact_visits)."""
        visits = []
        patient_ids = df_patients["patient_id"].values
        doctor_ids = df_doctors["doctor_id"].values
        
        start_date = datetime(2025, 1, 1)

        for visit_id in range(1, self.num_visits + 1):
            patient_id = int(random.choice(patient_ids))
            doctor_id = int(random.choice(doctor_ids))
            
            diagnosis = random.choice(self.DIAGNOSES_CATALOG)
            
            # Cost & Length of stay derived logically based on condition severity
            cost = round(random.uniform(diagnosis["base_cost"], diagnosis["max_cost"]), 2)
            
            is_hospitalized = random.random() < diagnosis["stay_risk"]
            length_of_stay = random.randint(1, 12) if is_hospitalized else 0
            readmitted = random.choice([True, False]) if length_of_stay > 3 else False
            
            visit_timestamp = start_date + timedelta(
                days=random.randint(0, 500),
                hours=random.randint(8, 20),
                minutes=random.randint(0, 59)
            )

            visits.append({
                "visit_id": visit_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "diagnosis_id": diagnosis["id"],
                "visit_date": visit_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "treatment_cost": cost,
                "length_of_stay_days": length_of_stay,
                "readmitted": readmitted,
                "created_at": datetime.now().isoformat()
            })
        return pd.DataFrame(visits)


# ------------------------------------------------------------------------------
# 4. Pipeline Execution & Data Quality Report
# ------------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("🚀 Initiating HIPAA-Compliant Data Generation Engine...")
    print("=" * 60)

    generator = HealthcareDataGenerator(
        num_patients=1000, 
        num_doctors=50, 
        num_visits=10000
    )

    # 1. Generate Dimensions
    print("--> Generating Anonymized Patient Dimension...")
    df_patients = generator.generate_patients()

    print("--> Generating Doctor Dimension...")
    df_doctors = generator.generate_doctors()

    # 2. Generate Fact
    print("--> Generating Fact Visits Engine...")
    df_visits = generator.generate_visits(df_patients, df_doctors)

    # 3. Export to Clean CSVs for Warehouse Ingestion
    print("--> Exporting structured CSV files to /data directory...")
    
    patients_file = os.path.join(OUTPUT_DIR, "dim_patients.csv")
    doctors_file = os.path.join(OUTPUT_DIR, "dim_doctors.csv")
    visits_file = os.path.join(OUTPUT_DIR, "fact_visits.csv")

    df_patients.to_csv(patients_file, index=False)
    df_doctors.to_csv(doctors_file, index=False)
    df_visits.to_csv(visits_file, index=False)

    # 4. Summary Execution Report
    print("\n" + "=" * 60)
    print("✅ DATA PIPELINE PIPELINE GENERATION SUCCESSFUL")
    print("=" * 60)
    print(f"📊 Total Patients Created : {len(df_patients):,} (Salted Hash & Masked)")
    print(f"📊 Total Doctors Created  : {len(df_doctors):,}")
    print(f"📊 Total Visit Records    : {len(df_visits):,}")
    print(f"🔒 Encryption Algorithm   : Salted SHA-256 (Truncated 16-Char)")
    print(f"📂 Output Destination     : {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == "__main__":
    main()