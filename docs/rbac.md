# Role-Based Access Control (RBAC)

## Overview
Sentinel AI enforces hierarchical Role-Based Access Control at the API dependency level per organization tenant.

## Roles & Permissions Matrix

| Permission / Action | `ORGANIZATION_ADMIN` | `ANALYST` | `VIEWER` |
|:---|:---:|:---:|:---:|
| View Dashboards & Telemetry | ✅ | ✅ | ✅ |
| View Transaction Tables & Filters | ✅ | ✅ | ✅ |
| View Model Explainability (SHAP) | ✅ | ✅ | ✅ |
| Download Generated PDF Reports | ✅ | ✅ | ✅ |
| View Audit Logs | ✅ | ✅ | ✅ |
| Ingest & Upload CSV Datasets | ✅ | ✅ | ❌ |
| Run Machine Learning Analyses | ✅ | ✅ | ❌ |
| Create & Archive Clients | ✅ | ✅ | ❌ |
| Generate Executive PDF Reports | ✅ | ✅ | ❌ |
| Invite & Manage Team Members | ✅ | ❌ | ❌ |
| Change Member Roles | ✅ | ❌ | ❌ |
| Organization Configuration | ✅ | ❌ | ❌ |

## Backend Enforcement
Endpoints use reusable FastAPI dependencies:
- `require_org_member`: Verifies caller belongs to the target organization.
- `require_org_analyst`: Requires `ORGANIZATION_ADMIN` or `ANALYST` role.
- `require_org_admin`: Requires `ORGANIZATION_ADMIN` role.

Unprivileged or cross-tenant requests are denied with HTTP `403 Forbidden` or secure `404 Not Found`.
