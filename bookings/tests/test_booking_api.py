from datetime import date, time
from unittest.mock import patch
import pytest
from rest_framework import status
from django.urls import reverse
from bookings.models import BookingRequest


@pytest.mark.django_db
class TestBookingAPI:
    def setup_method(self):
        self.url = reverse('bookings:booking-create')

    @patch('bookings.services.payment_service.requests.post')
    def test_booking_success(self, mock_post, api_client, parent, active_lsa):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "transaction_id": "TXN-TEST-123"
        }

        payload = {
            "parent_id": parent.id,
            "lsa_id": active_lsa.id,
            "session_date": "2026-08-15",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "notes": "Math support session"
        }

        response = api_client.post(self.url, payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["parent_id"] == parent.id
        assert response.data["lsa_id"] == active_lsa.id
        assert response.data["status"] == BookingRequest.Status.CONFIRMED

    def test_non_existent_parent(self, api_client, active_lsa):
        payload = {
            "parent_id": 99999,
            "lsa_id": active_lsa.id,
            "session_date": "2026-08-15",
            "start_time": "10:00:00",
            "end_time": "11:00:00"
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_existent_lsa(self, api_client, parent):
        payload = {
            "parent_id": parent.id,
            "lsa_id": 99999,
            "session_date": "2026-08-15",
            "start_time": "10:00:00",
            "end_time": "11:00:00"
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inactive_lsa_rejection(self, api_client, parent, inactive_lsa):
        payload = {
            "parent_id": parent.id,
            "lsa_id": inactive_lsa.id,
            "session_date": "2026-08-15",
            "start_time": "10:00:00",
            "end_time": "11:00:00"
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "inactive" in str(response.data).lower()

    def test_end_time_before_start_time(self, api_client, parent, active_lsa):
        payload = {
            "parent_id": parent.id,
            "lsa_id": active_lsa.id,
            "session_date": "2026-08-15",
            "start_time": "11:00:00",
            "end_time": "10:00:00"
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_overlapping_booking_rejection(self, api_client, parent, active_lsa, existing_booking):
        # Existing booking is on 2026-08-20 from 10:00:00 to 11:00:00
        # Request overlapping 10:30 to 11:30
        payload = {
            "parent_id": parent.id,
            "lsa_id": active_lsa.id,
            "session_date": "2026-08-20",
            "start_time": "10:30:00",
            "end_time": "11:30:00"
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already booked" in str(response.data).lower()

    @patch('bookings.services.payment_service.requests.post')
    def test_back_to_back_booking_acceptance(self, mock_post, api_client, parent, active_lsa, existing_booking):
        # Existing booking is 10:00 to 11:00
        # Request back-to-back 11:00 to 12:00 -> should be ACCEPTED
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True, "transaction_id": "TXN-B2B-123"}

        payload = {
            "parent_id": parent.id,
            "lsa_id": active_lsa.id,
            "session_date": "2026-08-20",
            "start_time": "11:00:00",
            "end_time": "12:00:00"
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == BookingRequest.Status.CONFIRMED
