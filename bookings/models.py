from decimal import Decimal
from django.core.validators import MinValueValidator, EmailValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Parent(models.Model):
    """
    Parent model representing a client booking LSAs for children.
    """
    full_name = models.CharField(max_length=255, verbose_name=_("Full Name"))
    email = models.EmailField(
        unique=True,
        db_index=True,
        validators=[EmailValidator()],
        verbose_name=_("Email Address")
    )
    phone = models.CharField(max_length=30, verbose_name=_("Phone Number"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Parent")
        verbose_name_plural = _("Parents")
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class Skill(models.Model):
    """
    Normalized Skill model for multi-skill assignment to LSA Profiles.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_("Skill Name")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class LSAProfile(models.Model):
    """
    Learning Support Assistant (LSA) Profile model.
    """
    full_name = models.CharField(max_length=255, verbose_name=_("Full Name"))
    email = models.EmailField(
        unique=True,
        db_index=True,
        validators=[EmailValidator()],
        verbose_name=_("Email Address")
    )
    phone = models.CharField(max_length=30, verbose_name=_("Phone Number"))
    bio = models.TextField(blank=True, verbose_name=_("Bio"))
    skills = models.ManyToManyField(
        Skill,
        related_name='lsas',
        blank=True,
        verbose_name=_("Skills")
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_("Hourly Rate ($)")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Active Status")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("LSA Profile")
        verbose_name_plural = _("LSA Profiles")
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hourly_rate__gt=0),
                name='hourly_rate_positive'
            )
        ]

    def __str__(self) -> str:
        return f"{self.full_name} - ${self.hourly_rate}/hr ({'Active' if self.is_active else 'Inactive'})"


class BookingRequest(models.Model):
    """
    Booking request connecting a Parent with an LSA Profile for a specific time session.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        FAILED = 'FAILED', _('Failed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    parent = models.ForeignKey(
        Parent,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name=_("Parent")
    )
    lsa = models.ForeignKey(
        LSAProfile,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name=_("LSA Profile")
    )
    session_date = models.DateField(db_index=True, verbose_name=_("Session Date"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Booking Request")
        verbose_name_plural = _("Booking Requests")
        ordering = ['-session_date', 'start_time']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='booking_end_after_start'
            )
        ]
        indexes = [
            models.Index(fields=['session_date', 'lsa'], name='booking_date_lsa_idx'),
            models.Index(fields=['status'], name='booking_status_idx'),
        ]

    def __str__(self) -> str:
        return f"Booking #{self.id}: Parent={self.parent.full_name}, LSA={self.lsa.full_name}, Date={self.session_date} ({self.start_time}-{self.end_time}) [{self.status}]"


class Payment(models.Model):
    """
    Payment model representing financial transactions associated with Booking Requests.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SUCCESS = 'SUCCESS', _('Success')
        FAILED = 'FAILED', _('Failed')

    booking = models.ForeignKey(
        BookingRequest,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_("Booking Request")
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_("Transaction ID")
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_("Amount ($)")
    )
    currency = models.CharField(
        max_length=10,
        default='USD',
        verbose_name=_("Currency")
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status")
    )
    provider = models.CharField(
        max_length=50,
        default='MockPay',
        verbose_name=_("Payment Provider")
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Raw Provider Response")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id'], name='payment_txn_idx'),
            models.Index(fields=['status'], name='payment_status_idx'),
        ]

    def __str__(self) -> str:
        return f"Payment #{self.id} for Booking #{self.booking_id}: ${self.amount} [{self.status}] ({self.transaction_id})"

