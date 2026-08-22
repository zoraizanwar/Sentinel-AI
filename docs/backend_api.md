# Sentinel AI — Backend REST API Documentation

## 1. API Architecture Overview

The Sentinel AI backend is engineered with **FastAPI** (Python 3.13 + Pydantic v2), strictly decoupled from persistent databases for the MVP. It operates over a high-performance **in-memory session architecture (`SessionStore`)** with automated TTL expiration, powering fast interactive analysis, multi-criteria transaction exploration, and on-demand local explainability (SHAP).

- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive Documentation**:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`
  - OpenAPI Specification: `http://localhost:8000/openapi.json`

---

## 2. API Endpoint Matrix

| Method | Endpoint | Description | Request Payload | Response Model | HTTP Status Codes |
|---|---|---|---|---|---|
| `GET` | `/health` | Service health status | None | `HealthResponse` | `200 OK` |
| `POST` | `/api/v1/dataset/inspect` | Pre-flight dataset inspection & data quality audit | `multipart/form-data` (CSV) | `DatasetInspectionResult` | `200 OK`, `400 Bad Request`, `413 File Too Large` |
| `POST` | `/api/v1/analysis/run` | End-to-end ML training, threshold tuning & risk analytics | `multipart/form-data` (CSV) | `AnalysisResult` | `200 OK`, `400 Bad Request`, `413 File Too Large`, `422 Invalid Dataset` |
| `GET` | `/api/v1/analysis/{analysis_id}` | Retrieve single-source-of-truth analysis result | None | `AnalysisResult` | `200 OK`, `404 Not Found` |
| `GET` | `/api/v1/analysis/{analysis_id}/transactions` | Server-side paginated, sorted & filtered transaction explorer | Query params (`page`, `page_size`, `risk_band`, `min_amount`, etc.) | `PaginatedTransactionsResponse` | `200 OK`, `404 Not Found` |
| `GET` | `/api/v1/analysis/{analysis_id}/transactions/{tx_id}/explain` | On-demand local SHAP attribution & risk factors | None | `LocalExplanation` | `200 OK`, `404 Not Found`, `500 Explain Error` |
| `POST` | `/api/v1/analysis/{analysis_id}/report/pdf` | PDF executive audit report generation | None | Binary PDF Stream (`application/pdf`) | `200 OK`, `404 Not Found` |

---

## 3. Detailed Endpoint Specifications

### 1. Health Check
- **`GET /health`**
- **Response**:
```json
{
  "status": "healthy",
  "service": "sentinel-ai",
  "version": "1.0.0"
}
```

---

### 2. Pre-flight Dataset Inspection
- **`POST /api/v1/dataset/inspect`**
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file: UploadFile` (.csv)
- **Response** (`DatasetInspectionResult`):
```json
{
  "dataset_name": "fraudTrain.csv",
  "file_size_bytes": 351238196,
  "row_count": 1296675,
  "column_count": 23,
  "target_column": "is_fraud",
  "validation_status": "WARNINGS",
  "errors": [],
  "warnings": [
    {
      "severity": "WARNING",
      "code": "SEVERE_CLASS_IMBALANCE",
      "message": "Severe class imbalance detected in target 'is_fraud': 7,506 fraud cases (0.579%) vs 1,289,169 legitimate (171.75:1 ratio).",
      "column": "is_fraud"
    }
  ],
  "class_distribution": {
    "target_column": "is_fraud",
    "total_count": 1296675,
    "legitimate_count": 1289169,
    "fraud_count": 7506,
    "fraud_percentage": 0.578865,
    "imbalance_ratio": 171.75,
    "is_single_class": false,
    "is_severely_imbalanced": true
  }
}
```

---

### 3. Run Full Fraud Analysis
- **`POST /api/v1/analysis/run`**
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file: UploadFile` (.csv)
- **Response** (`AnalysisResult`): Returns the complete Single Source of Truth analysis result containing dataset summary, data quality metrics, fraud statistics, model evaluation summaries, 10-bin risk score histograms, categorical breakdowns, empirical findings, and operational recommendations.

---

### 4. Retrieve Analysis Result
- **`GET /api/v1/analysis/{analysis_id}`**
- **Response** (`AnalysisResult`): Fetches the precomputed analysis result by UUID.

---

### 5. Server-Side Transactions Explorer
- **`GET /api/v1/analysis/{analysis_id}/transactions`**
- **Query Parameters**:
  - `page`: int (default: 1)
  - `page_size`: int (default: 25, max: 100)
  - `sort_by`: str (e.g. `risk_score`, `amt`, `trans_date_trans_time`)
  - `sort_order`: `asc` | `desc` (default: `desc`)
  - `risk_band`: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
  - `is_fraud`: 0 | 1
  - `min_amount` / `max_amount`: float
  - `search`: string (matches merchant, category, city, state, or transaction ID)
- **Response** (`PaginatedTransactionsResponse`): Returns filtered array of transactions with pagination metadata.

---

### 6. On-Demand SHAP Explanation
- **`GET /api/v1/analysis/{analysis_id}/transactions/{tx_id}/explain`**
- **Response** (`LocalExplanation`):
```json
{
  "transaction_id": "16bf2e46c54369a8eab2214649506425",
  "fraud_probability": 0.9421,
  "risk_score": 94.21,
  "risk_band": "CRITICAL",
  "base_value": 0.0058,
  "positive_contributions": [
    {
      "feature_name": "amt",
      "feature_value": "948.25",
      "shap_value": 0.3842,
      "contribution_type": "RISK_INCREASING",
      "human_explanation": "Transaction amount of $948.25 increased fraud risk score by 0.384."
    }
  ],
  "negative_contributions": [],
  "method": "TreeExplainer",
  "is_cached": false
}
```

---

### 7. PDF Report Generation & Download
- **`POST /api/v1/analysis/{analysis_id}/report/pdf`**
- **Response**: Binary PDF Stream (`application/pdf`)
- **Headers**: `Content-Disposition: attachment; filename="sentinel_ai_fraud_intelligence_report_{analysis_id}.pdf"`

---

## 4. In-Memory Session Architecture & Lifecycle

- **Thread-Safety**: Managed via `threading.RLock` in `SessionStore`.
- **Keying**: Cryptographically secure `UUID4` generated per analysis.
- **TTL Expiration**: Configured via `SESSION_TTL_SECONDS` (default: 3,600s = 1 hour).
- **Background Cleaner**: An async worker runs via FastAPI lifespan every 5 minutes to prune expired sessions and reclaim memory.
- **Decoupled Architecture**: Zero database dependencies (no PostgreSQL, no Redis, no SQLite).

---

## 5. Security & Error Handling Hierarchy

| Custom Exception | HTTP Status | Response Error Code | Client Description |
|---|---|---|---|
| `FileValidationError` | `400 Bad Request` / `413 File Too Large` | `FILE_VALIDATION_ERROR` / `FILE_TOO_LARGE` | Invalid file type or file exceeds 500 MB limit. |
| `IngestionError` | `400 Bad Request` | `INGESTION_ERROR` | Corrupt CSV or unparseable encodings. |
| `DatasetValidationError` | `422 Unprocessable Entity` | `DATASET_VALIDATION_ERROR` | Single-class target, missing target, or insufficient rows. |
| `AnalysisNotFoundError` | `404 Not Found` | `ANALYSIS_NOT_FOUND` | Analysis session ID does not exist or expired. |
| `TransactionNotFoundError`| `404 Not Found` | `TRANSACTION_NOT_FOUND` | Transaction ID not in session. |
| `ExplainabilityError` | `500 Internal Error` | `EXPLAINABILITY_ERROR` | Error computing SHAP attribution. |
| Unhandled Exceptions | `500 Internal Error` | `INTERNAL_SERVER_ERROR` | Masked generic error without internal stack traces. |
