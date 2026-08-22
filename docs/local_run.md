# Sentinel AI — Localhost Execution & Operations Guide

This guide provides simple, step-by-step instructions for running Sentinel AI completely on your local machine.

---

## 1. System Prerequisites

- **Python**: Python 3.10+ (Python 3.13 supported)
- **Node.js**: Node.js v18+ and `npm`
- **Operating System**: Windows / macOS / Linux
- **No External Databases Required**: The application is database-free and operates entirely with an in-memory session store.

---

## 2. Dataset Setup

Place your raw credit card transaction dataset in the `data/raw/` directory:

```
data/raw/
├── fraudTrain.csv    (Primary training and demonstration dataset)
└── fraudTest.csv     (Holdout chronological test dataset)
```

The dataset can be obtained from the [Kaggle Credit Card Fraud Detection Dataset (Simulated)](https://www.kaggle.com/datasets/kartik2112/fraud-detection).

---

## 3. Starting the Backend API Server

Open a terminal in the project root directory (`Sentinel AI/`):

```powershell
# 1. (Optional) Activate your virtual environment if one is used
# 2. Run the FastAPI backend server with Uvicorn
py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Backend Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 4. Starting the React Frontend

Open a second terminal in the `frontend/` directory:

```powershell
cd frontend
npm install   # Run once to install dependencies
npm run dev
```

- **Frontend Application URL**: [http://localhost:5173](http://localhost:5173)

The Vite development server automatically proxies API requests (`/api/*` and `/health`) to `http://127.0.0.1:8000`.

---

## 5. End-to-End User Workflow

1. **Upload Dataset**:
   - Navigate to [http://localhost:5173/upload](http://localhost:5173/upload).
   - Drag and drop `fraudTrain.csv` (or any valid CSV transaction export).
   - Review the pre-flight structural inspection (row count, target variable detection, class imbalance ratio, missing cells).
2. **Execute Analysis**:
   - Click **"Run Fraud Analysis"**.
   - The multi-stage progress banner tracks partition ingestion, preprocessing, candidate classifier training, threshold optimization, and risk scoring.
3. **Explore Dashboard**:
   - **Overview (`/`)**: Executive KPIs, Risk Tier Distribution (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), Category Loss Bar Charts, 10-bin Risk Score Histogram, and Top Predictive Feature rankings.
   - **Transactions Explorer (`/transactions`)**: Server-side paginated and filtered table. Filter by Risk Band, Actual Fraud status, or amount range.
4. **Investigate Transactions & SHAP Explainability**:
   - Click any transaction row in the table or search by ID in `/investigation`.
   - The slide-in **Investigation Drawer** renders local SHAP feature attributions separating risk-escalating factors (red) from risk-mitigating factors (green).
5. **Generate & Download PDF Audit Report**:
   - Navigate to [http://localhost:5173/reports](http://localhost:5173/reports).
   - Click **"Generate PDF Audit Report"**.
   - An executive multi-page audit report complete with embedded charts, model benchmark matrices, and zero PII leakage downloads directly to your machine.

---

## 6. Running Automated Tests

### Backend Test Suite (Pytest)
From project root:
```powershell
py -m pytest backend/tests -v
```

### Frontend Test Suite (Vitest)
From `frontend/` directory:
```powershell
cd frontend
npm test
```

### Frontend Production Build Verification
From `frontend/` directory:
```powershell
cd frontend
npm run build
```

---

## 7. Common Issues & Troubleshooting

| Issue | Cause | Resolution |
|---|---|---|
| **CORS error in browser console** | Backend is not running on port 8000 | Ensure FastAPI backend is started on `http://127.0.0.1:8000`. |
| **"Analysis session no longer exists" (404)** | In-memory session expired (TTL) or server restarted | Re-upload the CSV from the `/upload` page to initialize a new session. |
| **"Target column contains only one class" (422)** | Uploaded CSV has no fraud examples | Ensure the uploaded dataset contains both legitimate (`0`) and fraudulent (`1`) examples. |
| **PDF download does not trigger** | Pop-up blocker or session expired | Check the notification message on the Reports page; re-run analysis if session has expired. |
