"""Django Admin Configuration"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    University, Faculty, Department, ProgramDuration,
    Representative, RepresentativeHistory, SubmissionNotification
)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """Admin interface for University model."""
    
    list_display = ['abbreviation', 'name', 'state', 'type', 'faculties_count', 'is_active']
    list_filter = ['state', 'type', 'is_active']
    search_fields = ['name', 'abbreviation']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'abbreviation', 'state', 'type')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    """Admin interface for Faculty model."""
    
    list_display = ['name', 'abbreviation', 'university', 'departments_count', 'is_active']
    list_filter = ['university', 'is_active']
    search_fields = ['name', 'abbreviation', 'university__name']
    ordering = ['university__name', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('university', 'name', 'abbreviation')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin interface for Department model."""
    
    list_display = ['name', 'abbreviation', 'faculty', 'university_name', 'representatives_count', 'is_active']
    list_filter = ['faculty__university', 'faculty', 'is_active']
    search_fields = ['name', 'abbreviation', 'faculty__name']
    ordering = ['faculty__university__name', 'faculty__name', 'name']
    
    def university_name(self, obj):
        return obj.faculty.university.name
    university_name.short_description = 'University'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('faculty', 'name', 'abbreviation')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ProgramDuration)
class ProgramDurationAdmin(admin.ModelAdmin):
    """Admin interface for Program Duration model."""
    
    list_display = ['department', 'duration_years', 'program_type']
    list_filter = ['duration_years', 'program_type']
    search_fields = ['department__name']
    ordering = ['department__name']
    
    fieldsets = (
        ('Program Information', {
            'fields': ('department', 'duration_years', 'program_type')
        }),
        ('Additional Details', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


class RepresentativeHistoryInline(admin.TabularInline):
    """Inline admin for representative history."""
    
    model = RepresentativeHistory
    extra = 0
    can_delete = False
    fields = ['role', 'department', 'verification_status', 'snapshot_date']
    readonly_fields = ['role', 'department', 'verification_status', 'snapshot_date']
    ordering = ['-snapshot_date']


@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    """Admin interface for Representative model."""
    
    list_display = [
        'display_name', 'phone_number', 'role_badge', 'department',
        'level_display', 'verification_badge', 'is_active', 'created_at'
    ]
    list_filter = [
        'role', 'verification_status', 'is_active',
        'university', 'faculty', 'submission_source'
    ]
    search_fields = [
        'full_name', 'nickname', 'phone_number', 'email',
        'department__name', 'faculty__name', 'university__name'
    ]
    readonly_fields = [
        'university', 'faculty', 'current_level_display',
        'is_final_year', 'expected_graduation_year',
        'verified_by', 'verified_at', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    inlines = [RepresentativeHistoryInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'nickname', 'phone_number', 'whatsapp_number', 'email')
        }),
        ('Institutional Information', {
            'fields': ('university', 'faculty', 'department', 'role')
        }),
        ('Academic Information', {
            'fields': (
                'entry_year', 'tenure_start_year',
                'current_level_display', 'is_final_year', 'expected_graduation_year'
            ),
            'description': 'Entry year for class reps, tenure start for presidents'
        }),
        ('Submission Details', {
            'fields': ('submission_source', 'submission_source_other')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verified_at')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_representatives', 'dispute_representatives', 'deactivate_representatives']
    
    def role_badge(self, obj):
        """Display role as colored badge."""
        colors = {
            'CLASS_REP': 'primary',
            'DEPT_PRESIDENT': 'success',
            'FACULTY_PRESIDENT': 'warning'
        }
        color = colors.get(obj.role, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def verification_badge(self, obj):
        """Display verification status as colored badge."""
        colors = {
            'UNVERIFIED': 'warning',
            'VERIFIED': 'success',
            'DISPUTED': 'danger'
        }
        color = colors.get(obj.verification_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_verification_status_display()
        )
    verification_badge.short_description = 'Status'
    
    def level_display(self, obj):
        """Display current level for class reps."""
        if obj.role == 'CLASS_REP':
            return obj.current_level_display or '-'
        return 'N/A'
    level_display.short_description = 'Level'
    
    def verify_representatives(self, request, queryset):
        """Bulk verify action."""
        for rep in queryset:
            rep.verify(request.user)
        self.message_user(request, f"Successfully verified {queryset.count()} representatives")
    verify_representatives.short_description = "Verify selected representatives"
    
    def dispute_representatives(self, request, queryset):
        """Bulk dispute action."""
        for rep in queryset:
            rep.dispute()
        self.message_user(request, f"Marked {queryset.count()} representatives as disputed")
    dispute_representatives.short_description = "Dispute selected representatives"
    
    def deactivate_representatives(self, request, queryset):
        """Bulk deactivate action."""
        for rep in queryset:
            rep.deactivate(reason="Bulk deactivation by admin")
        self.message_user(request, f"Deactivated {queryset.count()} representatives")
    deactivate_representatives.short_description = "Deactivate selected representatives"


@admin.register(RepresentativeHistory)
class RepresentativeHistoryAdmin(admin.ModelAdmin):
    """Admin interface for Representative History."""
    
    list_display = ['representative', 'role', 'department', 'verification_status', 'snapshot_date']
    list_filter = ['role', 'verification_status', 'is_active']
    search_fields = ['full_name', 'phone_number']
    ordering = ['-snapshot_date']
    readonly_fields = [
        'representative', 'full_name', 'phone_number', 'department',
        'faculty', 'university', 'role', 'entry_year', 'tenure_start_year',
        'verification_status', 'is_active', 'snapshot_date'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SubmissionNotification)
class SubmissionNotificationAdmin(admin.ModelAdmin):
    """Admin interface for Submission Notifications."""
    
    list_display = [
        'representative', 'status_badge', 'email_badge',
        'read_by', 'created_at'
    ]
    list_filter = ['is_read', 'is_emailed', 'created_at']
    search_fields = ['representative__full_name', 'representative__phone_number']
    ordering = ['-created_at']
    readonly_fields = ['representative', 'emailed_at', 'read_by', 'read_at', 'created_at']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def status_badge(self, obj):
        """Display read status as badge."""
        if obj.is_read:
            return format_html('<span class="badge bg-success">Read</span>')
        return format_html('<span class="badge bg-warning">Unread</span>')
    status_badge.short_description = 'Status'
    
    def email_badge(self, obj):
        """Display email status as badge."""
        if obj.is_emailed:
            return format_html('<span class="badge bg-success">Sent</span>')
        return format_html('<span class="badge bg-secondary">Pending</span>')
    email_badge.short_description = 'Email'
    
    def mark_as_read(self, request, queryset):
        """Mark notifications as read."""
        count = 0
        for notification in queryset:
            notification.mark_as_read(request.user)
            count += 1
        self.message_user(request, f"Marked {count} notifications as read")
    mark_as_read.short_description = "Mark as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark notifications as unread."""
        queryset.update(is_read=False, read_by=None, read_at=None)
        self.message_user(request, f"Marked {queryset.count()} notifications as unread")
    mark_as_unread.short_description = "Mark as unread"