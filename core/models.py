from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="facilities")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    country = models.CharField(max_length=2, default="IN")

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class SourceFile(models.Model):
    SOURCE_TYPES = [
        ("sap", "SAP fuel/procurement flat file"),
        ("utility", "Utility portal electricity CSV"),
        ("travel", "Concur-like corporate travel CSV"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="source_files")
    source_type = models.CharField(max_length=24, choices=SOURCE_TYPES)
    filename = models.CharField(max_length=255)
    checksum = models.CharField(max_length=64)
    received_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=24, default="processed")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.source_type}: {self.filename}"


class NormalizedActivity(models.Model):
    STATUS = [
        ("pending", "Pending review"),
        ("failed", "Failed validation"),
        ("approved", "Approved"),
        ("locked", "Locked for audit"),
        ("rejected", "Rejected"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="activities")
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE, related_name="activities")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    source_type = models.CharField(max_length=24)
    source_record_id = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    scope = models.CharField(max_length=16)
    activity_start = models.DateField(null=True, blank=True)
    activity_end = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unit = models.CharField(max_length=24)
    co2e_kg = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    emission_factor = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    currency = models.CharField(max_length=8, blank=True)
    supplier = models.CharField(max_length=160, blank=True)
    raw_payload = models.JSONField(default=dict)
    normalized_payload = models.JSONField(default=dict)
    flags = models.JSONField(default=list)
    status = models.CharField(max_length=24, choices=STATUS, default="pending")
    edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("tenant", "source_file", "source_record_id")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.source_type} {self.source_record_id}"


class AuditEvent(models.Model):
    activity = models.ForeignKey(NormalizedActivity, on_delete=models.CASCADE, related_name="audit_events")
    action = models.CharField(max_length=64)
    actor = models.CharField(max_length=120, default="analyst@demo")
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
