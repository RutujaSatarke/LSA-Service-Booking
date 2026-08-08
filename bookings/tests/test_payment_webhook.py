from datetime import date, time
from decimal import Decimal
import pytest
from rest_framework import status
from bookings.models import BookingRequest, Payment


@pytest.mark.django_db
class TestPaymentWebhookAPI:
    """
    Test cases for the automated payment webhook endpoint (/api/payments/webhook/).
    """

    def test_webhook_payment_success_transitions_booking_to_confirmed(self, api_client, parent, active_lsa):
        # Create a pending booking
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 30),
            start_time=time(10, 0, 0),
            end_time=time(11, 0, 0),
            status=BookingRequest.Status.PENDING
        )

        payload = {
            "booking_id": booking.id,
            "transaction_id": "TXN-WH-SUCCESS-001",
            "event": "payment.succeeded",
            "amount": "30.00",
            "provider": "Stripe"
        }

        response = api_client.post('/api/payments/webhook/', data=payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["booking_status"] == BookingRequest.Status.CONFIRMED
        assert response.data["payment_status"] == Payment.Status.SUCCESS

        # Verify database state transition
        booking.refresh_from_db()
        assert booking.status == BookingRequest.Status.CONFIRMED

        # Verify payment entity created
        payment = Payment.objects.get(transaction_id="TXN-WH-SUCCESS-001")
        assert payment.booking_id == booking.id
        assert payment.amount == Decimal("30.00")
        assert payment.status == Payment.Status.SUCCESS
        assert payment.provider == "Stripe"

    def test_webhook_payment_failure_transitions_booking_to_failed(self, api_client, parent, active_lsa):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 30),
            start_time=time(12, 0, 0),
            end_time=time(13, 0, 0),
            status=BookingRequest.Status.PENDING
        )

        payload = {
            "booking_id": booking.id,
            "transaction_id": "TXN-WH-FAIL-001",
            "event": "payment.failed",
            "amount": "30.00"
        }

        response = api_client.post('/api/payments/webhook/', data=payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["booking_status"] == BookingRequest.Status.FAILED

        booking.refresh_from_db()
        assert booking.status == BookingRequest.Status.FAILED

        payment = Payment.objects.get(transaction_id="TXN-WH-FAIL-001")
        assert payment.status == Payment.Status.FAILED

    def test_webhook_non_existent_booking_returns_404(self, api_client):
        payload = {
            "booking_id": 99999,
            "event": "payment.succeeded",
            "transaction_id": "TXN-404"
        }
        response = api_client.post('/api/payments/webhook/', data=payload, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "does not exist" in response.data["error"]

    def test_webhook_missing_required_fields_returns_400(self, api_client):
        payload = {
            "transaction_id": "TXN-NO-BOOKING"
        }
        response = api_client.post('/api/payments/webhook/', data=payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_unsupported_event_returns_400(self, api_client, parent, active_lsa):
        booking = BookingRequest.objects.create(
            parent=parent,
            lsa=active_lsa,
            session_date=date(2026, 8, 30),
            start_time=time(14, 0, 0),
            end_time=time(15, 0, 0),
            status=BookingRequest.Status.PENDING
        )
        payload = {
            "booking_id": booking.id,
            "event": "unknown_event_type"
        }
        response = api_client.post('/api/payments/webhook/', data=payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
