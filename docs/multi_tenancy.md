# Multi-Tenancy Architecture

## Overview
Sentinel AI implements an enterprise-grade hierarchical multi-tenant architecture designed for multi-client financial risk intelligence operations:

```
User (Global Account)
  └── Organization (Tenant Domain)
        ├── Organization Members & Roles (Admin, Analyst, Viewer)
        └── Clients (Monitored Financial Entities)
              ├── Datasets (Isolated CSV Storage & Validation)
              │     └── Analyses (ML Model Executions)
              │           ├── Scored Transactions (Database Indexed)
              │           └── SHAP Attributions (Cached)
              ├── Reports (Multi-Scope Executive PDFs)
              └── Audit Logs (Append-Only Governance Trail)
```

## Strict Tenant Isolation
1. **Database Level**: All persistent records (`Client`, `Dataset`, `Analysis`, `Transaction`, `Report`, `AuditLog`) maintain mandatory `organization_id` foreign keys with database indexes.
2. **Repository & Service Level**: Every database query, insert, update, and search explicitly filters by `organization_id`. Cross-tenant record lookups return `None` or raise HTTP `404 Not Found` / `403 Forbidden`.
3. **Filesystem Level**: Uploaded dataset files and generated PDF reports are partitioned by organization and client IDs:
   - Datasets: `data/uploads/org_{org_id}/client_{client_id}/{filename}`
   - Reports: `data/reports/org_{org_id}/report_{report_id}.pdf`
4. **API Level**: FastAPI dependencies (`require_org_member`, `require_org_analyst`, `require_org_admin`) verify user membership and permissions prior to endpoint execution.
