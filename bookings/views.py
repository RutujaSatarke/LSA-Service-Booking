import logging
import uuid
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, views, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import exception_handler
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer

from bookings.models import LSAProfile, BookingRequest, Parent, Payment
from bookings.serializers import (
    ParentSerializer,
    LSAProfileSerializer,
    BookingRequestCreateSerializer,
    BookingRequestDetailSerializer,
    PaymentSerializer,
    PaymentWebhookSerializer,
)
from bookings.selectors import get_active_lsas_by_skills
from bookings.services import PaymentGatewayService


logger = logging.getLogger('bookings')


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler providing consistent, clean error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize validation error output
        if isinstance(response.data, dict) and 'detail' not in response.data and 'error' not in response.data:
            first_error = next(iter(response.data.values()))
            if isinstance(first_error, list) and first_error:
                error_msg = str(first_error[0])
            else:
                error_msg = str(first_error)
            response.data = {"error": error_msg, "details": response.data}
        elif isinstance(response.data, dict) and 'detail' in response.data:
            response.data = {"error": str(response.data['detail'])}
        return response

    # Handle unhandled exceptions
    if isinstance(exc, ObjectDoesNotExist):
        logger.warning(f"Resource not found: {str(exc)}")
        return Response(
            {"error": "The requested resource was not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    elif isinstance(exc, IntegrityError):
        logger.error(f"Database integrity error: {str(exc)}")
        return Response(
            {"error": "Database constraint violation occurred."},
            status=status.HTTP_400_BAD_REQUEST
        )

    logger.exception(f"Unhandled exception in API view: {str(exc)}")
    return Response(
        {"error": "An internal server error occurred. Please try again later."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


class LSASearchView(views.APIView):
    """
    Search active LSAs by required skills.
    
    Prevents N+1 query problem by prefetching related skill entities.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Search active LSAs by skills",
        parameters=[
            OpenApiParameter(
                name="skills",
                type=str,
                description="Comma-separated skill names (e.g. math,science)",
                required=False
            )
        ],
        responses={200: LSAProfileSerializer(many=True)}
    )
    def get(self, request):
        skills_param = request.query_params.get('skills', None)
        skill_list = [s.strip() for s in skills_param.split(',')] if skills_param else None

        lsas_queryset = get_active_lsas_by_skills(skill_list)
        serializer = LSAProfileSerializer(lsas_queryset, many=True)

        return Response({
            "count": len(serializer.data),
            "results": serializer.data
        }, status=status.HTTP_200_OK)


class BookingCreateView(views.APIView):
    """
    Create a new LSA booking request and trigger mock payment processing.
    
    Includes robust double-booking prevention via transaction atomic locks and ORM validation.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Create LSA Booking Request",
        request=BookingRequestCreateSerializer,
        responses={
            201: BookingRequestDetailSerializer,
            400: OpenApiResponse(description="Bad Request / Invalid Data"),
            404: OpenApiResponse(description="Parent or LSA Not Found"),
            409: OpenApiResponse(description="Overlapping Booking Conflict"),
        }
    )
    def post(self, request):
        serializer = BookingRequestCreateSerializer(data=request.data)
        if not serializer.is_validated_by_rf(request):
            # Formatted validation response
            errors = serializer.errors
            logger.warning(f"Booking validation failed: {errors}")
            
            # Check for conflict error message
            if 'error' in errors:
                return Response({"error": errors['error'][0]}, status=status.HTTP_409_CONFLICT)
            
            # Check for not found error messages
            for field in ['parent_id', 'lsa_id']:
                if field in errors and any("does not exist" in str(e) for e in errors[field]):
                    return Response({"error": errors[field][0]}, status=status.HTTP_404_NOT_FOUND)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        parent = validated_data['parent']
        lsa = validated_data['lsa']
        session_date = validated_data['session_date']
        start_time = validated_data['start_time']
        end_time = validated_data['end_time']
        notes = validated_data.get('notes', '')

        # Use atomic transaction and row locking for double-booking concurrency protection
        try:
            with transaction.atomic():
                # Lock the target LSA row to ensure concurrent booking requests execute serially
                locked_lsa = LSAProfile.objects.select_for_update().get(id=lsa.id)
                
                # Re-verify overlap inside lock to prevent race conditions
                from bookings.validators import check_booking_overlap
                check_booking_overlap(locked_lsa.id, session_date, start_time, end_time)

                booking = BookingRequest.objects.create(
                    parent=parent,
                    lsa=locked_lsa,
                    session_date=session_date,
                    start_time=start_time,
                    end_time=end_time,
                    status=BookingRequest.Status.PENDING,
                    notes=notes
                )
                logger.info(f"Booking #{booking.id} created with status PENDING for Parent #{parent.id} and LSA #{locked_lsa.id}")

        except Exception as exc:
            if "already booked" in str(exc):
                return Response({"error": "LSA is already booked during the requested time."}, status=status.HTTP_409_CONFLICT)
            raise exc

        # Trigger mock payment service
        payment_service = PaymentGatewayService()
        payment_result = payment_service.process_payment(
            booking_id=booking.id,
            amount=locked_lsa.hourly_rate
        )

        if payment_result["success"]:
            booking.status = BookingRequest.Status.CONFIRMED
            booking.save(update_fields=['status', 'updated_at'])
            
            # Record Payment entity
            Payment.objects.create(
                booking=booking,
                transaction_id=payment_result.get("transaction_id") or f"TXN-MOCK-{booking.id}",
                amount=locked_lsa.hourly_rate,
                currency='USD',
                status=Payment.Status.SUCCESS,
                provider='MockPay',
                raw_response=payment_result
            )
            
            logger.info(f"Booking #{booking.id} status updated to CONFIRMED following successful payment.")
            
            response_serializer = BookingRequestDetailSerializer(booking)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            booking.status = BookingRequest.Status.FAILED
            booking.save(update_fields=['status', 'updated_at'])
            
            # Record failed Payment entity
            Payment.objects.create(
                booking=booking,
                transaction_id=f"TXN-FAILED-{booking.id}-{uuid.uuid4().hex[:6]}",
                amount=locked_lsa.hourly_rate,
                currency='USD',
                status=Payment.Status.FAILED,
                provider='MockPay',
                raw_response=payment_result
            )
            
            logger.warning(f"Booking #{booking.id} payment failed: {payment_result.get('error')}. Status set to FAILED.")
            
            return Response({
                "error": f"Booking payment failed: {payment_result.get('error')}",
                "booking_id": booking.id,
                "status": booking.status
            }, status=status.HTTP_400_BAD_REQUEST)

    # DRF helper compatibility check
    def _is_validated(self, serializer, request):
        return serializer.is_valid()


# Adding method directly to BookingCreateView helper
def _is_validated_by_rf(self, request):
    return self.is_valid()

BookingRequestCreateSerializer.is_validated_by_rf = _is_validated_by_rf


class PaymentWebhookView(views.APIView):
    """
    Automated Webhook Endpoint listening to payment success/failure events.
    
    Dynamically transitions BookingRequest states and maintains audit records in Payment entity.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Automated Payment Webhook Endpoint",
        description="Listens to external payment webhook events (e.g. payment.succeeded, payment.failed) and dynamically transitions booking states.",
        request=PaymentWebhookSerializer,
        responses={
            200: OpenApiResponse(description="Webhook Processed & State Transitioned"),
            400: OpenApiResponse(description="Invalid Webhook Payload or Unsupported Event"),
            404: OpenApiResponse(description="Booking Request Not Found"),
        }
    )
    def post(self, request):
        serializer = PaymentWebhookSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Payment webhook validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        booking_id = validated_data['booking_id']
        event = validated_data.get('event', '').lower()
        status_field = validated_data.get('status', '').upper()
        transaction_id = validated_data.get('transaction_id')
        amount = validated_data.get('amount')
        provider = validated_data.get('provider', 'MockPay')

        try:
            booking = BookingRequest.objects.select_related('lsa', 'parent').get(id=booking_id)
        except BookingRequest.DoesNotExist:
            logger.warning(f"Webhook received for non-existent Booking #{booking_id}")
            return Response(
                {"error": f"Booking request with ID {booking_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        is_success = (
            event in ['payment.succeeded', 'payment_success', 'charge.succeeded', 'success']
            or status_field in ['SUCCESS', 'APPROVED', 'CONFIRMED']
        )
        is_failure = (
            event in ['payment.failed', 'payment_failure', 'charge.failed', 'failure', 'failed']
            or status_field in ['FAILED', 'DECLINED', 'REJECTED']
        )

        if not is_success and not is_failure:
            return Response(
                {"error": f"Unsupported or unrecognized webhook event type: '{event or status_field}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_booking_status = BookingRequest.Status.CONFIRMED if is_success else BookingRequest.Status.FAILED
        payment_status = Payment.Status.SUCCESS if is_success else Payment.Status.FAILED

        txn_id = transaction_id or f"TXN-WEBHOOK-{booking.id}-{uuid.uuid4().hex[:8]}"
        pay_amount = amount if amount is not None else booking.lsa.hourly_rate

        with transaction.atomic():
            booking.status = new_booking_status
            booking.save(update_fields=['status', 'updated_at'])

            payment, _ = Payment.objects.update_or_create(
                transaction_id=txn_id,
                defaults={
                    'booking': booking,
                    'amount': pay_amount,
                    'currency': 'USD',
                    'status': payment_status,
                    'provider': provider,
                    'raw_response': request.data,
                }
            )

        logger.info(
            f"Webhook successfully transitioned Booking #{booking.id} to {new_booking_status} "
            f"(Payment ID #{payment.id}, Txn: {txn_id})"
        )

        return Response({
            "message": f"Payment webhook processed successfully. Booking #{booking.id} state updated to {new_booking_status}.",
            "booking_id": booking.id,
            "booking_status": booking.status,
            "payment_id": payment.id,
            "transaction_id": payment.transaction_id,
            "payment_status": payment.status,
        }, status=status.HTTP_200_OK)


class MockPaymentGatewayView(views.APIView):
    """
    Mock endpoint simulating external payment gateway behavior.
    Used for end-to-end integration testing and local simulation.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Mock Payment Gateway Endpoint",
        description="Simulates processing a payment charge for testing.",
        request=inline_serializer(
            name="MockPaymentRequestSerializer",
            fields={
                "booking_id": serializers.IntegerField(),
                "amount": serializers.DecimalField(max_digits=8, decimal_places=2),
            }
        ),
        responses={200: OpenApiResponse(description="Simulated Payment Success Result")}
    )
    def post(self, request):
        booking_id = request.data.get('booking_id')
        amount = request.data.get('amount')
        
        # Simulate payment status based on test header or booking ID
        if request.headers.get('X-Simulate-Payment-Fail') == 'true':
            return Response({
                "success": False,
                "error": "Payment declined by issuing bank."
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "transaction_id": f"TXN-MOCK-SUCCESS-{booking_id}",
            "amount": amount,
            "status": "APPROVED"
        }, status=status.HTTP_200_OK)

