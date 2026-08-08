from typing import Optional, List
from django.db.models import QuerySet
from bookings.models import LSAProfile, BookingRequest


def get_active_lsas_by_skills(skill_names: Optional[List[str]] = None) -> QuerySet[LSAProfile]:
    """
    Retrieve active LSAs, optionally filtered by skill names, with skills prefetched to avoid N+1 queries.
    
    :param skill_names: List of skill names to filter by (e.g., ['math', 'science'])
    :return: Optimized QuerySet of active LSAProfile instances
    """
    queryset = LSAProfile.objects.filter(is_active=True).prefetch_related('skills')

    if skill_names:
        # Clean and split skills if comma separated or list passed
        cleaned_skills = []
        for name in skill_names:
            cleaned_skills.extend([s.strip().lower() for s in name.split(',') if s.strip()])
        
        if cleaned_skills:
            queryset = queryset.filter(skills__name__iregex=r'(' + '|'.join(cleaned_skills) + r')').distinct()

    return queryset.order_by('id')


def get_booking_by_id(booking_id: int) -> Optional[BookingRequest]:
    """
    Retrieve a booking by ID with parent and lsa relationships pre-selected.
    """
    try:
        return BookingRequest.objects.select_related('parent', 'lsa').get(id=booking_id)
    except BookingRequest.DoesNotExist:
        return None
