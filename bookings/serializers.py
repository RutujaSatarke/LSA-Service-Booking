from rest_framework import serializers
from bookings.models import Parent, Skill, LSAProfile, BookingRequest, Payment
from bookings.validators import (
    validate_booking_times,
    validate_lsa_active,
    check_booking_overlap,
)



class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['id', 'full_name', 'email', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LSAProfileSerializer(serializers.ModelSerializer):
    skills = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = LSAProfile
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'bio',
            'skills',
            'hourly_rate',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookingRequestCreateSerializer(serializers.Serializer):
    """
    Serializer used for creating a new booking request.
    """
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(),
        source='parent',
        error_messages={
            'does_not_exist': 'Parent with ID {pk_value} does not exist.',
            'incorrect_type': 'Invalid parent ID format.'
        }
    )
    lsa_id = serializers.PrimaryKeyRelatedField(
        queryset=LSAProfile.objects.all(),
        source='lsa',
        error_messages={
            'does_not_exist': 'LSA Profile with ID {pk_value} does not exist.',
            'incorrect_type': 'Invalid LSA ID format.'
        }
    )
    session_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        lsa = attrs.get('lsa')
        session_date = attrs.get('session_date')

        # 1. Validate start_time < end_time
        validate_booking_times(start_time, end_time)

        # 2. Validate LSA is active
        validate_lsa_active(lsa)

        # 3. Check overlapping bookings for the same LSA
        check_booking_overlap(lsa.id, session_date, start_time, end_time)

        return attrs


class BookingRequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer used for detailed output of a booking request.
    """
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)
    lsa_id = serializers.IntegerField(source='lsa.id', read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    lsa_name = serializers.CharField(source='lsa.full_name', read_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            'id',
            'parent_id',
            'parent_name',
            'lsa_id',
            'lsa_name',
            'session_date',
            'start_time',
            'end_time',
            'status',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer representing Payment entity records.
    """
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'booking_id',
            'transaction_id',
            'amount',
            'currency',
            'status',
            'provider',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentWebhookSerializer(serializers.Serializer):
    """
    Serializer validating incoming payment webhook notifications.
    Supports events like 'payment.succeeded', 'payment.failed', or direct status 'SUCCESS' / 'FAILED'.
    """
    booking_id = serializers.IntegerField(
        required=True,
        error_messages={'required': 'booking_id is required.'}
    )
    transaction_id = serializers.CharField(
        required=False,
        allow_blank=True,
        default=None
    )
    event = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    status = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    amount = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        default=None
    )
    provider = serializers.CharField(
        required=False,
        allow_blank=True,
        default='MockPay'
    )

    def validate(self, attrs):
        event = attrs.get('event', '').lower()
        status_val = attrs.get('status', '').upper()

        if not event and not status_val:
            raise serializers.ValidationError({
                'event': 'Either event or status field must be provided in payment webhook payload.'
            })
        return attrs

