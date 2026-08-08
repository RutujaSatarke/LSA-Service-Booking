from decimal import Decimal
from datetime import date, time
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from bookings.models import Parent, Skill, LSAProfile, BookingRequest, Payment


@pytest.mark.django_db
class TestParentModel:
    def test_parent_creation_and_str(self):
        parent = Parent.objects.create(
            full_name="Mark Smith",
            email="mark.smith@example.com",
            phone="+123456789"
        )
        assert parent.id is not None
        assert str(parent) == "Mark Smith (mark.smith@example.com)"

    def test_parent_email_uniqueness(self):
        Parent.objects.create(
            full_name="Parent 1",
            email="duplicate@example.com",
            phone="+123456789"
        )
        with pytest.raises(IntegrityError):
            Parent.objects.create(
                full_name="Parent 2",
                email="duplicate@example.com",
                phone="+987654321"
            )


@pytest.mark.django_db
class TestSkillModel:
    def test_skill_creation_and_str(self):
        skill = Skill.objects.create(name="Phonics", description="Phonics intervention")
        assert skill.id is not None
        assert str(skill) == "Phonics"


@pytest.mark.django_db
class TestLSAProfileModel:
    def test_lsa_creation_and_str(self):
        lsa = LSAProfile.objects.create(
            full_name="Clara Oswald",
            email="clara@example.com",
            phone="+1122334455",
            hourly_rate=Decimal("35.00"),
            is_active=True
        )
        assert lsa.id is not None
        assert "$35.00/hr" in str(lsa)

    def test_hourly_rate_validation(self):
        lsa = LSAProfile(
            full_name="Invalid LSA",
            email="invalid@example.com",
            phone="+1122334455",
            hourly_rate=Decimal("-10.00"),
            is_active=True
        )
        with pytest.raises(ValidationError):
            lsa.full_clean()


@pytest.mark.django_db
class TestBookingRequestModel:
    def test_booking_creation_and_str(self, parent, active_lsa):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 25),
            start_time=time(14, 0, 0),
            end_time=time(15, 0, 0),
            status=BookingRequest.Status.CONFIRMED
        )
        assert booking.id is not None
        assert f"Booking #{booking.id}" in str(booking)

    def test_booking_end_time_must_be_after_start_time(self, parent, active_lsa):
        booking = BookingRequest(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 25),
            start_time=time(15, 0, 0),
            end_time=time(14, 0, 0),  # End time before start time
            status=BookingRequest.Status.PENDING
        )
        # Model full_clean validation should fail
        with pytest.raises(ValidationError):
            booking.full_clean()


@pytest.mark.django_db
class TestPaymentModel:
    def test_payment_creation_and_str(self, parent, active_lsa):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 25),
            start_time=time(10, 0, 0),
            end_time=time(11, 0, 0),
            status=BookingRequest.Status.CONFIRMED
        )
        payment = Payment.objects.create(
            booking=booking,
            transaction_id="TXN-TEST-12345",
            amount=Decimal("25.00"),
            currency="USD",
            status=Payment.Status.SUCCESS,
            provider="MockPay"
        )
        assert payment.id is not None
        assert str(payment) == f"Payment #{payment.id} for Booking #{booking.id}: $25.00 [SUCCESS] (TXN-TEST-12345)"

    def test_payment_transaction_id_uniqueness(self, parent, active_lsa):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 25),
            start_time=time(11, 0, 0),
            end_time=time(12, 0, 0),
            status=BookingRequest.Status.CONFIRMED
        )
        Payment.objects.create(
            booking=booking,
            transaction_id="TXN-DUP-001",
            amount=Decimal("25.00"),
            status=Payment.Status.SUCCESS
        )
        with pytest.raises(IntegrityError):
            Payment.objects.create(
                booking=booking,
                transaction_id="TXN-DUP-001",
                amount=Decimal("25.00"),
                status=Payment.Status.SUCCESS
            )

