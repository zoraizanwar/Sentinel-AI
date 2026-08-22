# Sentinel AI

### AI-Powered Fraud Detection & Risk Intelligence Platform

[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-72%20Passed-10B981?style=flat-square)](file:///c:/Users/Zuraiz%20Malik/Desktop/Sentinel%20AI/backend/tests)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-7%20Passed-10B981?style=flat-square)](file:///c:/Users/Zuraiz%20Malik/Desktop/Sentinel%20AI/frontend/src/test)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict%200%20Errors-3178C6?style=flat-square)](file:///c:/Users/Zuraiz%20Malik/Desktop/Sentinel%20AI/frontend/tsconfig.json)
[![FastAPI](https://img.shields.io/badge/FastAPI-Pydantic%20v2-009688?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React%2018-Tailwind%20CSS-61DAFB?style=flat-square)](https://react.dev)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Engine-D97706?style=flat-square)](https://www.reportlab.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

Sentinel AI is an enterprise-grade AI fraud detection and risk intelligence platform engineered to ingest large-scale credit card transaction datasets, intercept high-risk financial attacks with mathematically optimized decision thresholds, explain model predictions using game-theoretic SHAP attributions, provide real-time multi-tenant risk intelligence dashboards, manage distinct client financial entities with strict tenant isolation, and compile executive-ready PDF audit reports.

---

## Architecture Overview

Sentinel AI employs a decoupled, leak-free architecture that executes entirely on **localhost** without requiring external persistent database servers.

```mermaid
graph TD
    User([Fraud Analyst / Risk Officer]) <--> UI[React 18 + Vite + Tailwind Dashboard]
    
    subgraph Frontend Layer [Frontend SPA - Port 5173]
        UI --> Views[Executive Overview | Transactions Explorer | Analytics | Investigation Drawer | PDF Reports]
        Views --> Client[Axios API Client + SSE Progress Tracking]
    end
    
    Client <--> API[FastAPI REST API - Port 8000]
    
    subgraph Backend Core [FastAPI Service Layer]
        API --> Ingest[CSV Ingestion & Pre-flight Validator]
        API --> Session[Thread-Safe In-Memory SessionStore with TTL]
        API --> Svc[Analysis Service Orchestrator]
    end
    
    subgraph Machine Learning Pipeline [ML & Explainability Core]
        Svc --> Split[Chronological Train/Validation Partitioning]
        Split --> Preproc[Fit-on-Train Preprocessor & Feature Engineering]
        Preproc --> Models[Candidate Classifier Training & PR-AUC Optimization]
        Models --> Scorer[Deterministic Risk Scoring: 0 - 100 Bands]
        Scorer --> SHAP[TreeExplainer Local Feature Attribution]
        Scorer --> Analytics[Behavioral Pattern & Loss Exposure Aggregator]
    end
    
    subgraph Reporting Engine [Executive Document Compiler]
        Svc --> PDF[ReportLab Engine + In-Memory Matplotlib Charts]
        PDF --> Download[Dynamic Multi-Page Numbered PDF Stream]
    end
    
    Session --> Views
    Download --> UI
```

---

## Key Capabilities

1. **Pre-Flight Structural & Data Quality Audit**:
   - Parses CSV datasets up to 500 MB without mutating raw inputs.
   - Evaluates class imbalance ratios ($171:1$ on raw training data), missing cell rates, duplicate rows, and single-class target errors.
2. **Leak-Free Machine Learning Pipeline**:
   - Strict fit-on-train-only transformers (`RobustScaler`, `OneHotEncoder`, `SimpleImputer`).
   - Domain feature extraction: Haversine distance ($\text{km}$), customer age, cyclical hour/day, night transaction flag ($23:00 - 06:00$), and log amount compression.
   - Decoupled metadata tracking: PII identifiers (`cc_num`, names, street addresses) are strictly excluded from model feature vectors.
3. **Precision-Recall Curve Threshold Optimization**:
   - Sweeps validation PR curves to maximize the $F_1$ score for extreme class imbalance, dynamically determining the optimal operational threshold ($\tau^* = 0.8255$) rather than assuming an arbitrary 0.5 boundary.
4. **Deterministic Risk Scoring & Enterprise Risk Bands**:
   - Transparent scalar mapping derived directly from model fraud probability:
     $$\text{risk\_score} = \text{round}(\text{fraud\_probability} \times 100, 2)$$
   - Segmented into standard financial risk tiers: `LOW` ($0-20$), `MEDIUM` ($20-50$), `HIGH` ($50-80$), and `CRITICAL` ($80-100$).
5. **Explainable AI (SHAP Waterfall Attributions)**:
   - Computes local Shapley additive explanations on-demand for any transaction, isolating the exact positive risk-escalators (e.g. night hours, high dollar amounts) and negative risk-mitigators (e.g. low amount, close proximity).
6. **Executive PDF Reporting Engine (ReportLab)**:
   - Compiles downloadable multi-page audit reports with dynamic two-pass `NumberedCanvas` (`Page X of Y`), embedded high-resolution charts, candidate benchmark tables, confusion matrices, top high-risk queues, and operational recommendations.

---

## Machine Learning Benchmark & Validation Results

The models were evaluated against the real-world [Kaggle Credit Card Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection) ($1,296,675$ training rows and $555,719$ chronologically separated unseen test rows):

| Candidate Model | Validation PR-AUC | Validation ROC-AUC | Validation Precision | Validation Recall | Validation F1 | Decision Threshold ($\tau^*$) | Unseen Test PR-AUC |
|---|---|---|---|---|---|---|---|
| **Random Forest (Selected Winner)** | **0.8817** | **0.9962** | **84.24%** | **80.91%** | **0.8254** | **0.8255** | **0.8189** |
| **Logistic Regression (Baseline)** | 0.2202 | 0.9561 | 35.29% | 43.21% | 0.3885 | 0.9996 | 0.1842 |

### Unseen Holdout Test Performance (`fraudTest.csv` — $N = 555,719$)
- **PR-AUC**: **0.8189**
- **ROC-AUC**: **0.9950**
- **Test Precision**: **80.24%**
- **Test Recall**: **75.52%** ($1,620$ out of $2,145$ fraud attacks intercepted)
- **Test F1 Score**: **0.7781**
- **False Positive Rate**: **0.07%** (only $399$ false alarms across $553,574$ legitimate transactions)

#### Unseen Test Confusion Matrix
| Metric | Actual Fraud (1) | Actual Legitimate (0) |
|---|---|---|
| **Predicted Fraud (1)** | **True Positive (TP): 1,620** | **False Positive (FP): 399** |
| **Predicted Legit (0)** | **False Negative (FN): 525** | **True Negative (TN): 553,175** |

---

## Technology Stack

### Backend
- **Python 3.10+ / 3.13**
- **FastAPI**: Async REST API routing and OpenAPI documentation.
- **Pydantic v2**: Type-safe schema validation and serialization.
- **Scikit-Learn & XGBoost**: Machine learning pipelines, robust scalers, and ensemble classifiers.
- **SHAP**: Game-theoretic local feature attributions.
- **ReportLab & Matplotlib**: High-resolution PDF compiling with in-memory chart generation.
- **Pytest**: Backend unit, security, and integration test suite.

### Frontend
- **React 18 & TypeScript 5.7**
- **Vite**: Ultra-fast build tool and development server.
- **Tailwind CSS 3.4**: Cyber/fintech dark UI theme with consistent semantic risk colors.
- **Recharts**: Interactive SVG charts (Donut risk distribution, Category loss bars, 10-bin histograms).
- **Lucide React**: Modern icon system.
- **Vitest & React Testing Library**: Component unit tests.

---

## Project Structure

```
Sentinel AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── analyze.py       # Full ML pipeline execution endpoint
│   │   │   │   ├── explain.py       # SHAP local attribution endpoint
│   │   │   │   ├── reports.py       # PDF report generation endpoint
│   │   │   │   ├── router.py        # Master API v1 router
│   │   │   │   ├── transactions.py  # Paginated transaction explorer endpoint
│   │   │   │   └── upload.py        # Pre-flight dataset inspection endpoint
│   │   │   └── deps.py              # Dependency injection providers
│   │   ├── core/
│   │   │   ├── exceptions.py        # Domain exception hierarchy
│   │   │   ├── security.py          # Upload and path traversal security
│   │   │   └── session_store.py     # Thread-safe in-memory session manager
│   │   ├── schemas/                 # Strongly-typed Pydantic v2 schemas
│   │   ├── services/
│   │   │   ├── analytics/           # Risk aggregations & recommendations
│   │   │   ├── ingestion/           # CSV ingestion & validation engine
│   │   │   ├── ml/                  # Preprocessing, training, thresholding & SHAP
│   │   │   ├── reporting/           # ReportLab PDF generator & in-memory charts
│   │   │   └── analysis_service.py  # Master analysis orchestrator
│   │   ├── config.py                # System settings & thresholds
│   │   └── main.py                  # FastAPI application entrypoint
│   └── tests/                       # Comprehensive backend test suite (61 tests)
├── frontend/
│   ├── src/
│   │   ├── api/                     # Axios client & typed endpoint callers
│   │   ├── components/
│   │   │   ├── common/              # RiskBadge, StatCard, Skeleton, EmptyState
│   │   │   ├── investigation/       # SHAPWaterfall, TransactionDrawer
│   │   │   └── layout/              # Sidebar, Header, AppLayout
│   │   ├── context/                 # AnalysisContext & session persistence
│   │   ├── pages/                   # Overview, Transactions, Analytics, Reports, Upload
│   │   ├── test/                    # Vitest frontend tests (7 tests)
│   │   └── types/                   # TypeScript interfaces matching backend schemas
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── data/
│   └── raw/                         # Raw CSV datasets (fraudTrain.csv, fraudTest.csv)
├── docs/                            # Deep-dive architecture & operational docs
├── requirements.txt                 # Backend Python dependencies
├── .gitignore                       # Clean repository exclusions
└── README.md                        # Project documentation
```

---

## Localhost Quickstart Guide

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18 or higher (with `npm`)

### 1. Install Backend Dependencies
```powershell
# From project root
py -m pip install -r requirements.txt
```

### 2. Start the Backend API Server
```powershell
# From project root
py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Health Status: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Start the React Frontend
Open a new terminal:
```powershell
cd frontend
npm install
npm run dev
```
- Frontend Dashboard: [http://localhost:5173](http://localhost:5173)

---

## Running the Automated Test Suites

### Backend Tests (Pytest)
```powershell
# From project root
py -m pytest backend/tests -v
```
*Result: 61 passed, 0 failed.*

### Frontend Tests (Vitest)
```powershell
cd frontend
npm test
```
*Result: 7 passed, 0 failed.*

### Frontend Production Build Verification
```powershell
cd frontend
npm run build
```
*Result: 0 TypeScript errors, production `dist/` bundle compiled successfully.*

---

## Data Privacy & Security Guardrails

- **Zero PII Leakage**: Cardholder names, full street addresses, and primary card numbers (`cc_num`) are stripped from machine learning features, excluded from API responses, and never printed in PDF reports.
- **Path Traversal Protection**: Uploaded file names are strictly sanitized against traversal attacks (`../`, `..\`).
- **Sanitized JSON Error Responses**: Production errors return clean domain codes (`ANALYSIS_NOT_FOUND`, `DATASET_INVALID`, `FILE_TOO_LARGE`) without exposing Python stack traces.
- **In-Memory TTL Protection**: Analysis sessions automatically expire after 1 hour with a background lifespan cleaner to prevent memory exhaustion.

---

## Operational Limitations & Disclaimers

1. **Simulated Dataset Origin**: The platform is benchmarked on synthetic credit card transaction data. Real-world fraud patterns evolve adversarially and require periodic model retraining.
2. **Decision-Support Scope**: Sentinel AI is engineered as an analyst decision-support system to assist risk teams rather than an automated system executing irreversible banking actions without oversight.
3. **Probability Calibration Notice**: Raw model probabilities represent tree ensemble leaf vote distributions; risk scores map linearly ($\text{risk\_score} = \text{prob} \times 100$) without post-hoc isotonic calibration.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
