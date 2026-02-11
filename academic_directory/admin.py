# academic_directory/admin.py
"""
Academic Directory — Django Admin

Fixes in this version:
  - verified_by / verified_at populated correctly via save_model override
  - Autocomplete dropdowns for university → faculty → department cascading
  - All badge/colour styles use project palette (#064E3B / #F59E0B / #DC2626)
  - Email notifications wired to background_utils (no Celery)
"""
import logging
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    University,
    Faculty,
    Department,
    ProgramDuration,
    Representative,
    RepresentativeHistory,
    SubmissionNotification,
)
from .utils.notifications import send_bulk_verification_email

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared inline style fragments
# ---------------------------------------------------------------------------
_BADGE = (
    'display:inline-block;padding:3px 10px;border-radius:12px;'
    'font-size:11px;font-weight:700;letter-spacing:.4px;'
    'text-transform:uppercase;color:#fff;'
)


def _badge(bg_colour: str, label: str) -> str:
    return format_html(
        '<span style="{style}background:{bg};">{label}</span>',
        style=_BADGE,
        bg=bg_colour,
        label=label,
    )


# ---------------------------------------------------------------------------
# University
# ---------------------------------------------------------------------------
@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['abbreviation', 'name', 'state', 'type_badge', 'is_active']
    list_filter = ['type', 'state', 'is_active']
    search_fields = ['name', 'abbreviation', 'state']   # required for autocomplete
    ordering = ['name']

    fieldsets = (
        ('Identity', {'fields': ('name', 'abbreviation')}),
        ('Location & Classification', {'fields': ('state', 'type')}),
        ('Status', {'fields': ('is_active',)}),
    )

    def type_badge(self, obj):
        colours = {
            'FEDERAL': '#064E3B',
            'STATE': '#1D4ED8',
            'PRIVATE': '#7C3AED',
        }
        return _badge(colours.get(obj.type, '#6B7280'), obj.get_type_display())
    type_badge.short_description = 'Type'
    type_badge.allow_tags = True


# ---------------------------------------------------------------------------
# Faculty
# ---------------------------------------------------------------------------
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['abbreviation', 'name', 'university', 'is_active']
    list_filter = ['university', 'is_active']
    search_fields = ['name', 'abbreviation', 'university__name']  # required for autocomplete
    ordering = ['university__name', 'name']
    autocomplete_fields = ['university']

    fieldsets = (
        ('Identity', {'fields': ('university', 'name', 'abbreviation')}),
        ('Status', {'fields': ('is_active',)}),
    )


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['abbreviation', 'name', 'faculty', 'university_display', 'is_active']
    list_filter = ['faculty__university', 'faculty', 'is_active']
    search_fields = ['name', 'abbreviation', 'faculty__name', 'faculty__university__name']
    ordering = ['faculty__university__name', 'faculty__name', 'name']
    autocomplete_fields = ['faculty']

    fieldsets = (
        ('Identity', {'fields': ('faculty', 'name', 'abbreviation')}),
        ('Status', {'fields': ('is_active',)}),
    )

    def university_display(self, obj):
        return obj.faculty.university.abbreviation
    university_display.short_description = 'University'


# ---------------------------------------------------------------------------
# ProgramDuration
# ---------------------------------------------------------------------------
@admin.register(ProgramDuration)
class ProgramDurationAdmin(admin.ModelAdmin):
    list_display = ['department', 'duration_years', 'program_type']
    list_filter = ['duration_years', 'program_type']
    search_fields = ['department__name']
    ordering = ['department__name']
    autocomplete_fields = ['department']

    fieldsets = (
        ('Program Information', {'fields': ('department', 'duration_years', 'program_type')}),
        ('Additional Details', {'fields': ('notes',), 'classes': ('collapse',)}),
    )


# ---------------------------------------------------------------------------
# RepresentativeHistory inline
# ---------------------------------------------------------------------------
class RepresentativeHistoryInline(admin.TabularInline):
    model = RepresentativeHistory
    extra = 0
    can_delete = False
    fields = ['role', 'department', 'verification_status', 'snapshot_date']
    readonly_fields = ['role', 'department', 'verification_status', 'snapshot_date']
    ordering = ['-snapshot_date']


# ---------------------------------------------------------------------------
# Representative
# ---------------------------------------------------------------------------
@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'phone_number', 'role_badge',
        'department', 'level_display', 'verification_badge', 'is_active', 'created_at',
    ]
    list_filter = [
        'role', 'verification_status', 'is_active',
        'university', 'faculty', 'submission_source',
    ]
    search_fields = [
        'full_name', 'nickname', 'phone_number', 'email',
        'department__name', 'faculty__name', 'university__name',
    ]
    readonly_fields = [
        'university', 'faculty',
        'current_level_display', 'is_final_year', 'expected_graduation_year',
        'verified_by', 'verified_at',
        'created_at', 'updated_at',
    ]
    ordering = ['-created_at']
    autocomplete_fields = ['department']        # cascades: selecting dept shows university/faculty via readonly
    inlines = [RepresentativeHistoryInline]

    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'nickname', 'phone_number', 'whatsapp_number', 'email'),
        }),
        ('Institutional Information', {
            'fields': ('university', 'faculty', 'department', 'role'),
        }),
        ('Academic Information', {
            'fields': (
                'entry_year', 'tenure_start_year',
                'current_level_display', 'is_final_year', 'expected_graduation_year',
            ),
            'description': 'Entry year for class reps; tenure start year for presidents.',
        }),
        ('Submission Details', {
            'fields': ('submission_source', 'submission_source_other'),
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verified_at'),
            'description': (
                'Change Verification Status and Save — verified_by / verified_at '
                'are set automatically.'
            ),
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['verify_representatives', 'dispute_representatives', 'deactivate_representatives']

    # ------------------------------------------------------------------
    # save_model — auto-populate verified_by / verified_at
    # ------------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        if change:
            original = Representative.objects.get(pk=obj.pk)
            old_status = original.verification_status
            new_status = obj.verification_status

            if old_status != new_status:
                if new_status == 'VERIFIED':
                    from django.utils import timezone
                    obj.verified_by = request.user
                    obj.verified_at = timezone.now()
                elif new_status in ('UNVERIFIED', 'DISPUTED'):
                    # Clear verification metadata when un-verifying or disputing
                    obj.verified_by = None
                    obj.verified_at = None

        super().save_model(request, obj, form, change)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    def role_badge(self, obj):
        colours = {
            'CLASS_REP': '#064E3B',
            'DEPT_PRESIDENT': '#F59E0B',
            'FACULTY_PRESIDENT': '#1D4ED8',
        }
        return _badge(colours.get(obj.role, '#6B7280'), obj.get_role_display())
    role_badge.short_description = 'Role'
    role_badge.allow_tags = True

    def verification_badge(self, obj):
        colours = {
            'UNVERIFIED': '#F59E0B',
            'VERIFIED': '#064E3B',
            'DISPUTED': '#DC2626',
        }
        return _badge(colours.get(obj.verification_status, '#6B7280'), obj.get_verification_status_display())
    verification_badge.short_description = 'Status'
    verification_badge.allow_tags = True

    def level_display(self, obj):
        if obj.role == 'CLASS_REP':
            return obj.current_level_display or '—'
        return 'N/A'
    level_display.short_description = 'Level'

    # ------------------------------------------------------------------
    # Bulk actions
    # ------------------------------------------------------------------
    def verify_representatives(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            verification_status='VERIFIED',
            verified_by=request.user,
            verified_at=timezone.now(),
        )
        try:
            send_bulk_verification_email(list(queryset), request.user)
        except Exception as exc:
            logger.error(f"admin verify_representatives: email error: {exc}")
        self.message_user(request, f"Successfully verified {queryset.count()} representative(s).")
    verify_representatives.short_description = "✅ Verify selected representatives"

    def dispute_representatives(self, request, queryset):
        queryset.update(
            verification_status='DISPUTED',
            verified_by=None,
            verified_at=None,
        )
        self.message_user(request, f"Marked {queryset.count()} representative(s) as disputed.")
    dispute_representatives.short_description = "⚠️ Dispute selected representatives"

    def deactivate_representatives(self, request, queryset):
        from django.utils import timezone
        for rep in queryset:
            rep.deactivate(reason="Bulk deactivation by admin")
        self.message_user(request, f"Deactivated {queryset.count()} representative(s).")
    deactivate_representatives.short_description = "🚫 Deactivate selected representatives"


# ---------------------------------------------------------------------------
# RepresentativeHistory
# ---------------------------------------------------------------------------
@admin.register(RepresentativeHistory)
class RepresentativeHistoryAdmin(admin.ModelAdmin):
    list_display = ['representative', 'role', 'department', 'verification_status', 'snapshot_date']
    list_filter = ['role', 'verification_status']
    search_fields = ['representative__full_name', 'phone_number']
    readonly_fields = [
        'representative', 'full_name', 'phone_number', 'role',
        'entry_year', 'tenure_start_year', 'verification_status',
        'is_active', 'snapshot_date', 'department', 'faculty', 'university',
    ]
    ordering = ['-snapshot_date']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# SubmissionNotification
# ---------------------------------------------------------------------------
@admin.register(SubmissionNotification)
class SubmissionNotificationAdmin(admin.ModelAdmin):
    list_display = ['representative', 'is_read', 'is_emailed', 'created_at', 'read_at']
    list_filter = ['is_read', 'is_emailed']
    search_fields = ['representative__full_name', 'representative__phone_number']
    readonly_fields = ['representative', 'is_emailed', 'emailed_at', 'created_at', 'read_at', 'read_by']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False