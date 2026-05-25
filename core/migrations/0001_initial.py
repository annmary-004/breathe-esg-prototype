# Generated for the Breathe ESG intern prototype.
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Facility",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=160)),
                ("country", models.CharField(default="IN", max_length=2)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="facilities", to="core.tenant")),
            ],
            options={"unique_together": {("tenant", "code")}},
        ),
        migrations.CreateModel(
            name="SourceFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("sap", "SAP fuel/procurement flat file"), ("utility", "Utility portal electricity CSV"), ("travel", "Concur-like corporate travel CSV")], max_length=24)),
                ("filename", models.CharField(max_length=255)),
                ("checksum", models.CharField(max_length=64)),
                ("received_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("status", models.CharField(default="processed", max_length=24)),
                ("notes", models.TextField(blank=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_files", to="core.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="NormalizedActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(max_length=24)),
                ("source_record_id", models.CharField(max_length=120)),
                ("category", models.CharField(max_length=80)),
                ("scope", models.CharField(max_length=16)),
                ("activity_start", models.DateField(blank=True, null=True)),
                ("activity_end", models.DateField(blank=True, null=True)),
                ("quantity", models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True)),
                ("unit", models.CharField(max_length=24)),
                ("co2e_kg", models.DecimalField(blank=True, decimal_places=3, max_digits=14, null=True)),
                ("emission_factor", models.DecimalField(blank=True, decimal_places=6, max_digits=12, null=True)),
                ("currency", models.CharField(blank=True, max_length=8)),
                ("supplier", models.CharField(blank=True, max_length=160)),
                ("raw_payload", models.JSONField(default=dict)),
                ("normalized_payload", models.JSONField(default=dict)),
                ("flags", models.JSONField(default=list)),
                ("status", models.CharField(choices=[("pending", "Pending review"), ("failed", "Failed validation"), ("approved", "Approved"), ("locked", "Locked for audit"), ("rejected", "Rejected")], default="pending", max_length=24)),
                ("edited", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.CharField(blank=True, max_length=120)),
                ("facility", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.facility")),
                ("source_file", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="core.sourcefile")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="core.tenant")),
            ],
            options={"ordering": ("-created_at",), "unique_together": {("tenant", "source_file", "source_record_id")}},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=64)),
                ("actor", models.CharField(default="analyst@demo", max_length=120)),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(blank=True, default=dict)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("activity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="core.normalizedactivity")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
