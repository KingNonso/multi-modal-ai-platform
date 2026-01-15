Perfect! Now I understand the full context. The steering doc you provided is solid, but I can enhance it significantly to align with the comprehensive project vision. Here's an improved version:

# KIRO Steering Document - Enhanced & Aligned

**inclusion: always**

---

# Technology Stack

## Project Type

**Monorepo for a unified, multi-modal AI customer service platform** containing:

- A **Next.js/React frontend application** (customer-facing + agent dashboards + admin console)
- A **Django 5.2 backend** (Python 3.14) for core platform logic, orchestration, and integration layer
- **Microservices layer** for channel adapters, AI/ML pipelines, and real-time processing

This is a **unified platform architecture**, not separate single-channel solutions.

## Languages & Runtimes

- **JavaScript/TypeScript**: Next.js/React frontend (Node.js runtime)

  - Customer-facing web interfaces
  - Agent and manager dashboards
  - Admin configuration console
  - Real-time chat, notification, and status streaming

- **Python 3.14**: Django 5.2 backend and microservices
  - Core orchestration engine
  - Integration layer (CRM, ERP, email, social media APIs)
  - AI/ML pipeline services (NLU, speech processing, sentiment analysis)
  - Data persistence and context management
  - WebSocket and WebRTC signaling

## Build System & Package Management

- **Node.js**: 24.13.0 LTS + **Yarn 1.22.22** as primary package manager for frontend
- **Python**: **`uv`** for dependency and virtual environment management (Python 3.14, Django 5.2)
- **Monorepo Structure**: Single repository with:
  - `/frontend` - Next.js application
  - `/backend` - Django application and core services
  - `/services` - Microservices (channel adapters, AI pipelines, real-time handlers)
  - `/shared` - Common utilities, type definitions, configuration schemas
  - `/infrastructure` - Docker Compose, deployment configurations, scripts

## Key Technology Requirements

### Multi-Channel Support (Core Differentiator)

The platform handles **unified context persistence** across:

| Channel                | Type                         | Technology Stack                                | Latency Target             |
| ---------------------- | ---------------------------- | ----------------------------------------------- | -------------------------- |
| **Voice** (phone/VoIP) | Synchronous, real-time       | PSTN/SIP/WebRTC, Twilio/Vonage SDK              | <500ms                     |
| **Chat**               | Synchronous, near real-time  | WebSocket, Socket.io                            | <2s                        |
| **Social Media**       | Asynchronous + real-time DMs | Native APIs (X, Facebook, Instagram, TikTok)    | <2s (DMs), <5min (public)  |
| **Email**              | Asynchronous                 | SMTP/IMAP, Gmail API, Microsoft Graph, SendGrid | <5min                      |
| **Video**              | Synchronous, high-bandwidth  | WebRTC, Zoom/Teams SDKs                         | <500ms audio, 100ms frames |

**Context Sync**: All channels maintain a single customer record with persistent conversation history (14+ day minimum retention).

### AI/ML Stack

- **Natural Language Understanding (NLU)**

  - Intent classification, entity extraction
  - Multi-language support (40+ languages)
  - Sentiment analysis and emotion detection

- **Speech Processing**

  - Speech-to-text (STT)
  - Text-to-speech (TTS)
  - Voice biometrics and speaker identification
  - Real-time transcription with <500ms latency

- **Computer Vision**

  - Image classification and damage assessment
  - Document OCR and form extraction
  - Facial expression analysis (for video)
  - Product identification from photos

- **Knowledge Retrieval**

  - Semantic search over internal knowledge bases
  - Real-time FAQ/documentation matching
  - Automatic article suggestion engine
  - Conversation context encoding and retrieval

- **AI Model Orchestration**
  - Conversation state management
  - Decision routing (when to escalate, which channel to recommend)
  - Autonomous transaction execution (refunds, bookings, updates)

### Integration Layer

**CRM & Business Systems**:

- **CRM Connectors**: Salesforce, HubSpot, Pipedrive, Zendesk
- **ERP/Order Management**: SAP, NetSuite, Shopify
- **Inventory**: Real-time stock checking and reservations
- **Billing/Finance**: Stripe, PayPal, custom payment systems

**Communication Providers**:

- **Email APIs**: Gmail, Microsoft Graph, SendGrid, Twilio SendGrid
- **SMS/Messaging**: Twilio, Vonage, Nexmo, native WhatsApp Business API
- **Social Media APIs**: Twitter/X, Facebook, Instagram, TikTok, LinkedIn
- **Voice**: Twilio, Vonage, AWS Connect, custom SIP

**Infrastructure**:

- REST APIs for all integrations
- Webhook event subscriptions for real-time sync
- Middleware for data transformation and normalization
- Event-driven messaging (likely Kafka/RabbitMQ for scale)

### Infrastructure & Deployment

- **Containerization**: Docker with docker-compose for local development
- **Orchestration**: Kubernetes for production (AWS EKS or self-managed)
- **Primary Cloud**: AWS (with multi-region support capability)

  - EC2 / ECS for compute
  - RDS (PostgreSQL) for primary database
  - S3 for conversation history and file storage
  - ElastiCache (Redis) for real-time state and caching
  - SQS/SNS for event routing
  - CloudFront for CDN (global delivery)

- **Real-Time Infrastructure**:

  - WebSocket server for chat and live agent collaboration
  - Redis for conversation state and presence (who's online)
  - Message queue (SQS/Kafka) for asynchronous channel processing

- **Observability**:
  - CloudWatch for logs and metrics
  - OpenTelemetry for distributed tracing
  - Grafana/Prometheus for dashboards
  - PagerDuty for alerting

## Performance Requirements

| Metric                       | Target                            | Business Impact                                        |
| ---------------------------- | --------------------------------- | ------------------------------------------------------ |
| **Voice Latency**            | <500ms                            | Conversational natural experience                      |
| **Chat Latency**             | <2s                               | Perceived instant response                             |
| **Email Response**           | <5min                             | SLA compliance for async channels                      |
| **System Uptime**            | 99.99% (52 minutes downtime/year) | Enterprise-grade availability                          |
| **Concurrent Conversations** | 100K+                             | Scale to millions of daily interactions                |
| **AI Automation Rate**       | 70-80%                            | Cost reduction target (85% cost/interaction reduction) |
| **First Contact Resolution** | >80%                              | Reduce repeat contacts and escalations                 |

## Development Workflow Requirements

### Critical: Always Required Steps

These steps MUST be performed every time you work on the project:

#### Backend (Python/Django) - ALWAYS:

1. **Activate virtual environment** before any Python command:

   ```bash
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

2. **Install/update dependencies** when requirements change or after pulling code:

   ```bash
   uv pip install -r requirements.txt
   ```

3. **Run migrations** after pulling code or changing models:

   ```bash
   python manage.py migrate
   ```

4. **Collect static files** before deployment or when static assets change:
   ```bash
   python manage.py collectstatic --noinput
   ```

#### Frontend (Next.js/React) - ALWAYS:

1. **Install/update dependencies** when package.json changes or after pulling code:

   ```bash
   yarn install
   ```

2. **Clear Next.js cache** if experiencing build issues:

   ```bash
   rm -rf .next
   ```

3. **Environment variables** must be set in `.env.local` (never commit this file):
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_WS_URL`
   - Any other `NEXT_PUBLIC_*` variables

#### Both Frontend & Backend - ALWAYS:

1. **Check environment files exist**:

   - Backend: `.env` (gitignored, copy from `.env.example`)
   - Frontend: `.env.local` (gitignored, copy from `.env.example`)

2. **Verify Docker services are running** (if using Docker for local dev):

   ```bash
   docker compose ps  # Check status
   docker compose up -d postgres redis  # Start dependencies
   ```

3. **Check database connection** before running migrations or starting servers

4. **Pull latest code and sync dependencies**:
   ```bash
   git pull
   cd backend && source .venv/bin/activate && uv pip install -r requirements.txt
   cd ../frontend && yarn install
   ```

### Pre-commit Checklist

Before committing code, ALWAYS:

- Run linters: `yarn lint` (frontend), `ruff check .` or `flake8` (backend)
- Run tests: `yarn test` (frontend), `pytest` (backend)
- Check for secrets/API keys in code
- Verify `.env` files are gitignored and not staged

## Common Commands

```bash
# ===== Frontend (Next.js/React) =====
cd frontend

# Setup
yarn install
yarn dev       # Run dev server on http://localhost:3000

# Building & Testing
yarn build
yarn test
yarn lint

# ===== Backend (Django 5.2 + Python 3.14 with uv) =====
cd backend

# Setup
uv venv                              # Create/activate virtual environment
uv pip install -r requirements.txt   # Install dependencies

# Database & Migrations
python manage.py migrate
python manage.py createsuperuser

# Running
python manage.py runserver           # Dev server on http://localhost:8000
python manage.py celery worker       # Background task worker

# ===== Docker (Local Development) =====
# Builds and runs all services: frontend, backend, PostgreSQL, Redis, etc.
docker compose up --build

# Run specific service
docker compose up -d postgres redis
docker compose logs -f backend

# ===== Microservices (Optional - Phase 2) =====
# Channel-specific adapters
cd services/voice-adapter
docker build -t voice-adapter .

cd services/social-media-listener
docker build -t social-adapter .
```

## Security & Compliance

### Certifications & Standards

- **SOC 2 Type II**: Annual attestation of security controls
- **HIPAA**: For healthcare customer service scenarios (encryption, audit logging, BAA agreements)
- **PCI DSS**: For payment processing integrations (tokenization, segregated network)
- **GDPR**: EU data residency, right-to-be-forgotten, data processing agreements
- **CCPA**: California privacy rights, data inventory, deletion workflows
- **ISO 27001**: Information security management system

### Data Security

- **Encryption at Rest**: AES-256 for database and file storage
- **Encryption in Transit**: TLS 1.3 for all API communication, WSS for WebSocket
- **Key Management**: AWS KMS or HashiCorp Vault
- **Database Security**: PostgreSQL row-level security (RLS) for multi-tenancy

### Audit & Compliance

- **Audit Logging**: All data access, modifications, and API calls logged with timestamp and user
- **Log Retention**: Minimum 7 years per regulatory requirements
- **User Activity Tracking**: Customer identity, agent actions, system events
- **Compliance Reporting**: Automated reports for audit readiness

### Data Privacy

- **Data Residency**: Support for region-specific storage (EU, Canada, Australia)
- **Right to Erasure**: Automated deletion workflows for customer data
- **Data Retention Policies**: Configurable retention periods (default 14 days for conversations)
- **Anonymization**: PII masking in logs and analytics dashboards

### Access Control

- **Role-Based Access Control (RBAC)**: Agent, Manager, Administrator, Data Scientist roles
- **Multi-Factor Authentication (MFA)**: Required for all internal users
- **IP Whitelisting**: Configurable per customer environment
- **API Key Rotation**: Automatic key expiration and renewal

### MVP Deployment Architecture - Simplified

For an MVP, I want monolithic simplicity with just enough separation to be maintainable. Here's the dead-simple approach:

Single-Container Deployment Model
text
┌─────────────────────────────────────┐
│ AWS ECS Fargate │
├─────────────────────────────────────┤
│ Docker Container (All-in-One Image) │
│ ├── Next.js frontend (served) │
│ ├── Django backend (gunicorn) │
│ ├── Celery worker (background) │
│ └── WebSocket server (daphne) │
├─────────────────────────────────────┤
│ RDS PostgreSQL (managed AWS) │
│ ElastiCache Redis (for sessions) │
└─────────────────────────────────────┘
