from django.contrib import admin
from .models import AuditEvent, Facility, NormalizedActivity, SourceFile, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("tenant", "code", "name", "country")


@admin.register(SourceFile)
class SourceFileAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source_type", "filename", "status", "received_at")


@admin.register(NormalizedActivity)
class NormalizedActivityAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source_type", "category", "scope", "quantity", "unit", "status")
    list_filter = ("tenant", "source_type", "scope", "status")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("activity", "action", "actor", "created_at")
