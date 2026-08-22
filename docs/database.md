# Database Schema & Persistence

## Overview
Sentinel AI uses asynchronous SQLAlchemy 2.0 with `asyncpg` for production PostgreSQL and `aiosqlite` for local developer testing. Schema migrations are managed through Alembic.

## Entity Relational Schema

### 1. `users`
- `id` (UUID, Primary Key)
- `email` (String, Unique Index)
- `hashed_password` (String)
- `full_name` (String)
- `is_active` (Boolean, Default: True)
- `created_at`, `updated_at` (DateTime)

### 2. `organizations`
- `id` (UUID, Primary Key)
- `name` (String)
- `slug` (String, Unique Index)
- `created_at`, `updated_at` (DateTime)

### 3. `organization_members`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `role` (Enum: `ORGANIZATION_ADMIN`, `ANALYST`, `VIEWER`)
- `joined_at` (DateTime)
- Unique Constraint: `(organization_id, user_id)`

### 4. `clients`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`, Index)
- `client_code` (String, Index)
- `name` (String)
- `industry` (String, Optional)
- `contact_email` (String, Optional)
- `status` (Enum: `ACTIVE`, `ARCHIVED`)
- `created_at`, `updated_at` (DateTime)
- Unique Constraint: `(organization_id, client_code)`

### 5. `datasets`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`, Index)
- `client_id` (UUID, Foreign Key -> `clients.id`, Index)
- `uploaded_by_user_id` (UUID, Foreign Key -> `users.id`)
- `filename` (String)
- `file_path` (String)
- `file_size_bytes` (BigInteger)
- `row_count` (Integer)
- `column_count` (Integer)
- `has_target` (Boolean)
- `target_column_name` (String, Optional)
- `fraud_rate_percentage` (Float, Optional)
- `validation_summary` (JSON)
- `validation_status` (Enum: `VALID`, `WARNINGS`, `INVALID`)
- `processing_status` (Enum: `PENDING`, `VALIDATED`, `ANALYZED`, `FAILED`)
- `created_at`, `updated_at` (DateTime)

### 6. `analyses`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`, Index)
- `client_id` (UUID, Foreign Key -> `clients.id`, Index)
- `dataset_id` (UUID, Foreign Key -> `datasets.id`, Index)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `model_name` (String)
- `optimal_threshold` (Float)
- `execution_time_seconds` (Float)
- `validation_metrics` (JSON)
- `test_metrics` (JSON)
- `fraud_statistics` (JSON)
- `risk_statistics` (JSON)
- `feature_importance` (JSON)
- `status` (Enum: `RUNNING`, `COMPLETED`, `FAILED`)
- `created_at`, `updated_at` (DateTime)

### 7. `transactions`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`, Index)
- `client_id` (UUID, Foreign Key -> `clients.id`, Index)
- `analysis_id` (UUID, Foreign Key -> `analyses.id`, Index)
- `transaction_id` (String, Index)
- `amount` (Float)
- `timestamp` (String, Optional)
- `category` (String, Optional)
- `merchant` (String, Optional)
- `city` (String, Optional)
- `state` (String, Optional)
- `fraud_probability` (Float)
- `risk_score` (Float)
- `risk_band` (Enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `is_fraud_pred` (Integer)
- `is_fraud_actual` (Integer, Optional)
- `created_at` (DateTime)
- Composite Performance Indexes:
  - `(analysis_id, risk_score)`
  - `(analysis_id, risk_band)`
  - `(analysis_id, amount)`
  - `(analysis_id, is_fraud_pred)`
  - `(organization_id, client_id, analysis_id)`

### 8. `reports`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`, Index)
- `client_id` (UUID, Foreign Key -> `clients.id`, Optional)
- `analysis_id` (UUID, Foreign Key -> `analyses.id`, Optional)
- `created_by_user_id` (UUID, Foreign Key -> `users.id`)
- `report_type` (Enum: `ORGANIZATION`, `CLIENT`, `ANALYSIS`)
- `title` (String)
- `filename` (String)
- `file_path` (String)
- `file_size_bytes` (BigInteger)
- `created_at` (DateTime)

### 9. `audit_logs`
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Foreign Key -> `organizations.id`, Index)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `action` (String, Index)
- `resource_type` (String, Index)
- `resource_id` (String, Optional)
- `details` (JSON, Optional)
- `ip_address` (String, Optional)
- `created_at` (DateTime, Index)

## Alembic Migrations
Run database schema migrations locally:
```bash
alembic upgrade head
```
