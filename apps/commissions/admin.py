from django.contrib import admin
from .models import CommissionSheet, CommissionEntry


class CommissionEntryInline(admin.TabularInline):
    model = CommissionEntry
    extra = 0


@admin.register(CommissionSheet)
class CommissionSheetAdmin(admin.ModelAdmin):
    list_display = ('subject', 'date', 'status', 'chairman')
    list_filter = ('status', 'subject', 'date')
    inlines = [CommissionEntryInline]


@admin.register(CommissionEntry)
class CommissionEntryAdmin(admin.ModelAdmin):
    list_display = ('student', 'sheet', 'grade')
    list_filter = ('grade', 'sheet__subject')
    search_fields = ('student__last_name', 'student__first_name')
