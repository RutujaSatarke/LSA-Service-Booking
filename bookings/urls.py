from django.urls import path
from bookings.views import (
    BookingCreateView,
    LSASearchView,
    MockPaymentGatewayView,
    PaymentWebhookView,
)

app_name = 'bookings'

urlpatterns = [
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
    path('lsas/search/', LSASearchView.as_view(), name='lsa-search'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    path('payments/mock/', MockPaymentGatewayView.as_view(), name='payment-mock'),
]

