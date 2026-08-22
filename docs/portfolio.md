# Sentinel AI — Engineering Portfolio & Technical Case Study

## Executive Summary & Elevator Pitch

**Sentinel AI** is an enterprise-style AI fraud detection and risk intelligence platform built with **Python (FastAPI)**, **React 18 (TypeScript)**, **SQLAlchemy 2.0**, and **Scikit-Learn / XGBoost / SHAP**. 

Designed to combat financial transaction fraud across extreme class imbalances ($171:1$), Sentinel AI implements an automated, leak-free machine learning pipeline that compares candidate models, optimizes decision thresholds via Precision-Recall curve analysis, scores transactions into calibrated financial risk tiers ($0-100$), and produces local game-theoretic SHAP explainability for fraud investigators. The platform features strict multi-tenant organization isolation, client portfolio management, Role-Based Access Control (RBAC), immutable security audit logging, and two-pass ReportLab PDF report generation.

---

## 1. Problem Statement

Financial institutions and payment processors process millions of credit card transactions daily. Detecting fraudulent attacks presents severe technical challenges:
1. **Extreme Class Imbalance**: Fraud typically accounts for less than $0.6\%$ of all transactions. Naive classifiers predicting 100% legitimate achieve $>99.4\%$ accuracy while failing completely at fraud prevention.
2. **Data Leakage & Overfitting**: Preprocessing whole datasets before temporal partitioning causes target and feature leakage, yielding inflated validation scores that collapse on unseen test data.
3. **The Arbitrary 0.5 Threshold Fallacy**: Standard classification pipelines use a default $0.5$ probability cutoff, resulting in either excessive false positives (blocking legitimate cardholders) or high false negatives (missing actual fraud losses).
4. **The "Black-Box" Problem**: Regulatory mandates (e.g. GDPR, FCRA, Dodd-Frank) require financial institutions to explain why a specific transaction was flagged or declined.
5. **Multi-Tenant Enterprise Isolation**: Enterprise platforms must host multiple institutional clients and organizations without cross-tenant data exposure.

---

## 2. Technical & Architecture Highlights

### Decoupled Full-Stack Architecture
- **Backend Core**: FastAPI asynchronous REST API with Pydantic v2 validation, dependency injection, and JWT Bearer authentication.
- **Frontend SPA**: React 18, TypeScript, Tailwind CSS, Lucide icons, and Recharts with responsive data grids and real-time state management.
- **Database & Storage Layer**: SQLAlchemy 2.0 async engine supporting PostgreSQL (`asyncpg`) and local zero-setup SQLite (`aiosqlite`) fallback.
- **Reporting Engine**: ReportLab PDF compiler utilizing a custom two-pass `NumberedCanvas` (`Page X of Y`), dynamic KPI grids, confusion matrix visualizers, and top risk queues.

---

## 3. Machine Learning & Data Science Highlights

| Dimension | Engineering Implementation |
|---|---|
| **Data Partitioning** | Chronological temporal splitting ensuring models only train on historical transactions and are evaluated on future transactions. |
| **Leak-Free Transformers** | Transformers (`RobustScaler`, `OneHotEncoder`, `SimpleImputer`) are fitted strictly on the training partition and applied to validation/test sets without re-fitting. |
| **Domain Feature Engineering** | Geodesic Haversine distances ($\text{km}$), cyclical hour/day sine-cosine encoding, night attack indicators ($23:00 - 06:00$), and logarithmic transaction amount scaling. |
| **Candidate Model Benchmarking** | Systematic comparison between **Random Forest**, **Logistic Regression**, and **XGBoost**. |
| **Threshold Optimization** | Exhaustive validation PR curve sweep maximizing $F_1$ score to identify the optimal boundary ($\tau^* = 0.8255$). |
| **Explainable AI (SHAP)** | TreeExplainer computing exact Shapley additive values on-demand to isolate positive risk escalators and negative risk mitigators. |

### Verified Real-World Benchmark Results
Evaluated against the Kaggle Credit Card Fraud Dataset ($1,296,675$ training rows and $555,719$ unseen holdout test rows):

- **Random Forest Validation PR-AUC**: **0.8817** (vs Baseline Logistic Regression: 0.2202)
- **Random Forest Validation ROC-AUC**: **0.9962** (vs Baseline Logistic Regression: 0.9561)
- **Unseen Test Set PR-AUC**: **0.8189**
- **Unseen Test Precision**: **80.24%**
- **Unseen Test Recall**: **75.52%** ($1,620$ out of $2,145$ fraud attacks intercepted)
- **Unseen Test False Positive Rate**: **0.07%** (only $399$ false alarms across $553,574$ legitimate transactions)

---

## 4. Key Engineering Decisions & Trade-Offs

### 1. Why PR-AUC Over ROC-AUC for Evaluation?
Under extreme class imbalance ($171:1$), ROC-AUC can be deceptive because a high number of True Negatives inflates the False Positive Rate denominator ($FPR = \frac{FP}{FP + TN}$), making a poorly calibrated model look artificially superior. PR-AUC directly balances Precision ($\frac{TP}{TP + FP}$) and Recall ($\frac{TP}{TP + FN}$), focusing purely on positive fraud identification.

### 2. Why Fit-on-Train Preprocessing?
Fitting scalers or encoders across the entire dataset before splitting leaks statistical properties (mean, standard deviation, category cardinality) of future test transactions into the training feature space. Sentinel AI encapsulates all transformations inside fit-on-train pipelines.

### 3. Why Deterministic Risk Scoring (0 - 100)?
Raw model probabilities often bunch in low decimal ranges (e.g. $0.001 - 0.05$) due to class priors. Sentinel AI scales probability into intuitive financial risk tiers:
- `LOW` ($0 - 20$): Auto-approved transactions.
- `MEDIUM` ($20 - 50$): Normal transactions requiring standard velocity checks.
- `HIGH` ($50 - 80$): Elevated risk flagged for fraud analyst review.
- `CRITICAL` ($80 - 100$): Urgent attacks intercepted above optimal decision threshold $\tau^*$.

### 4. Why Asynchronous SQLite with PostgreSQL Compatibility?
To enable seamless evaluation and local demonstration without forcing users to provision cloud database clusters or local Docker containers, Sentinel AI utilizes SQLAlchemy 2.0 with a dual-driver model: `postgresql+asyncpg` for production environments and `sqlite+aiosqlite` for zero-configuration local execution.

---

## 5. Verification & Test Evidence

The repository maintains an automated end-to-end test suite:

- **Backend Pytest Suite**: **72 passed, 0 failed** (`backend/tests`)
  - Verification of multi-tenant isolation, JWT RBAC security, leak-free ML transformers, model evaluation, SHAP explainability, and ReportLab PDF streaming.
- **Frontend Vitest Suite**: **7 passed, 0 failed** (`frontend/src/test`)
  - Component unit tests for StatCards, RiskBadges, Reports empty states, and API error extractors.
- **TypeScript Strict Compilation**: **0 errors** (`tsc --noEmit`).
- **Production Build**: Successful compilation into minified assets via Vite.

---

## 6. Interview Talking Points & Questions

### Q: "How does Sentinel AI handle explainability for fraud analysts?"
> *"Sentinel AI integrates TreeExplainer SHAP values at the single-transaction level. When an investigator opens the Investigation Drawer for an anomalous transaction, the system computes the exact additive contribution of each feature relative to the dataset base value. The investigator sees a waterfall chart showing exactly why the model escalated risk (e.g. +32% from transaction amount >$1,000 and +18% from high-risk distance) and what mitigated risk (e.g. -12% from familiar merchant category)."*

### Q: "How is multi-tenancy enforced across the database?"
> *"Every entity in the database (clients, datasets, analyses, transactions, reports, audit logs) is scoped to an `organization_id`. FastAPI dependency injection layers (`require_org_member`, `require_org_admin`) validate the incoming JWT against the requested URL parameters, ensuring users cannot query or mutate data outside their organization boundary."*

### Q: "What was the most challenging technical hurdle in this project?"
> *"Balancing high model recall with low false positive rates on heavily imbalanced financial data. By implementing precision-recall curve threshold sweeps on a chronologically separated validation set, we derived an optimal operating threshold ($\tau^* = 0.8255$) that captures 75.52% of all fraud attacks while maintaining a 0.07% false positive rate across over half a million unseen transactions."*
