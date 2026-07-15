## v1.1.0 Partial Updates (PATCH) (15th July 2026)

- Added PATCH endpoint for partially updating users
- PUT and PATCH use separate schemas: PUT requires every field (full replace), PATCH accepts only the fields being changed
- Duplicate email validation on PATCH accounts for the field not being included in the request

## v0.1.0 Initial Setup (15th July 2026)

- Project scaffolding
- Field length and content validation
- Duplicate validation
- Exception handling and logging
- JWT authentication with protected routes
- Admin-only access control (RBAC) for registration and user management