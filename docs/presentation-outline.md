# HabotConnect - LSA Service Booking Platform
## Hiring Assessment Technical Presentation Outline (15 Slides)

---

### Slide 1: Title & Overview
- **Title**: HabotConnect - Learning Support Assistant (LSA) Service Booking Backend
- **Presenter**: Abhishek Bodkhe (Python Backend Developer)
- **GitHub Repository**: https://github.com/ABHISHEKBODKHE011/LSA-Service-Booking
- **Context**: Production-grade REST API backend platform connecting parents with LSAs for children with learning difficulties.


---

### Slide 2: Problem Statement
- **Domain Challenge**: Parents of children with specialized educational needs require reliable, real-time booking of qualified LSAs.
- **Key Technical Hurdles**:
  - Overlapping booking conflicts (double-booking race conditions).
  - Performance bottlenecks due to N+1 query patterns in skill filtering.
  - Integration with third-party payment gateways with fault tolerance.

---

### Slide 3: Core Requirements
- **Relational Domain Modeling**: Parents, LSA Profiles, Skills, Booking Requests.
- **Strict Concurrency Protection**: Prevent overlapping time slots for the same LSA.
- **Optimized Search**: Filter active LSAs by multi-skill requirements in `O(1)` query complexity.
- **Resilient Third-Party Integration**: Service layer for mock payment gateway with timeout and retry controls.
- **Automated Verification**: Comprehensive unit & integration testing via pytest and GitHub Actions CI.

---

### Slide 4: System Architecture
- **Architecture Pattern**: Django MVT + DRF RESTful Service Layer Architecture.
- **Layer Breakdown**:
  - `models.py`: Relational database schemas & DB-level constraints.
  - `selectors.py`: Optimized, read-only ORM query abstractions.
  - `validators.py`: Business logic & time interval overlap verification.
  - `services/`: Third-party payment gateway integration.
  - `views.py` & `serializers.py`: DRF request validation and response formatting.

---

### Slide 5: Technology Stack
- **Language**: Python 3.12+ (Type hints, Dataclasses, Clean OOP).
- **Framework**: Django 5.2 + Django REST Framework (DRF).
- **Database**: PostgreSQL (Production & CI) / SQLite (Local Fallback).
- **Testing**: pytest, pytest-django, pytest-cov.
- **API Documentation**: OpenAPI 3.0 via `drf-spectacular`.
- **CI/CD**: GitHub Actions with automated PostgreSQL service container.

---

### Slide 6: Relational Database Schema Design
- **Entities**:
  - `Parent`: `id`, `full_name`, `email` (unique, indexed), `phone`, timestamps.
  - `Skill`: Normalized entity (`id`, `name` unique indexed, `description`).
  - `LSAProfile`: `id`, `full_name`, `email`, `hourly_rate` (>0 check constraint), `is_active` (indexed).
  - `BookingRequest`: FKs to `Parent` & `LSAProfile` (`on_delete=PROTECT`), `session_date`, `start_time`, `end_time` (check constraint `end_time > start_time`), `status` (PENDING, CONFIRMED, FAILED, CANCELLED).
  - `Payment`: FK to `BookingRequest` (`on_delete=PROTECT`), `transaction_id` (unique, indexed), `amount`, `status` (PENDING, SUCCESS, FAILED), `provider`, `raw_response`.

---

### Slide 7: Entity Relationship Diagram (ERD)
- **Relationships**:
  - `Parent (1) ─── (N) BookingRequest`
  - `LSAProfile (1) ─── (N) BookingRequest`
  - `LSAProfile (N) ─── (N) Skill` (Normalized Junction Table `lsa_profiles_skills`)
  - `BookingRequest (1) ─── (N) Payment`
- **Integrity**:
  - `models.PROTECT` prevents orphan bookings or payment records if parent/profile is deleted.

---

### Slide 8: Booking Request API (`POST /api/v1/bookings/`)
- **Payload Validation**:
  - Parent & LSA existence check.
  - Active status check for target LSA.
  - Logical time check (`start_time < end_time`).
- **Response Codes**:
  - `201 Created`: Booking created & payment confirmed.
  - `400 Bad Request`: Validation failure / Inactive LSA / Payment failure.
  - `404 Not Found`: Missing Parent or LSA ID.
  - `409 Conflict`: Overlapping time slot for the requested LSA.

---

### Slide 9: Double-Booking Prevention & Concurrency Control
- **Interval Overlap Condition**:
  `start_time < existing.end_time AND end_time > existing.start_time` for active bookings (`CONFIRMED`, `PENDING`).
- **Back-to-Back Bookings**:
  Allowed (e.g. 10:00-11:00 and 11:00-12:00) because 11:00 is not `<` 11:00.
- **Race Condition Prevention**:
  `transaction.atomic()` block combined with `select_for_update()` on the `LSAProfile` row locks the LSA during transaction evaluation.

---

### Slide 10: LSA Search API (`GET /api/v1/lsas/search/`)
- **Endpoint**: `GET /api/v1/lsas/search/?skills=math,science`
- **Features**:
  - Excludes inactive LSAs (`is_active=True`).
  - Supports multi-skill comma-separated filtering.
  - Structured count and results response.

---

### Slide 11: N+1 Query Problem & ORM Optimization
- **The Bad Pattern (N+1)**:
  Looping through LSAs and querying `lsa.skills.all()` executes 1 query for LSAs + N queries for skills.
- **The Solution**:
  `LSAProfile.objects.filter(is_active=True).prefetch_related('skills')`
  Executes exactly **2 SQL queries** regardless of dataset size (1 for LSAs, 1 for M2M Skill join batch).
- **Verification**:
  Automated pytest assertion using `django_assert_num_queries(2)`.

---

### Slide 12: Resilient Payment Gateway Integration & Webhooks
- **Service Abstraction**: `PaymentGatewayService` in `bookings/services/payment_service.py`.
- **Fault Tolerance**:
  - Configurable request timeout (5s).
  - Explicit handling for `requests.Timeout`, `requests.ConnectionError`, and `requests.HTTPError`.
- **Automated Webhook (`POST /api/payments/webhook/`)**:
  - Listens to payment `payment.succeeded` or `payment.failed` events.
  - Dynamically transitions `BookingRequest` state between `PENDING`, `CONFIRMED`, and `FAILED`.
  - Creates and updates audit trail records in `Payment` model.

---

### Slide 13: Testing & Quality Assurance Strategy
- **Framework**: `pytest-django` test suite (28 test cases).
- **Test Scenarios Covered**:
  - Model validations & check constraints (Parent, LSA, Booking, Payment).
  - Booking success, back-to-back acceptance, overlap rejection.
  - 404 & 400 validation error responses.
  - Payment webhook event processing and dynamic booking state transitions.
  - Mock payment gateway success/failure/timeout cases.
  - N+1 query optimization assertion.
- **Code Coverage**: 88% overall coverage.


---

### Slide 14: CI/CD Pipeline (GitHub Actions)
- **Workflow File**: `.github/workflows/tests.yml`
- **Automation Steps**:
  - Live PostgreSQL 16 Alpine container service.
  - Django project system check (`manage.py check`).
  - Migration file consistency check (`manage.py makemigrations --check`).
  - Automated pytest test suite execution with coverage reporting.

---

### Slide 15: Conclusion & Future Enhancements
- **Summary**: Delivered a robust, production-quality, testable Python backend following clean architecture principles.
- **Future Roadmap**:
  - JWT authentication for parents and LSAs (Django REST Framework SimpleJWT).
  - Asynchronous background task processing (Celery + Redis) for email notifications.
  - Real-time WebSocket notifications for booking updates.
