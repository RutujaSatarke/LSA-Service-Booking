from decimal import Decimal
from datetime import date, time
import pytest
from rest_framework.test import APIClient
from bookings.models import Parent, Skill, LSAProfile, BookingRequest


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def parent(db):
    return Parent.objects.create(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1234567890"
    )


@pytest.fixture
def math_skill(db):
    return Skill.objects.create(name="Math", description="Mathematics assistance")


@pytest.fixture
def science_skill(db):
    return Skill.objects.create(name="Science", description="Science assistance")


@pytest.fixture
def speech_skill(db):
    return Skill.objects.create(name="Speech Therapy", description="Speech intervention")


@pytest.fixture
def active_lsa(db, math_skill, science_skill):
    lsa = LSAProfile.objects.create(
        full_name="David Miller",
        email="david.m@lsa.example.com",
        phone="+1987654321",
        bio="Experienced math and science assistant.",
        hourly_rate=Decimal("30.00"),
        is_active=True
    )
    lsa.skills.set([math_skill, science_skill])
    return lsa


@pytest.fixture
def inactive_lsa(db, math_skill):
    lsa = LSAProfile.objects.create(
        full_name="Emily Davis",
        email="emily.d@lsa.example.com",
        phone="+1987654322",
        bio="Inactive profile",
        hourly_rate=Decimal("28.00"),
        is_active=False
    )
    lsa.skills.set([math_skill])
    return lsa


@pytest.fixture
def existing_booking(db, parent, active_lsa):
    return BookingRequest.objects.create(
        parent=parent,
        lsa=active_lsa,
        session_date=date(2026, 8, 20),
        start_time=time(10, 0, 0),
        end_time=time(11, 0, 0),
        status=BookingRequest.Status.CONFIRMED,
        notes="Existing math session"
    )
