# Sentinel AI — System Architecture & Technical Specification

## 1. High-Level Architecture Overview

Sentinel AI is engineered as a decoupled, multi-tenant AI fraud detection and risk intelligence platform running locally. It provides leak-free machine learning pipelines, post-training threshold optimization, transaction-level SHAP explainability, fine-grained Role-Based Access Control (RBAC), multi-client portfolio management, append-only security audit logging, and executive PDF report generation.

```mermaid
graph TD
    subgraph ClientLayer ["Client Layer (Browser SPA)"]
        User["Security Analyst / Risk Officer"]
        SPA["React 18 + Vite + Tailwind CSS"]
        State["Context Layer (Auth, Workspace, Analysis)"]
        Axios["Axios API Client (JWT Bearer Auth)"]
        User --> SPA
        SPA --> State
        State --> Axios
    end

    subgraph APILayer ["API & Security Gateway (FastAPI)"]
        Gateway["FastAPI Application Router (Port 8001)"]
        AuthMiddleware["JWT Authentication & RBAC Interceptor"]
        TenantGuard["Tenant Isolation & Client Scope Enforcer"]
        AuditLogger["Append-Only Audit Event Dispatcher"]
        
        Axios <-->|"HTTP / REST (JSON + Multipart)"| Gateway
        Gateway --> AuthMiddleware
        AuthMiddleware --> TenantGuard
        TenantGuard --> AuditLogger
    end

    subgraph ServiceLayer ["Core Service Orchestration"]
        OrgService["Organization & Member Service"]
        ClientService["Client Portfolio Service"]
        IngestService["Dataset Ingestion & Validation Service"]
        MLService["Machine Learning & Inference Pipeline"]
        ExplainService["SHAP Explainability Engine"]
        ReportService["ReportLab Executive PDF Engine"]
    end

    subgraph PersistenceLayer ["Database & Storage Engine"]
        AsyncEngine["SQLAlchemy 2.0 Async Engine"]
        DB[("PostgreSQL / SQLite Database")]
        FileStore["Local Dataset & PDF Repository (data/)"]
    end

    TenantGuard --> OrgService
    TenantGuard --> ClientService
    TenantGuard --> IngestService
    TenantGuard --> MLService
    TenantGuard --> ExplainService
    TenantGuard --> ReportService

    OrgService --> AsyncEngine
    ClientService --> AsyncEngine
    IngestService --> FileStore
    IngestService --> AsyncEngine
    MLService --> AsyncEngine
    ExplainService --> MLService
    ReportService --> FileStore
    ReportService --> AsyncEngine
    AsyncEngine <--> DB
```

---

## 2. Multi-Tenancy & Data Isolation Model

Sentinel AI enforces strict multi-tenant isolation across all entities in the platform. No user or organization can access, inspect, or query datasets, analyses, transactions, or audit logs belonging to another organization.

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER_MEMBERSHIP : has
    USER ||--o{ USER_MEMBERSHIP : belongs_to
    ORGANIZATION ||--o{ CLIENT : manages
    CLIENT ||--o{ DATASET : uploads
    CLIENT ||--o{ ANALYSIS : executes
    ANALYSIS ||--o{ TRANSACTION : generates
    ANALYSIS ||--o{ REPORT : produces
    ORGANIZATION ||--o{ AUDIT_LOG : records

    ORGANIZATION {
        string id PK
        string name
        string slug
        datetime created_at
    }

    USER {
        string id PK
        string email UK
        string password_hash
        string full_name
        boolean is_active
    }

    USER_MEMBERSHIP {
        string id PK
        string user_id FK
        string organization_id FK
        enum role "ADMIN | ANALYST | VIEWER"
    }

    CLIENT {
        string id PK
        string organization_id FK
        string client_code UK
        string name
        string industry
    }

    DATASET {
        string id PK
        string organization_id FK
        string client_id FK
        string filename
        int row_count
        int column_count
        float fraud_rate_percentage
        enum status "VALIDATED | INVALID | ANALYZED"
    }

    ANALYSIS {
        string id PK
        string organization_id FK
        string client_id FK
        string dataset_id FK
        string model_name
        float optimal_threshold
        float execution_time_seconds
        json fraud_statistics
        json risk_statistics
        json validation_metrics
        json test_metrics
    }
```

### Role-Based Access Control (RBAC) Matrix

| Permission / Action | ORGANIZATION_ADMIN | ANALYST | VIEWER |
|---|:---:|:---:|:---:|
| View Organization & Client Dashboards | ✅ | ✅ | ✅ |
| View Historical Analyses & Transactions | ✅ | ✅ | ✅ |
| Run SHAP Transaction Explainability | ✅ | ✅ | ✅ |
| Download PDF Audit Reports | ✅ | ✅ | ✅ |
| Upload CSV Datasets | ✅ | ✅ | ❌ |
| Run Machine Learning Analyses | ✅ | ✅ | ❌ |
| Generate New Audit Reports | ✅ | ✅ | ❌ |
| Create / Edit Clients | ✅ | ✅ | ❌ |
| Invite Members & Assign Roles | ✅ | ❌ | ❌ |
| View Security Audit Logs | ✅ | ❌ | ❌ |

---

## 3. Machine Learning Architecture & Leak-Free Pipeline

```mermaid
flowchart TD
    RawCSV["Raw CSV Dataset (data/uploads)"] --> Ingest["1. Pre-Flight Structural & Imbalance Inspection"]
    Ingest --> Clean["2. Target Extraction & PII Exclusion"]
    Clean --> Partition["3. Chronological Train / Val / Test Partitioning"]
    
    subgraph FitOnTrainOnly ["Fit-on-Train Preprocessing (Zero Leakage)"]
        Partition --> Fit["Fit Feature Transformers on Training Set Only"]
        Fit --> Scale["RobustScaler (Numeric Amounts & Distances)"]
        Fit --> Enc["OneHotEncoder (handle_unknown='ignore')"]
        Fit --> Geo["Haversine Geodesic Distance Extraction"]
        Fit --> Time["Cyclical Hour / Day & Night Flag Extraction"]
    end

    Scale --> Transform["Transform Training, Validation, and Test Sets"]
    Enc --> Transform
    Geo --> Transform
    Time --> Transform

    subgraph ModelTraining ["Candidate Model Benchmarking"]
        Transform --> RF["Train Random Forest Classifier"]
        Transform --> LR["Train Logistic Regression Baseline"]
        Transform --> XGB["Train XGBoost Classifier"]
    end

    RF --> Evaluate["4. Precision-Recall AUC & ROC-AUC Validation"]
    LR --> Evaluate
    XGB --> Evaluate

    Evaluate --> Winner["5. Select Top Classifier (Random Forest Winner)"]
    Winner --> ThreshOpt["6. Precision-Recall Curve F1 Threshold Sweep (tau* = 0.8255)"]
    ThreshOpt --> Holdout["7. Evaluate on Chronologically Unseen Test Set (555,719 rows)"]
    Holdout --> Scorer["8. Deterministic Risk Scoring & Tier Segmentation (0 - 100)"]
    Scorer --> SHAPCore["9. SHAP TreeExplainer Local Feature Attribution Engine"]
```

---

## 4. End-to-End Request Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as Fraud Analyst
    participant Frontend as React SPA (Port 5173)
    participant API as FastAPI Router (Port 8001)
    participant Auth as Auth & RBAC Middleware
    participant ML as Persistent ML Service
    participant DB as SQLite / PostgreSQL

    Analyst->>Frontend: Select Client & Upload Dataset
    Frontend->>API: POST /organizations/{org_id}/clients/{client_id}/datasets/upload
    API->>Auth: Validate JWT & Verify ANALYST/ADMIN Role
    Auth-->>API: Authorized
    API->>DB: Store Dataset Metadata & Raw File Path
    DB-->>Frontend: Dataset Created (ID: dt_123, Status: VALIDATED)

    Analyst->>Frontend: Click "Execute ML Fraud Analysis"
    Frontend->>API: POST /organizations/{org_id}/clients/{client_id}/datasets/{dataset_id}/analyze
    API->>ML: Run Leak-Free Partitioning, Model Benchmarking & Threshold Sweep
    ML->>DB: Persist Model Artifacts, Metrics, Risk Bands & Scored Transactions
    DB-->>Frontend: Analysis Complete (ID: an_456, Selected: Random Forest)

    Analyst->>Frontend: Inspect Individual High-Risk Transaction
    Frontend->>API: GET /organizations/{org_id}/analyses/{analysis_id}/transactions/{tx_id}/explain
    API->>ML: Compute Local SHAP Attributions (TreeExplainer)
    ML-->>Frontend: Return Base Value, Feature Contributions & Escalators

    Analyst->>Frontend: Click "Generate Executive PDF Audit Report"
    Frontend->>API: POST /organizations/{org_id}/reports/generate
    API->>DB: Compile Analysis KPIs, Confusion Matrix & Recommendations into PDF
    API-->>Frontend: Binary PDF Stream (NumberedCanvas, Multi-Page)
```

---

## 5. Security & Governance Boundaries

1. **Authentication & Token Lifecycle**:
   - Cryptographically signed JSON Web Tokens (HS256) with configurable TTL (`ACCESS_TOKEN_EXPIRE_MINUTES=480`).
   - Passwords hashed using standard `bcrypt` with adaptive cost parameters.
2. **Tenant Boundary Enforcement**:
   - Every database query dynamically joins against `organization_id`.
   - FastAPI dependencies (`require_org_member`, `require_org_admin`, `require_org_analyst`) verify membership before routing to business logic.
3. **PII and Data Protection**:
   - High-risk identifiers (`cc_num`, `first`, `last`, `street`, `dob`) are stripped before vectorization and never stored in model artifacts.
4. **Append-Only Audit Logging**:
   - Every state-changing operational action (`USER_REGISTERED`, `LOGIN_SUCCESS`, `CLIENT_CREATED`, `DATASET_UPLOADED`, `ANALYSIS_STARTED`, `REPORT_GENERATED`, `MEMBER_ADDED`) writes an immutable audit record containing timestamp, acting user ID, organization ID, action name, and metadata details.
