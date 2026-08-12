# HabotConnect - LSA Service Booking Platform
## Hiring Assessment Technical Presentation Outline (15 Slides)

**Candidate Name**: Abhishek Bodkhe  
**Position**: Python Backend Developer  
**Contact Email**: abhishek.bodkhe@example.com  
**GitHub Repository**: https://github.com/ABHISHEKBODKHE011/LSA-Service-Booking  
**Submission Deadline**: 13th August 2026  
**Submission Link**: https://forms.gle/YzHDkd23ApzpP2ze7  

---

### Slide 1: Title & Project Overview
- **Title**: HabotConnect - Learning Support Assistant (LSA) Service Booking Backend
- **Presenter**: Abhishek Bodkhe (Python Backend Developer Candidate)
- **GitHub Repository**: https://github.com/ABHISHEKBODKHE011/LSA-Service-Booking
- **Context**: Production-grade REST API backend platform connecting parents with LSAs for children with learning difficulties and special educational needs.

---

### Slide 2: HabotConnect Values & Leadership Principles Alignment
- **Quiet Management & Self-Reliance**: Fully autonomous engineering prototype designed with clear interfaces, zero manual intervention, and high reliability.
- **Detail-Obsessed Quality**: Strict database constraints, indexed models, exact data types, and protective foreign keys (`models.PROTECT`).
- **Poka-Yoke (Mistake-Proofing)**: Concurrency locking (`select_for_update()`), interval overlap validators, and idempotent webhook handlers to prevent bad states automatically.

---

### Slide 3: Problem Statement & Engineering Challenges
- **Domain Challenge**: Parents of children with specialized needs require reliable, real-time booking of qualified LSAs.
- **Key Technical Hurdles**:
  1. Concurrent double-booking race conditions.
  2. Performance bottlenecks from N+1 query patterns during multi-skill searches.
  3. Resilient payment webhook state transitions and 3rd-party integration.

---

### Slide 4: Core Deliverables & Requirements
- **Relational Schema**: 4 core entities (`Parent`, `LSAProfile`, `BookingRequest`, `Payment`) plus normalized `Skill`.
- **Booking Endpoint**: `POST /api/v1/bookings/` with overlap validation and payment processing.
- **Optimized Search Endpoint**: `GET /api/v1/lsas/search/` with `O(1)` query complexity for skill filtering.
- **Automated Webhook Endpoint**: `POST /api/v1/payments/webhook/` for event-driven booking state transitions.
- **Verification & CI**: 28 automated Pytest test cases and GitHub Actions CI workflow.

---

### Slide 5: System Architecture & Design Choices
- **Architecture Pattern**: Layered Django MVT + DRF RESTful Service Architecture.
- **Layer Separation**:
  - `models.py`: Relational database schema & DB-level constraints.
  - `selectors.py`: Optimized, read-only ORM query abstractions (`prefetch_related`).
  - `validators.py`: Business logic & time interval overlap verification.
  - `services/`: Third-party mock payment gateway integration (`requests`).
  - `views.py` & `serializers.py`: API view handlers and payload validation.

---

### Slide 6: Technology Stack Selection
- **Core Language**: Python 3.12+ (Type hints, Dataclasses, Clean OOP).
- **Framework**: Django 5.2 + Django REST Framework (DRF) 3.15.
- **Database**: PostgreSQL (Production/CI) / SQLite (Local Fallback).
- **Testing**: `pytest`, `pytest-django`, `pytest-cov`.
- **API Documentation**: OpenAPI 3.0 via `drf-spectacular`.
- **CI/CD**: GitHub Actions with live PostgreSQL 16 service container.

---

### Slide 7: Relational Database Schema Design
- **Entities**:
  - `Parent`: `id`, `full_name`, `email` (unique, indexed), `phone`, timestamps.
  - `Skill`: `id`, `name` (unique, indexed), `description`.
  - `LSAProfile`: `id`, `full_name`, `email`, `hourly_rate` (>0 check constraint), `is_active` (indexed).
  - `BookingRequest`: FKs to `Parent` & `LSAProfile` (`on_delete=PROTECT`), `session_date`, `start_time`, `end_time` (check `end > start`), `status` (PENDING, CONFIRMED, FAILED, CANCELLED).
  - `Payment`: FK to `BookingRequest` (`on_delete=PROTECT`), `transaction_id` (unique, indexed), `amount`, `status` (PENDING, SUCCESS, FAILED), `provider`, `raw_response`.

---

### Slide 8: Entity Relationship Diagram (ERD)
- **Relationships**:
  - `Parent (1) ─── (N) BookingRequest`
  - `LSAProfile (1) ─── (N) BookingRequest`
  - `LSAProfile (N) ─── (N) Skill` (Normalized Many-to-Many junction)
  - `BookingRequest (1) ─── (N) Payment`
- **Integrity**: `on_delete=models.PROTECT` prevents cascade deletions of historical booking and financial data.

---

### Slide 9: Booking Request API (`POST /api/v1/bookings/`)
- **Payload Validation**:
  - Parent & LSA existence checks.
  - LSA active status verification.
  - Session time logical check (`start_time < end_time`).
  - Time slot overlap check on target session date.
- **Response Handling**:
  - `201 Created`: Booking created and payment processed successfully.
  - `400 Bad Request`: Validation failure or payment failure.
  - `404 Not Found`: Non-existent Parent or LSA.
  - `409 Conflict`: Overlapping time slot conflict.

---

### Slide 10: Double-Booking Prevention & Concurrency Control
- **Overlap Formula**:
  $$\text{start\_time}_1 < \text{end\_time}_2 \quad \text{AND} \quad \text{end\_time}_1 > \text{start\_time}_2$$
- **Back-to-Back Bookings**: Allowed (e.g. 10:00-11:00 and 11:00-12:00).
- **Concurrency Locking**:
  `transaction.atomic()` combined with `select_for_update()` on `LSAProfile` locks the target LSA row during request processing to prevent concurrent race conditions.

---

### Slide 11: LSA Search API (`GET /api/v1/lsas/search/`)
- **Endpoint**: `GET /api/v1/lsas/search/?skills=math,science`
- **Capabilities**:
  - Case-insensitive multi-skill filtering.
  - Filters out inactive LSAs (`is_active=True`).
  - Structured response containing item count and results list.

---

### Slide 12: N+1 Query Problem & ORM Optimization
- **The N+1 Anti-Pattern**: Iterating over $N$ LSAs to retrieve their skills executes 1 query for LSAs + $N$ queries for skills (101 SQL queries for 100 LSAs).
- **The Optimization**:
  `LSAProfile.objects.filter(is_active=True).prefetch_related('skills')`
  Executes **exactly 2 SQL queries** regardless of dataset size.
- **Automated Verification**: Pytest assertion using `django_assert_num_queries(2)`.

---

### Slide 13: Payment Webhook Endpoint & Third-Party Resiliency
- **Service Abstraction**: `PaymentGatewayService` in `bookings/services/payment_service.py` handles external HTTP communication via `requests` with 5s timeouts and exception handling.
- **Automated Webhook (`POST /api/v1/payments/webhook/`)**:
  - Listens to external payment events (`payment.succeeded`, `payment.failed`).
  - Dynamically updates `BookingRequest` status (`CONFIRMED` / `FAILED`).
  - Creates/updates `Payment` audit trail records using idempotent transactions.

---

### Slide 14: Testing Strategy & CI/CD Pipeline
- **Test Suite**: 28 automated test cases using `pytest-django` achieving **88% total line coverage**.
- **Test Scenarios**:
  - Database schema & check constraints.
  - Booking success, edge cases (back-to-back), and overlap conflicts.
  - Payment webhook event processing and status transitions.
  - Mock payment timeouts and HTTP errors.
  - N+1 query optimization verification.
- **CI/CD**: GitHub Actions workflow (`.github/workflows/tests.yml`) running `manage.py check`, migration integrity checks, and `pytest --cov`.

---

### Slide 15: Conclusion & Technical Justification (Django vs Flask)
- **Framework Comparison**: Django MVT + DRF selected over Flask due to native ORM migrations, built-in transaction management (`transaction.atomic`), automated Admin dashboard, and DRF serialization ecosystem.
- **Summary**: Delivered a production-ready, mistake-proof (Poka-Yoke), high-performance Python backend prototype fully meeting HabotConnect's hiring standards.
