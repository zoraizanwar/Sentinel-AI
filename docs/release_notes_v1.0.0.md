# Sentinel AI v1.0.0 — Initial Portfolio Release

## Overview

We are pleased to announce the release of **Sentinel AI v1.0.0**, an enterprise-grade AI Fraud Detection & Risk Intelligence Platform running locally on **localhost**.

Sentinel AI provides an end-to-end fraud analysis, machine learning benchmarking, threshold optimization, SHAP explainability, and multi-tenant portfolio management system for fraud analysts and risk engineering teams.

---

## What's Included in v1.0.0

### 1. Multi-Tenant Organization & Client Architecture
- **Tenant Isolation**: Strict separation across organizations, users, clients, datasets, analyses, transactions, reports, and audit logs.
- **Client Portfolio Management**: Create and track multiple institutional financial clients with dedicated risk metrics.
- **Role-Based Access Control (RBAC)**: Fine-grained permissions for `ORGANIZATION_ADMIN`, `ANALYST`, and `VIEWER`.
- **Append-Only Audit Logs**: Chronological log of all administrative, analysis, and investigation actions.

### 2. Leak-Free Machine Learning Pipeline
- **Temporal Split Validation**: Chronological train/validation/test partitions preventing future leakage.
- **Domain Preprocessing**: Fit-on-train scalers, one-hot encoders, Haversine geodesic distance calculation, cyclical temporal features, and night transaction detection.
- **Model Comparison**: Automated evaluation across **Random Forest**, **Logistic Regression**, and **XGBoost**.
- **Precision-Recall Threshold Optimization**: Optimization of decision boundaries maximizing $F_1$ score under extreme imbalance.
- **Real-World Benchmark Verification**: Evaluated on $555,719$ unseen transactions achieving **0.8189 PR-AUC**, **80.24% Precision**, **75.52% Recall**, and **0.07% False Positive Rate**.

### 3. Explainable AI & Deterministic Risk Scoring
- **0 - 100 Risk Scoring**: Transparent scalar risk values derived directly from fraud probability.
- **Risk Bands**: Calibrated categorization into `LOW` (0-20), `MEDIUM` (20-50), `HIGH` (50-80), and `CRITICAL` (80-100).
- **SHAP Waterfall Attributions**: Local TreeExplainer attribution breakdown isolating exact positive risk-escalators and negative risk-mitigators.

### 4. Enterprise React Dashboard UI
- **Organization Dashboard**: High-level KPI aggregations, client risk overview table, and recent fraud analyses.
- **Client Management & Detail**: Institutional client cards, isolated dataset repositories, and client-specific dashboards.
- **Analysis Overview**: Executive KPI cards, risk distribution donut charts, category loss bar charts, 10-bin risk score histograms, empirical findings, and operational recommendations.
- **Transaction Explorer**: Server-side sorted, paginated, and filtered transaction query engine.
- **Investigation Drawer**: Slide-in drawer with real-time SHAP waterfall charts.
- **Settings & RBAC**: Manage organization members and assign roles.

### 5. Multi-Scope PDF Reporting Engine
- **ReportLab PDF Engine**: Compiles multi-page audit reports with dynamic two-pass `NumberedCanvas` (`Page X of Y`).
- **Three Supported Scopes**: Organization-level reports, Client-level reports, and Analysis-level reports.
- **Embedded Visuals**: High-resolution charts, benchmark tables, confusion matrices, and audit queues.

### 6. Persistence & Storage Layer
- **SQLAlchemy 2.0 Async Engine**: Dual-driver support for PostgreSQL (`asyncpg`) and local zero-setup SQLite (`aiosqlite`).
- **Alembic Database Migrations**: Version-controlled database schema migrations.
- **Thread-Safe In-Memory Session Engine**: Fast local execution without mandatory database setup.

---

## Test Verification

- **Backend Pytest**: **72 passed, 0 failed** (`py -m pytest backend/tests -v`)
- **Frontend Vitest**: **7 passed, 0 failed** (`npm test`)
- **TypeScript**: **0 errors** (`tsc --noEmit`)
- **Production Build**: **Successful** (`npm run build`)

---

## Localhost Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/zoraizanwar/Sentinel-AI.git
cd "Sentinel AI"

# 2. Setup Python environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt

# 3. Setup configuration
copy .env.example .env

# 4. Start backend
py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload

# 5. Start frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser to access Sentinel AI.
