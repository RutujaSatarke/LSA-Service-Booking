import logging
from decimal import Decimal
from typing import Dict, Any
import requests
from django.conf import settings

logger = logging.getLogger('bookings')


class PaymentProcessingError(Exception):
    """Custom exception raised when payment gateway fails or encounters error."""
    pass


class PaymentGatewayService:
    """
    Service layer handling external payment gateway integrations.
    """

    def __init__(self, api_url: str = None, timeout: int = 5):
        self.api_url = api_url or getattr(settings, 'PAYMENT_API_URL', 'https://api.habotconnect-mock-payment.com/v1/charge')
        self.timeout = timeout

    def process_payment(self, booking_id: int, amount: Decimal, currency: str = 'USD') -> Dict[str, Any]:
        """
        Process payment for a given booking request via external payment service.

        :param booking_id: ID of the booking request
        :param amount: Amount to charge
        :param currency: Currency code
        :return: Dict containing 'success', 'transaction_id', and optional 'error'
        """
        payload = {
            "booking_id": booking_id,
            "amount": str(amount),
            "currency": currency,
        }

        logger.info(f"Initiating payment processing for Booking #{booking_id}, Amount: ${amount}")

        # If using mock URL in dev/testing, return simulated response or execute request
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Payment successful for Booking #{booking_id}. Transaction ID: {data.get('transaction_id')}")
            return {
                "success": True,
                "transaction_id": data.get("transaction_id", f"TXN-MOCK-{booking_id}"),
                "message": "Payment processed successfully",
            }

        except requests.Timeout as exc:
            logger.error(f"Payment request timed out for Booking #{booking_id}: {str(exc)}")
            return {
                "success": False,
                "transaction_id": None,
                "error": "Payment service request timed out. Please try again.",
            }

        except requests.ConnectionError as exc:
            logger.error(f"Payment service connection failed for Booking #{booking_id}: {str(exc)}")
            return {
                "success": False,
                "transaction_id": None,
                "error": "Unable to connect to payment gateway.",
            }

        except requests.HTTPError as exc:
            logger.error(f"Payment HTTP error {exc.response.status_code} for Booking #{booking_id}: {exc.response.text}")
            return {
                "success": False,
                "transaction_id": None,
                "error": f"Payment gateway rejected request: {exc.response.text or 'HTTP error'}",
            }

        except requests.RequestException as exc:
            logger.error(f"Unexpected payment gateway request exception for Booking #{booking_id}: {str(exc)}")
            return {
                "success": False,
                "transaction_id": None,
                "error": "An unexpected error occurred during payment processing.",
            }

        except Exception as exc:
            logger.exception(f"Unexpected error processing payment for Booking #{booking_id}: {str(exc)}")
            return {
                "success": False,
                "transaction_id": None,
                "error": str(exc),
            }
