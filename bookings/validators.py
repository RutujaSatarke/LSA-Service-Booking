from datetime import date, time
from typing import Optional
from rest_framework.exceptions import ValidationError
from bookings.models import LSAProfile, BookingRequest


def validate_booking_times(start_time: time, end_time: time) -> None:
    """
    Validate that session end_time is strictly after start_time.
    """
    if start_time >= end_time:
        raise ValidationError({
            "end_time": "Session end time must be strictly after start time."
        })

    
def validate_lsa_active(lsa: LSAProfile) -> None:
    """
    Validate that the requested LSA is active.
    """
    if not lsa.is_active:
        raise ValidationError({
            "lsa_id": f"LSA '{lsa.full_name}' is currently inactive and cannot accept bookings."
        })


def check_booking_overlap(
    lsa_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
    exclude_booking_id: Optional[int] = None
) -> None:
    """
    Check if a booking request overlaps with an existing booking for the same LSA on the same date.
    
    Overlap logic:
      start_time < existing.end_time AND end_time > existing.start_time
      
    Back-to-back bookings (e.g. 10:00-11:00 and 11:00-12:00) do NOT overlap because 11:00 is not < 11:00.
    """
    active_statuses = [
        BookingRequest.Status.CONFIRMED,
        BookingRequest.Status.PENDING,
    ]

    overlapping_query = BookingRequest.objects.filter(
        lsa_id=lsa_id,
        session_date=session_date,
        status__in=active_statuses,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if exclude_booking_id:
        overlapping_query = overlapping_query.exclude(id=exclude_booking_id)

    if overlapping_query.exists():
        raise ValidationError({
            "error": "LSA is already booked during the requested time slot."
        })
