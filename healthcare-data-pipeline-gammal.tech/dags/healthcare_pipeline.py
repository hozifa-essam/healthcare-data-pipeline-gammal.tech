from datetime import datetime, timedelta
import os
import hashlib
import random
import pandas as pd
from faker import Faker

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# ---------------------------------------------------------
# 1. الإعدادات الأساسية للـ DAG
# ---------------------------------------------------------
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'healthcare_data_pipeline',
    default_args=default_args,
    description='HIPAA-Compliant End-to-End Healthcare Data Pipeline',
    schedule_interval='@daily',
    catchup=False,
)

# ---------------------------------------------------------
# 2. وظيفة التشفير واستخراج البيانات (Extract & Anonymize)
# ---------------------------------------------------------
SECRET_SALT = b'gammal_tech_secure_salt_2026'

def advanced_hash(value: str) -> str:
    """تشفير باستخدام Salted SHA-256 لمنع هجمات Rainbow Tables"""
    return hashlib.sha256(value.encode('utf-8') + SECRET_SALT).hexdigest()[:16]

def mask_phone(phone: str) -> str:
    """تطبيق Data Masking على أرقام الهواتف"""
    digits = ''.join(filter(str.isdigit, phone))
    return f"XXX-XXX-{digits[-4:]}" if len(digits) >= 4 else "XXX-XXX-0000"

def generate_and_encrypt_data():
    fake = Faker()
    Faker.seed(42)
    random.seed(42)
    
    # أ) توليد بيانات المرضى وتشفيرها
    patients = []
    for pat_id in range(1, 501):
        raw_name = fake.name()
        raw_phone = fake.phone_number()
        
        patients.append({
            'patient_id': pat_id,
            'patient_hash_id': advanced_hash(f"{raw_name}_{pat_id}"),
            'masked_phone': mask_phone(raw_phone),
            'gender': random.choice(['Male', 'Female']),
            'age': random.randint(18, 85),
            'blood_type': random.choice(['A+', 'A-', 'B+', 'O+', 'O-', 'AB+']),
            'state': fake.state_abbr()
        })
    df_patients = pd.DataFrame(patients)
    df_patients.to_csv('/opt/airflow/data/dim_patients.csv', index=False)

    # ب) توليد بيانات الأطباء
    specialties = ['Cardiology', 'Neurology', 'Pediatrics', 'Orthopedics', 'Oncology']
    doctors = []
    for doc_id in range(1, 51):
        doctors.append({
            'doctor_id': doc_id,
            'doctor_name': f"Dr. {fake.name()}",
            'specialty': random.choice(specialties),
            'years_of_experience': random.randint(3, 30),
            'hospital_branch': fake.city() + " Center"
        })
    df_doctors = pd.DataFrame(doctors)
    df_doctors.to_csv('/opt/airflow/data/dim_doctors.csv', index=False)

    # ج) توليد بيانات الزيارات (Fact Data)
    diagnoses = [
        (1, 'Hypertension', 'Cardiovascular'),
        (2, 'Type 2 Diabetes', 'Endocrine'),
        (3, 'Acute Bronchitis', 'Respiratory'),
        (4, 'Migraine', 'Neurological')
    ]
    
    visits = []
    start_date = datetime(2026, 1, 1)
    for visit_id in range(1, 5000):
        diag_id, _, _ = random.choice(diagnoses)
        visits.append({
            'visit_id': visit_id,
            'patient_id': random.randint(1, 500),
            'doctor_id': random.randint(1, 50),
            'diagnosis_id': diag_id,
            'visit_date': (start_date + timedelta(days=random.randint(0, 200))).strftime('%Y-%m-%d %H:%M:%S'),
            'treatment_cost': round(random.uniform(100.0, 3000.0), 2),
            'length_of_stay_days': random.randint(0, 7),
            'readmitted': random.choice([True, False])
        })
    df_visits = pd.DataFrame(visits)
    df_visits.to_csv('/opt/airflow/data/fact_visits.csv', index=False)

# ---------------------------------------------------------
# 3. وظيفة تحميل البيانات لقاعدة البيانات (Load to Postgres)
# ---------------------------------------------------------
def load_data_to_postgres():
    postgres_hook = PostgresHook(postgres_conn_id='postgres_healthcare')
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()

    # تحميل dim_patients
    df_patients = pd.read_csv('/opt/airflow/data/dim_patients.csv')
    for _, row in df_patients.iterrows():
        cursor.execute("""
            INSERT INTO dim_patients (patient_id, patient_hash_id, masked_phone, gender, age, blood_type, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id) DO NOTHING;
        """, tuple(row))

    # تحميل dim_doctors
    df_doctors = pd.read_csv('/opt/airflow/data/dim_doctors.csv')
    for _, row in df_doctors.iterrows():
        cursor.execute("""
            INSERT INTO dim_doctors (doctor_id, doctor_name, specialty, years_of_experience, hospital_branch)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (doctor_id) DO NOTHING;
        """, tuple(row))

    # تحميل fact_visits
    df_visits = pd.read_csv('/opt/airflow/data/fact_visits.csv')
    for _, row in df_visits.iterrows():
        cursor.execute("""
            INSERT INTO fact_visits (visit_id, patient_id, doctor_id, diagnosis_id, visit_date, treatment_cost, length_of_stay_days, readmitted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (visit_id) DO NOTHING;
        """, tuple(row))

    conn.commit()
    cursor.close()
    conn.close()

# ---------------------------------------------------------
# 4. تعريف الـ Tasks وربط السلسلة (Workflow Pipeline)
# ---------------------------------------------------------

task_extract_encrypt = PythonOperator(
    task_id='generate_and_anonymize_data',
    python_callable=generate_and_encrypt_data,
    dag=dag,
)

task_load_warehouse = PythonOperator(
    task_id='load_to_data_warehouse',
    python_callable=load_data_to_postgres,
    dag=dag,
)

# ترتيب التشغيل
task_extract_encrypt >> task_load_warehouse