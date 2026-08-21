# 🏥 Enterprise HIPAA-Compliant Healthcare Data Pipeline

[![Data Engineering](https://img.shields.io/badge/Domain-Data_Engineering-blue.svg)](#)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-green.svg)](https://www.python.org/)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Apache Airflow 2.8](https://img.shields.io/badge/Apache_Airflow-2.8-teal.svg)](https://airflow.apache.org/)
[![Docker Compose](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)

An **end-to-end, enterprise-grade Data Engineering pipeline** designed to ingest, cryptographically anonymize, transform, and load healthcare analytical records into a high-performance **Star Schema Data Warehouse**.

Built with a strict focus on **HIPAA Compliance (21 CFR Part 11)**, **Data Governance**, and **Query Optimization**, this repository showcases how modern healthcare data platforms operate securely at scale.

---

## 📐 Architecture Overview

```text
 [ Synthetic PII Source Engine ]
               │
               ▼
 [ Cryptographic Anonymization Layer ] ──► (Salted SHA-256 + Data Masking)
               │
               ▼
 [ Apache Airflow DAG Orchestrator ] ──► (Automated Daily ETL Workflow)
               │
               ▼
 [ PostgreSQL Data Warehouse Engine ] ──► (Kimball Star Schema + B-Tree Indexes)
               │
               ▼
 [ Analytical Layer / BI Dashboards ] ──► (KPI SQL Views & Role-Based Access Control)
🔥 Key Technical Highlights & Feature Implementation
1. 🔒 Cryptographic Anonymization & Security Standard (HIPAA)
Zero-PII Storage Policy: Raw Patient Identifiable Information (Names, SSNs, raw Phone numbers) is stripped at the extraction layer.

Salted SHA-256 Hashing: Patient unique IDs are hashed using dynamic Salted SHA-256 algorithms to eliminate vulnerability to Rainbow Table attacks.

Format-Preserving Data Masking: Phone numbers and email structures are masked (e.g., +1-XXX-XXX-1234) to preserve demographic analytical value without compromising privacy.

2. 🏛️ Data Warehouse Architecture (Kimball Star Schema)
Designed around a central Fact Table (fact_visits) linked via Foreign Key constraints to specialized Dimension Tables (dim_patients, dim_doctors, dim_diagnoses).

Query Optimization: Custom B-Tree Indexes created on high-cardinality join fields (visit_date, patient_id, doctor_id) and composite indexes for temporal range queries.

Analytical Views: Pre-aggregated KPI Views (vw_hospital_performance_kpis, vw_anonymized_patient_analytics) to serve BI tools seamlessly.

3. ⚙️ Robust Orchestration & Infrastructure as Code (IaC)
Fully containerized environment orchestrating PostgreSQL 15 and Apache Airflow 2.8 via a unified docker-compose.yml.

Multi-database Postgres isolation separating system metadata (airflow) from analytical processing warehouse (healthcare_dw).

Role-Based Access Control (RBAC): SQL initialization scripts configure isolated, read-only analyst roles (data_analyst) following the Principle of Least Privilege.

📂 Repository Structure
Plaintext
healthcare-data-pipeline/
│
├── dags/
│   └── healthcare_pipeline.py     # Apache Airflow DAG & Task Dependency Definitions
│
├── scripts/
│   └── generate_data.py           # Synthetic Generator with Salted SHA-256 & Masking
│
├── sql/
│   └── init.sql                   # Star Schema DDL, Indexes, Views & RBAC Roles
│
├── docker-compose.yml             # Docker Orchestration Setup (Postgres + Airflow)
└── README.md                      # Pipeline Documentation & Architecture Specification
🚀 Getting Started (Run the Project)
Prerequisites
Docker Desktop installed on your machine.

Git installed.

Step 1: Clone the Repository
Bash
git clone [https://github.com/your-username/healthcare-data-pipeline.git](https://github.com/your-username/healthcare-data-pipeline.git)
cd healthcare-data-pipeline
Step 2: Spin Up the Infrastructure via Docker
Run the containerized stack in detached mode:

Bash
docker compose up -d
Step 3: Access Interfaces
Apache Airflow Dashboard: Open http://localhost:8080 in your browser.

Username: admin

Password: admin_secure_password_2026

PostgreSQL Data Warehouse: Connect via DBeaver / pgAdmin or terminal:

Host: localhost | Port: 5432

Database: healthcare_dw | User: airflow

📈 Sample Analytical Queries (Business Intelligence)
You can query the pre-built view directly to extract high-level hospital KPIs:

SQL
-- Query Monthly Revenue, Readmission Rates, and Hospital Specialties
SELECT 
    visit_month,
    specialty,
    total_visits,
    total_revenue,
    readmission_rate_pct
FROM vw_hospital_performance_kpis
ORDER BY visit_month DESC, total_revenue DESC;
👤 Author & Acknowledgments
Developer: Data Engineering Trainee / Candidate

Methodology & Learning: Training Concepts & Practical Implementation inspired by Gammal Tech Data Engineering standards.
