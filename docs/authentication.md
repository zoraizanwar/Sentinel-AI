# Authentication & JWT Architecture

## Overview
Sentinel AI uses stateless JSON Web Token (JWT) authentication for secure, multi-tenant API communication.

## Flow
1. **Registration** (`POST /api/v1/auth/register`):
   - Accepts `email`, `password`, `full_name`, and optional `organization_name`.
   - Hashes password using bcrypt.
   - Automatically provisions a default organization and assigns the user the `ORGANIZATION_ADMIN` role.
   - Returns a JWT bearer token.
2. **Login** (`POST /api/v1/auth/login`):
   - Validates email and password.
   - Issues a signed HS256 JWT access token containing `sub` (User UUID) and expiration timestamp.
3. **Session Verification** (`GET /api/v1/auth/me`):
   - Returns user profile and all tenant memberships with assigned roles.
4. **Token Interception**:
   - Frontend stores the token in `localStorage` and injects `Authorization: Bearer <token>` into all outbound requests.
