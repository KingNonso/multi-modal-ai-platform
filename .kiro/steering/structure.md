---
inclusion: always
---

# Project Structure

## Repository Organization

This is a monorepo containing multiple packages/services for a multi-modal AI customer service platform.

## Expected Structure

```
/
├── frontend/              # Next.js/React web app (customer + internal UIs)
├── backend/               # Django 5.2 project and apps
├── docs/                  # Product and architecture documentation
├── infra/                 # Docker, AWS IaC and deployment configs
├── scripts/               # Dev, CI, and utility scripts
├── .github/               # CI/CD workflows
└── .kiro/                 # Steering docs and configuration
```

## Key Architectural Patterns

### Microservices

- Each channel is an independent service
- Services communicate via event-driven messaging
- Shared context engine maintains conversation state

### Channel Independence

- Each channel service handles its specific protocol
- All channels write to unified context store
- Context engine provides cross-channel continuity

### Integration Layer

- Centralized integration hub for business systems
- Pre-built connectors for major CRM/ERP platforms
- REST API gateway for external integrations

### Data Flow

1. Customer interaction → Channel service
2. Channel service → Context engine (store/retrieve)
3. Context engine → AI processing
4. AI processing → Integration hub (if needed)
5. Response → Channel service → Customer

## Configuration Management

- Environment-specific configs in `.env` files (gitignored)
- Shared configuration in version control
- Secrets managed via secure vaults (not in repo)

## Build Artifacts

All build outputs go to:

- `dist/` or `build/` directories (gitignored)
- `node_modules/` for dependencies (gitignored)
- `__pycache__/` and `venv/` for Python (gitignored)

## Documentation Location

- Product specs: `/docs/` or root-level markdown files
- API documentation: Per-service in `packages/*/docs/`
- Architecture diagrams: `/docs/architecture/`
- Runbooks: `/docs/operations/`
