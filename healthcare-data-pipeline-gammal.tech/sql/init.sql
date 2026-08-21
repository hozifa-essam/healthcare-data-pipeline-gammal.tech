-- ============================================================================
-- Healthcare Data Warehouse Initialization Script
-- Architecture: Star Schema (Kimball Methodology)
-- Security Standard: HIPAA-Compliant Data Storage & Role Security
-- Database Engine: PostgreSQL 15+
-- ============================================================================

-- إنشاء قاعدة البيانات الخاصة بالمشروع (في حال تنفيذ الكود بشكل منفصل)
-- CREATE DATABASE healthcare_dw;
-- \c healthcare_dw;

-- ============================================================================
-- 1. CLEANUP (Drop existing objects if re-running)
-- ============================================================================
DROP VIEW IF EXISTS vw_hospital_performance_kpis;
DROP VIEW IF EXISTS vw_anonymized_patient_analytics;
DROP TABLE IF EXISTS fact_visits CASCADE;
DROP TABLE IF EXISTS dim_diagnoses CASCADE;
DROP TABLE IF EXISTS dim_doctors CASCADE;
DROP TABLE IF EXISTS dim_patients CASCADE;

-- ============================================================================
-- 2. DIMENSION TABLES (جداول الأبعاد)
-- ============================================================================

-- أ) جدول أبعاد المرضى (Patients Dimension - Encrypted & Masked)
CREATE TABLE dim_patients (
    patient_id INT PRIMARY KEY,
    patient_hash_id VARCHAR(64) NOT NULL UNIQUE,  -- Salted SHA-256 Hash (Zero PII)
    masked_phone VARCHAR(20) NOT NULL,            -- Masked Format: XXX-XXX-1234
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female')),
    age INT CHECK (age >= 0 AND age <= 120),
    blood_type VARCHAR(5) CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    state VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ب) جدول أبعاد الأطباء (Doctors Dimension)
CREATE TABLE dim_doctors (
    doctor_id INT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(50) NOT NULL,
    years_of_experience INT CHECK (years_of_experience >= 0),
    hospital_branch VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ج) جدول أبعاد التشخيصات الطبية (Diagnoses Dimension)
CREATE TABLE dim_diagnoses (
    diagnosis_id INT PRIMARY KEY,
    diagnosis_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL
);

-- إدراج البيانات المرجعية الأساسية للتشخيصات (Seed Data)
INSERT INTO dim_diagnoses (diagnosis_id, diagnosis_name, category) VALUES
(1, 'Hypertension', 'Cardiovascular'),
(2, 'Type 2 Diabetes', 'Endocrine'),
(3, 'Acute Bronchitis', 'Respiratory'),
(4, 'Migraine', 'Neurological');

-- ============================================================================
-- 3. FACT TABLE (جدول الحقائق الرئيسي)
-- ============================================================================

CREATE TABLE fact_visits (
    visit_id INT PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES dim_patients(patient_id) ON DELETE CASCADE,
    doctor_id INT NOT NULL REFERENCES dim_doctors(doctor_id) ON DELETE CASCADE,
    diagnosis_id INT NOT NULL REFERENCES dim_diagnoses(diagnosis_id) ON DELETE RESTRICT,
    visit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    treatment_cost DECIMAL(10, 2) NOT NULL CHECK (treatment_cost >= 0.00),
    length_of_stay_days INT NOT NULL DEFAULT 0 CHECK (length_of_stay_days >= 0),
    readmitted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. PERFORMANCE OPTIMIZATION (B-Tree Indexes & Partitioning Support)
-- ============================================================================

-- فهارس تسريع عمليات الربط والتصفية حسب التاريخ والمرضى
CREATE INDEX idx_fact_visits_date ON fact_visits (visit_date);
CREATE INDEX idx_fact_visits_patient ON fact_visits (patient_id);
CREATE INDEX idx_fact_visits_doctor ON fact_visits (doctor_id);
CREATE INDEX idx_fact_visits_diagnosis ON fact_visits (diagnosis_id);

-- فهرس مركب للتحليلات الزمنية المتقدمة
CREATE INDEX idx_fact_visits_date_cost ON fact_visits (visit_date, treatment_cost);

-- ============================================================================
-- 5. ANALYTICAL VIEWS FOR BUSINESS INTELLIGENCE (KPIs)
-- ============================================================================

-- أ) عرض الإحصائيات الشهرية للأداء المالي والعلاجي للمستشفيات
CREATE VIEW vw_hospital_performance_kpis AS
SELECT 
    DATE_TRUNC('month', f.visit_date) AS visit_month,
    d.specialty,
    COUNT(f.visit_id) AS total_visits,
    COUNT(DISTINCT f.patient_id) AS unique_patients,
    ROUND(AVG(f.treatment_cost), 2) AS avg_treatment_cost,
    SUM(f.treatment_cost) AS total_revenue,
    ROUND(AVG(f.length_of_stay_days), 1) AS avg_length_of_stay,
    SUM(CASE WHEN f.readmitted THEN 1 ELSE 0 END) AS total_readmissions,
    ROUND((SUM(CASE WHEN f.readmitted THEN 1 ELSE 0 END)::NUMERIC / COUNT(f.visit_id)) * 100, 2) AS readmission_rate_pct
FROM fact_visits f
JOIN dim_doctors d ON f.doctor_id = d.doctor_id
GROUP BY 1, 2
ORDER BY visit_month DESC, total_revenue DESC;

-- ب) عرض تحليلي آمن للمرضى بدون أي كشف للهوية (HIPAA Aggregated View)
CREATE VIEW vw_anonymized_patient_analytics AS
SELECT 
    p.age,
    p.gender,
    p.state,
    diag.diagnosis_name,
    COUNT(f.visit_id) AS total_visits,
    ROUND(AVG(f.treatment_cost), 2) AS avg_cost
FROM fact_visits f
JOIN dim_patients p ON f.patient_id = p.patient_id
JOIN dim_diagnoses diag ON f.diagnosis_id = diag.diagnosis_id
GROUP BY p.age, p.gender, p.state, diag.diagnosis_name;

-- ============================================================================
-- 6. SECURITY & ACCESS CONTROL (Enterprise Best Practice)
-- ============================================================================

-- إنشاء دور لقراءة البيانات التحليلية فقط (Analyst Role)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'data_analyst') THEN
      CREATE ROLE data_analyst WITH LOGIN PASSWORD 'analyst_secure_pass_2026';
   END IF;
END
$$;

-- منح صلاحيات القراءة فقط على الـ Views والجداول للدور التحليلي
GRANT USAGE ON SCHEMA public TO data_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO data_analyst;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO data_analyst;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO data_analyst;