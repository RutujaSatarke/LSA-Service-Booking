# Hiring Project Form | Position: Python Backend Developer
**Company**: Habot 1.0 (HabotConnect)  
**Date**: 280726 | **Page**: 1 to 4  
**Submission Deadline**: 13th August 2026  
**Submission Link**: https://forms.gle/YzHDkd23ApzpP2ze7  

---

## 1. Why Are We Doing This Project? (Meaning & Purpose)
- This hiring project is a **reality-mimicking simulation** that recreates the most challenging day on the job, testing your ability to solve real production-level problems instead of theoretical questions.
- The assessment evaluates your ability to independently analyze ambiguous requirements, use documentation effectively, and design secure, reliable, and structured technical solutions without micromanagement.
- It also measures your ability to build automated, mistake-proof (**Poka-Yoke**) systems that protect data integrity and enforce operational standards through robust design rather than human memory.

---

## 2. What Will Be the Outcome of the Project?
The candidate will deliver a **production-ready backend prototype** consisting of:
1. A **normalized and indexed relational schema** containing `Parent`, `LSA` (`LSAProfile`), `Booking` (`BookingRequest`), and `Payment` entities.
2. A **high-performance query** optimized to fetch available LSAs, resolving the **N+1 database problem**.
3. A **robust booking API** (`/api/bookings/` or `/api/v1/bookings/`) with built-in validation preventing overlapping sessions (double-bookings).
4. An **automated webhook endpoint** (`/api/payments/webhook/` or `/api/v1/payments/webhook/`) that listens to payment success/failure events and dynamically transitions booking states.
5. An **automated test suite** containing at least 5 Pytest or unittest test cases.
6. A technical `README.md` clearly explaining design choices (MVC vs. MVT) and setup instructions.

---

## 3. Must Know
Hiring at HabotConnect is a demanding process. Typically 1 out of 180+ candidates are accepted. You must show that you know your work.  
If you wish to be a HaboTech, you must know its:
1. **Values**
2. **Leadership Principles**

---

## 4. Project Context
HabotConnect is building a 100% remote digital platform connecting parents with Learning Support Assistants (LSAs) for children with learning difficulties. To ensure reliable data flow across our platform, our backend infrastructure requires modular, lightweight RESTful APIs built on Python and Django/Flask. This simulation tests your ability to convert functional requirements into clean backend architecture, optimized queries, and reliable API endpoints.

---

## 5. You Will Be Assessed On
1. **Core Python & Framework Proficiency**: Clean execution of Object-Oriented Programming (OOP), exception handling, and framework architecture (Django MVT / Flask MVC).
2. **RESTful API Design & DRF/Flask-RESTful Integration**: Proper structure of endpoints, status codes, request/response validation, and integration with external mock services.
3. **Database Schema Design & Query Optimization**: Effective relational database modeling (PostgreSQL/MySQL), ORM query efficiency, and handling database migrations.
4. **Automated Testing & Diagnostic Skills**: Comprehensive unit/integration tests (`pytest` or `unittest`) and robust debugging/logging capabilities.
5. **Documentation & Version Control Discipline**: Clear technical documentation, API specifications, and structured Git pull request/branching workflow.

---

## 6. You are Expected To Do
- **Database Schema & ORM Setup**: Design a database schema for an LSA Service Booking module containing entities (`Parent`, `LSA_Profile`, `Booking_Request`, `Payment`). Write Django ORM or SQLAlchemy models with appropriate data types, relationships, and migration scripts.
- **RESTful API Endpoint Implementation**: Build working REST API endpoints using Django REST Framework (DRF) or Flask-RESTful:
  - `POST /api/v1/bookings/`: Accepts a booking request, validates payload inputs, and stores it in the database.
  - `GET /api/v1/lsas/search/`: Retrieves available LSAs filtered by skills, ensuring the SQL/ORM query is optimized (e.g. avoiding $N+1$ query problems).
  - `POST /api/v1/payments/webhook/`: Webhook endpoint processing external payment events (`payment.succeeded`, `payment.failed`) and updating booking status.
- **Third-Party Mock Integration**: Integrate a mock external service (e.g., a payment gateway or verification API) using Python's `requests` library with proper exception handling and logging.
- **Automated Unit Testing & CI/CD Pipeline**: Write automated unit tests using `pytest` or `unittest` covering success, edge, and failure cases. Create a basic GitHub Actions YAML workflow script to run tests on push.
- **Technical Documentation**: Write concise technical documentation detailing setup instructions, API specifications, database relationships, and query optimization choices.

---

## 7. Submission Is To Be
1. Provide a link to a public GitHub/GitLab repository containing your clean Python codebase, database models, API routes, unit tests, and GitHub Actions workflow.
2. Include a comprehensive `README.md` file in the repository with clear setup instructions, API endpoint documentation, and explanation of query optimizations.
3. Prepare a Google Slides / PowerPoint presentation (Maximum 15 slides) summarizing your architectural decisions, database design, API structures, and test coverage.

### Your presentation / Submission should include the following:
- Present each of the above tasks clearly using your slide presentation.
- Explain your technical choices and query optimization logic.
- All spreadsheet cells or table entries (if submitting supporting sheets) must have "Wrap Text" enabled for full visibility and use full forms only.
- Ensure your codebase, presentation, and answer documents are clearly labeled with your full name and contact information at the top.

---

## 8. Suggestions & Guidelines
- **Timeframe**: The project should take you 4 to 6 hours maximum to complete.
- **Resources**: You are expected to use outside resources to help you understand what is required (e.g., basic platform logic principles).
- **Independence**: Show us that you can do what is required by us without supervision. No company resource person will be available to assist you.
- **Self-Screening**: Use this opportunity to find out whether you truly want to work within HabotConnect's highly accountable, detail-obsessed, "Quiet Management" remote culture.

---

## 9. Presentation Details
- **When**: You will present your completed project during the Project Interview phase.
- **Where**: Video call presentation via Google Meet. You will receive a calendar invite with the date and time from our Human Resources team members.
- **Who**: You will be presenting to panel members which may include the CEO, Team Lead, and Human Resources team members.
- **How**: Slide presentation with links to your code repository or live demo. Maximum of 15 slides.

---

## 10. Additional HabotConnect Resource Links
- **The Leadership Principles**: `Leadership Principles -HAW 3 2025-271124.pdf`
- **HabotConnect Values**: `Habot- Values-HAW3-291124.pdf`
