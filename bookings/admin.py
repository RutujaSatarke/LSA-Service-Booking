from django.contrib import admin
from bookings.models import Parent, Skill, LSAProfile, BookingRequest, Payment


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'phone', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LSAProfile)
class LSAProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'phone', 'hourly_rate', 'is_active', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('is_active', 'skills')
    filter_horizontal = ('skills',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'lsa', 'session_date', 'start_time', 'end_time', 'status', 'created_at')
    search_fields = ('parent__full_name', 'parent__email', 'lsa__full_name', 'lsa__email')
    list_filter = ('status', 'session_date')
    ordering = ('-session_date', 'start_time')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'transaction_id', 'amount', 'currency', 'status', 'provider', 'created_at')
    search_fields = ('transaction_id', 'booking__id', 'booking__parent__full_name', 'booking__lsa__full_name')
    list_filter = ('status', 'provider', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

