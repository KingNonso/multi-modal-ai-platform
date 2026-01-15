---
inclusion: always
---

# Product Overview

Multi-Modal Customer Service AI Platform - a unified AI system enabling seamless customer service across voice, chat, email, video, and social media with persistent context across all channels.

## Core Value Proposition

- Single conversation thread across all channels - customers never repeat themselves
- 24/7 AI coverage achieving 70-80% automation rate
- Seamless escalation to human agents with full context transfer
- Real-time integration with CRM, ERP, and business systems

## Key Channels

- Voice (PSTN, VoIP, mobile) - <500ms latency
- Chat (web, WhatsApp, SMS, Messenger) - <2s latency
- Social Media (Twitter, Facebook, Instagram, TikTok) - proactive listening and response
- Email (SMTP/IMAP, Gmail, Microsoft Graph) - <5min response
- Video (WebRTC, Zoom, Teams) - avatar-based AI agents

## Target Metrics

- 70-80% automation rate
- > 80% first contact resolution
- <$2 cost per interaction (down from $8-12)
- 99.99% uptime
- CSAT >4.5/5.0

## Compliance Requirements

All features must support: GDPR, CCPA, HIPAA, PCI DSS, SOC 2 Type II

- Data residency requirements (EU, Canada, Australia)
- 7-year audit trails
- Right-to-be-forgotten support

## Implementation Snapshot

- Monorepo containing a Next.js/React frontend and a Django 5.2 backend
- Python 3.14 runtime for backend services, with virtual environments managed via `uv`
- Dockerized services for local development and production
- Deployment targets AWS (container-based deployment; specific services can be refined)

## Current Status

Planning Phase (v1.0) - 12-month deployment timeline
Priority: Voice + Chat first, then Email, then Video
