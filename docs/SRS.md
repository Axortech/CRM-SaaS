# Software Requirements Specification (SRS) – CRM SaaS Web Application

**Version:** 1.0  
**Date:** October 31, 2025  
**Project Type:** Multi-tenant SaaS Customer Relationship Management (CRM) Platform

---

## 1. Introduction

### 1.1 Purpose
This document defines the complete software requirements for a multi-tenant CRM SaaS web application that enables organizations to manage customer relationships, sales processes, activities, reporting, and subscriptions under customizable branding and billing plans. It serves as the single reference for product, engineering, QA, DevOps, and compliance teams.

### 1.2 Scope
The system delivers:
- Multi-tenant architecture with strict data isolation
- Lead, contact, company, opportunity, and task management
- Customizable UI with white-labeling
- Subscription and billing lifecycle management
- Role-based access control (RBAC)
- Analytics, dashboards, and reporting
- Email integration and templates
- Extensible API surface for third-party integrations

### 1.3 Definitions and Acronyms
| Term | Definition |
| --- | --- |
| SaaS | Software as a Service |
| CRM | Customer Relationship Management |
| DRF | Django REST Framework |
| RBAC | Role-Based Access Control |
| MFA | Multi-Factor Authentication |
| JWT | JSON Web Token |
| SSR | Server-Side Rendering |
| API | Application Programming Interface |

### 1.4 Technology Stack
- **Frontend:** Next.js 14+, React 18+, TypeScript, Tailwind CSS, Radix UI/shadcn
- **Backend:** Django 5.x, DRF 3.14+
- **Database:** PostgreSQL 15+
- **Cache & Queue:** Redis 7.x and Celery 5.x
- **Storage & Email:** AWS S3 (or compatible), SMTP/SendGrid/AWS SES
- **Payments:** Stripe (dj-stripe)

---

## 2. Overall Description

### 2.1 Product Perspective
Standalone multi-tenant SaaS CRM accessible through modern browsers. Each organization operates within an isolated logical tenant. Services run on Linux-based cloud infrastructure (AWS/GCP/Azure) with responsive experiences for desktop, tablet, and mobile users.

### 2.2 User Classes and Characteristics
| Role | Description |
| --- | --- |
| System Administrator | Oversees platform-level operations, observability, billing engines |
| Organization Owner | Controls subscription, billing, white-label configuration, root access |
| Organization Administrator | Manages users, permissions, custom fields, org-wide settings |
| Manager | Oversees teams, assigns work, consumes reports |
| Sales Representative | Manages assigned contacts, deals, and activity logs |
| Basic User | Light-weight access to assigned data and simple reporting |

### 2.3 Operating Environment
- **Client:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Server:** Linux containers orchestrated via Docker/Kubernetes
- **Mobile:** Responsive layout optimized for tablets and phones

### 2.4 Design and Implementation Constraints
- Enforce multi-tenancy and data isolation
- Regulatory compliance: GDPR, CCPA, SOC 2
- Scale to 10,000+ concurrent users with 99.9% uptime and p95 API latency < 200 ms

---

## 3. System Features and Requirements

Each requirement is tagged (e.g., FR-AUTH-001). Non-functional requirements appear in Section 6.

### 3.1 Authentication and Authorization
#### 3.1.1 Registration and Onboarding
- FR-AUTH-001 to FR-AUTH-010 cover email/password registration, verification, onboarding wizard, OAuth (Google/Microsoft), JWT auth, TOTP MFA, password reset, password strength enforcement, lockouts, and login history.

#### 3.1.2 Role-Based Access Control
- FR-RBAC-001 to FR-RBAC-006 require granular permissions, predefined roles, custom role creation, inheritance, owner-managed role assignment, and row-level security.

### 3.2 Subscription and Billing
#### 3.2.1 Subscription Plans
- FR-SUB-001 to FR-SUB-009 define plan tiers (Starter/Professional/Enterprise), billing cadence, discounts, plan changes, proration, trials, reminders, suspension rules, and retention.

#### 3.2.2 Payment Processing
- FR-PAY-001 to FR-PAY-008 cover Stripe integration, card payments, tokenized storage, invoicing, billing history, retry logic, multi-currency ability, and taxation.

### 3.3 White-Labeling and Customization
#### 3.3.1 Branding
- FR-BRAND-001 to FR-BRAND-011 include logo uploads, email/logo usage, brand colors, palette generation, live previews, favicon, custom subdomains, and email domains.

#### 3.3.2 Layout Customization
- FR-LAYOUT-001 to FR-LAYOUT-009 provide dashboard customization, widget control, custom fields, form reordering, conditional visibility, and default layout management.

### 3.4 Contact and Company Management
#### 3.4.1 Contacts and Leads
- FR-CONT-001 to FR-CONT-012 ensure contact CRUD, custom fields, lifecycle tracking, CSV import, deduplication, activity timelines, tagging, segmentation, source tracking, assignments, advanced search, and bulk actions.

#### 3.4.2 Companies
- FR-COMP-001 to FR-COMP-006 cover company records, contact linking, company attributes, interaction history, hierarchy, and custom fields.

### 3.5 Sales Pipeline
#### 3.5.1 Opportunities
- FR-OPP-001 to FR-OPP-012 define opportunity management, customizable stages, Kanban, probability, close tracking, relationships, line items, weighted pipeline, source tracking, activity logs, stale alerts, and assignment.

#### 3.5.2 Forecasting
- FR-FORE-001 to FR-FORE-005 specify forecasts by period/team, actual vs forecast, and multiple categories.

### 3.6 Activity and Task Management
#### 3.6.1 Tasks
- FR-TASK-001 to FR-TASK-010 require task CRUD, relationships, assignment, reminders, calendar view, templates, completion tracking, recurring tasks, dependencies, and filtering.

#### 3.6.2 Activity Logging
- FR-ACT-001 to FR-ACT-007 define comprehensive activity capture (auto/manual), timelines, templates, duration, and linkage to opportunities.

### 3.7 Email Integration
- FR-EMAIL-001 to FR-EMAIL-009 detail OAuth integrations, sync, in-app email composition, tracking, templates with variables, bulk campaigns, opt-outs, and timeline logging.

### 3.8 Reporting and Analytics
#### 3.8.1 Dashboards
- FR-DASH-001 to FR-DASH-008 include customizable dashboards, KPI visualization, pipeline charts, activity metrics, source performance, real-time updates, filters, and export.

#### 3.8.2 Reports
- FR-REP-001 to FR-REP-008 specify pre-built/custom reports, drag-and-drop builder, scheduling, chart types, sharing, filtering, and export formats.

### 3.9 User Management
- FR-USER-001 to FR-USER-008 cover invitations, plan-based limits, deactivation, activity audit, profile customization, teams, assignment rules, and audit logs.

### 3.10 Settings and Configuration
- FR-SET-001 to FR-SET-009 include org settings, business hours, pipeline customization, custom fields, workflow automation, notification preferences, data export, API keys, and webhooks.

### 3.11 Mobile Responsiveness
- FR-MOB-001 to FR-MOB-005 ensure responsive layouts, touch support, mobile navigation, and optimized assets.

---

## 4. Frontend Architecture (Next.js)

### 4.1 Technology Stack
- Next.js App Router, TypeScript 5.x, Tailwind CSS, Radix UI/shadcn
- React Hook Form + Zod, TanStack Query, Zustand/Redux Toolkit
- Recharts/Chart.js, dnd-kit, date-fns, Tiptap/Lexical
- Tooling: pnpm, ESLint, Prettier, Jest, React Testing Library, Playwright

### 4.2 Application Structure
```
frontend/
├─ app/ (auth and dashboard route groups, layouts, API routes)
├─ components/ (ui, forms, layouts, feature modules, shared)
├─ lib/ (api, hooks, utils, validators, constants)
├─ stores/
├─ types/
├─ styles/
└─ public/
```

### 4.3 Routing
- Authentication routes: `/login`, `/register`, `/forgot-password`, `/reset-password/[token]`, `/verify-email/[token]`
- Protected routes: `/dashboard`, `/contacts`, `/contacts/[id]`, `/companies`, `/companies/[id]`, `/opportunities`, `/opportunities/[id]`, `/tasks`, `/reports`, `/reports/[id]`, `/settings/*`

### 4.4 Component Architecture
- **UI:** Atomic components (Button, Input, Table, Tabs, etc.)
- **Layouts:** App shell with sidebar, header, breadcrumbs, quick create
- **Features:** Domain-specific components (contacts, opportunities, tasks, reports)
- **Forms:** Field builders, validation messaging, submit bars

### 4.5 State & Data Fetching
- **Global state:** Auth, org settings, branding, permissions, UI preferences
- **Server state:** Domain data via TanStack Query with targeted stale/caching windows, retries, optimistic updates, cursor pagination, and infinite scroll feeders.
- **Local state:** Form state, modal toggles, filters, ephemeral UI interactions.
- **API client:** Axios with JWT interceptors, logging (dev), retry, cancellation.

### 4.6 Navigation & Protection
- Middleware enforcement for auth, RBAC, subscription checks, and redirect flows. Sidebar with collapsible sections, top bar quick actions, breadcrumbs, global search, and quick create widgets.

### 4.7 White-Labeling
- CSS custom properties for theming, runtime injection of logos/favicons, cached assets, email branding, and layout customization engine storing JSON configuration per org/user.

### 4.8 Performance
- next/image, dynamic imports, server components, streaming SSR, ISR for reports, CDN-backed caching, service worker asset caching, and browser storage for user preferences.

### 4.9 Forms
- React Hook Form + Zod, multi-step flows, auto-save drafts, session storage persistence, dynamic custom fields with conditional visibility and validation.

### 4.10 Error Handling & Accessibility
- Global and feature error boundaries, fallback UIs, toast notifications, accessibility compliance (WCAG 2.1 AA), semantic HTML, ARIA labels, keyboard navigation, focus management, color contrast, and skip links.

### 4.11 Testing
- Unit: Components, hooks, utilities (80% coverage)
- Integration: Page and feature flows
- E2E: Critical journeys with Playwright across browsers and mobile form factors

---

## 5. Backend Architecture (Django REST Framework)

### 5.1 Technology Stack and Key Packages
- Django 5.x, DRF 3.14+, PostgreSQL 15+, Redis 7.x, Celery 5.x
- Core packages: drf-simplejwt, django-allauth, django-guardian, drf-spectacular, django-cors-headers, django-environ, psycopg2-binary, django-phonenumber-field, stripe/dj-stripe, django-auditlog, django-ratelimit, sentry-sdk, django-prometheus

### 5.2 Project Structure
```
backend/
├─ config/
│  ├─ settings/{base,development,production,test}.py
│  ├─ urls.py, asgi.py, wsgi.py
├─ apps/
│  ├─ accounts, organizations, subscriptions, contacts, companies,
│  │   opportunities, tasks, activities, emails, reports, customization,
│  │   integrations, notifications
├─ core/ (middleware, permissions, pagination, exceptions, validators, utils)
├─ tests/
├─ manage.py
└─ requirements/{base,development,production}.txt
```

### 5.3 Data Model Overview
- Comprehensive models for users, organizations, roles, memberships, subscriptions, payments, contacts, companies, opportunities, stages, line items, tasks, activities, emails, templates, custom fields, layouts, reports, scheduled reports, webhooks, audit logs, tags, notifications.
- Common indexing patterns: automatic FKs, unique emails, GIN indexes for search, composite indexes (`organization_id` + `created_at`, `owner_id`, `status`, etc.) to optimize tenant-scoped queries.
- Multi-tenancy ensured by mandatory `organization` FK, middleware scoping, optional PostgreSQL RLS or per-schema deployments for enterprise tenants.

### 5.4 API Architecture
- Versioned REST API (`/api/v1`) with URL and Accept-header version negotiation. Six-month minimum support for deprecated versions.
- Endpoint families span authentication, organizations, subscriptions, payments, contacts, companies, opportunities, tasks, activities, emails, reports, dashboard widgets, settings (custom fields, opportunity stages, layouts, webhooks), and user self-service endpoints.
- Standardized success/error envelopes, cursor/page-based pagination, filtering, searching, ordering, sparse fieldsets, field exclusion, and relation expansion.

### 5.5 Authentication & Authorization
- JWT access (15 min) and refresh (7 days) tokens stored in httpOnly cookies or Authorization header, with token blacklisting and device tracking.
- OAuth (Google/Microsoft) with account linking or auto-provisioning, MFA via TOTP, API keys with rotation and rate limits, and object-level permissions via django-guardian with caching.
- Role matrix: Owner (full control), Admin (org data and user management), Manager (team scope + partial settings), Sales Rep (own data + team read), Basic User (assigned data).

### 5.6 Business Logic
- Service-layer pattern encapsulates domain rules (validation, dedupe, multi-model writes, external APIs, events). Example: `ContactService.create_contact` handles validation, dedupe, creation, activity logging, webhooks, email notifications.
- Event system uses Django signals internally and webhooks externally. Event types: `contact.*`, `opportunity.*`, `task.*`, `payment.*`, `subscription.*`.
- Celery queues: default, high-priority, low-priority, scheduled. Periodic jobs handle reminders, stale opportunity scans, scheduled reports, subscription checks, and backups; async jobs handle bulk email, CSV import, large report generation, webhook delivery, email sync, and data exports.

### 5.7 Email Integration
- HTML/text template rendering, attachments, tracking of opens/clicks, bounce handling, unsubscribe management, IMAP/OAuth sync tasks, automatic contact linking, thread grouping, and attachment extraction.

### 5.8 Search
- PostgreSQL full-text search with weighted vectors, trigram similarity, ranked cross-entity global search that respects permissions and highlights matches.

### 5.9 File Handling
- S3/MinIO storage, signed URLs, tier-based limits, file-type validation, virus scanning (ClamAV), thumbnailing, optimization, format conversion, and avatar cropping.

### 5.10 Caching
- Redis-backed caches for sessions, permissions, organization settings, selective API responses, query results, and rate-limit tracking. Time-based expirations, manual invalidation hooks, key versioning, and automatic invalidation via model signals.

### 5.11 Rate Limiting
- Tier-based per-organization limits (Starter 1k/hr, Professional 5k/hr, Enterprise 20k/hr), plus IP and API-key throttles. Responses include limit headers with graceful degradation.

### 5.12 Validation
- Serializer-level validation (field/object/cross-field), reusable validators, subscription-limit enforcement, permission checks, dedupe routines, context-aware required fields.

### 5.13 Logging & Monitoring
- Structured JSON logging (request/response, SQL in dev, Celery tasks, auth events), audit logging (CRUD changes, user actions, IP/user-agent, two-year retention), performance monitoring via Sentry APM, DB query metrics, Celery task metrics, Prometheus exporters, and Django Debug Toolbar for dev.

### 5.14 Testing
- Unit tests for models, serializers, services, utilities (80%+ coverage).
- Integration tests for REST endpoints, auth flows, permission checks, transactions.
- Performance/load testing with Locust for API and DB metrics.

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **NFR-PERF-001:** API p95 latency < 200 ms
- **NFR-PERF-002:** Page load < 2 seconds on broadband
- **NFR-PERF-003:** Sustain 10,000 concurrent users
- **NFR-PERF-004:** Simple DB queries < 100 ms
- **NFR-PERF-005:** Support 1 million contacts per organization
- **NFR-PERF-006:** Background jobs complete < 5 minutes for bulk ops
- **NFR-PERF-007:** Notification delivery < 1 second

### 6.2 Scalability
- Horizontal app scaling, DB read replicas, CDN-backed static assets, auto-scaling policies, capacity for 100,000+ organizations, and future-ready microservice decomposition.

---

## 7. Traceability and Compliance
- Each functional requirement is uniquely tagged to enable traceability across design, implementation, and testing.
- Compliance priorities: GDPR (data subject rights, DPA), CCPA (opt-outs), SOC 2 (controls over security, availability, confidentiality).
- Audit logs retained for 24 months with export mechanisms for regulators.

---

## 8. Open Issues and Future Enhancements
1. Evaluate need for per-tenant schema isolation vs RLS for enterprise plans.
2. Plan for advanced analytics (AI-assisted scoring, sentiment analysis).
3. Consider marketplace integrations (Zoom, Slack, Teams) in next versions.

---

## 9. Approval
| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Product Owner | _TBD_ |  |  |
| Engineering Lead | _TBD_ |  |  |
| QA Lead | _TBD_ |  |  |
| Compliance Officer | _TBD_ |  |  |

---

**Document Control:** Version 1.0 supersedes previous drafts. Future revisions must update this section and retain change logs.
