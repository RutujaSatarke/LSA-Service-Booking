from decimal import Decimal
from unittest.mock import patch
import pytest
import requests
from bookings.services import PaymentGatewayService


class TestPaymentGatewayService:
    def setup_method(self):
        self.service = PaymentGatewayService()

    @patch('bookings.services.payment_service.requests.post')
    def test_process_payment_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "transaction_id": "TXN-SUCCESS-999"
        }

        result = self.service.process_payment(booking_id=1, amount=Decimal("50.00"))

        assert result["success"] is True
        assert result["transaction_id"] == "TXN-SUCCESS-999"

    @patch('bookings.services.payment_service.requests.post')
    def test_process_payment_timeout(self, mock_post):
        mock_post.side_effect = requests.Timeout("Gateway timed out")

        result = self.service.process_payment(booking_id=1, amount=Decimal("50.00"))

        assert result["success"] is False
        assert result["transaction_id"] is None
        assert "timed out" in result["error"].lower()

    @patch('bookings.services.payment_service.requests.post')
    def test_process_payment_connection_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        result = self.service.process_payment(booking_id=1, amount=Decimal("50.00"))

        assert result["success"] is False
        assert result["transaction_id"] is None
        assert "connect" in result["error"].lower()

    @patch('bookings.services.payment_service.requests.post')
    def test_process_payment_http_error(self, mock_post):
        mock_response = requests.Response()
        mock_response.status_code = 400
        mock_response._content = b'{"error": "Insufficient funds"}'
        mock_post.side_effect = requests.HTTPError(response=mock_response)

        result = self.service.process_payment(booking_id=1, amount=Decimal("50.00"))

        assert result["success"] is False
        assert result["transaction_id"] is None
        assert "rejected" in result["error"].lower()
