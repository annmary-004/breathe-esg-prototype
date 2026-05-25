import json
from decimal import Decimal

from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .ingestion import demo_tenant, ingest_sample_files, ingest_text
from .models import AuditEvent, NormalizedActivity


def index(request):
    return render(request, "index.html")


def encode(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def activity_json(activity):
    return {
        "id": activity.id,
        "source_type": activity.source_type,
        "source_record_id": activity.source_record_id,
        "facility": activity.facility.name if activity.facility else "Unmapped",
        "category": activity.category,
        "scope": activity.scope,
        "activity_start": activity.activity_start.isoformat() if activity.activity_start else None,
        "activity_end": activity.activity_end.isoformat() if activity.activity_end else None,
        "quantity": encode(activity.quantity),
        "unit": activity.unit,
        "co2e_kg": encode(activity.co2e_kg),
        "emission_factor": encode(activity.emission_factor),
        "supplier": activity.supplier,
        "status": activity.status,
        "flags": activity.flags,
        "raw_payload": activity.raw_payload,
        "normalized_payload": activity.normalized_payload,
        "approved_at": activity.approved_at.isoformat() if activity.approved_at else None,
        "approved_by": activity.approved_by,
    }


def bootstrap(request):
    tenant = demo_tenant()
    return JsonResponse({"tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}})


def summary(request):
    tenant = demo_tenant()
    rows = NormalizedActivity.objects.filter(tenant=tenant)
    by_status = dict(rows.values_list("status").annotate(c=Count("id")))
    by_scope = {r["scope"]: float(r["co2e"] or 0) for r in rows.values("scope").annotate(co2e=Sum("co2e_kg"))}
    return JsonResponse({
        "total_rows": rows.count(),
        "failed_rows": by_status.get("failed", 0),
        "pending_rows": by_status.get("pending", 0),
        "approved_rows": by_status.get("approved", 0) + by_status.get("locked", 0),
        "by_status": by_status,
        "by_scope": by_scope,
    })


def activities(request):
    tenant = demo_tenant()
    qs = NormalizedActivity.objects.filter(tenant=tenant).select_related("facility", "source_file")
    status = request.GET.get("status")
    source_type = request.GET.get("source")
    if status and status != "all":
        qs = qs.filter(status=status)
    if source_type and source_type != "all":
        qs = qs.filter(source_type=source_type)
    return JsonResponse({"results": [activity_json(a) for a in qs[:200]]})


@csrf_exempt
@require_POST
def ingest_sample(request):
    return JsonResponse({"ingested": ingest_sample_files()})


@csrf_exempt
@require_POST
def ingest_upload(request, source_type):
    if source_type not in {"sap", "utility", "travel"}:
        return JsonResponse({"error": "source_type must be sap, utility, or travel"}, status=400)
    file_obj = request.FILES.get("file")
    if not file_obj:
        return JsonResponse({"error": "multipart file field named 'file' is required"}, status=400)
    text = file_obj.read().decode("utf-8-sig")
    source, created = ingest_text(source_type, file_obj.name, text, demo_tenant())
    return JsonResponse({"source_file_id": source.id, "rows": len(created), "status": source.status})


@csrf_exempt
@require_http_methods(["POST"])
def approve_activity(request, pk):
    activity = get_object_or_404(NormalizedActivity, pk=pk)
    if activity.status == "failed":
        return JsonResponse({"error": "failed rows must be fixed or rejected before approval"}, status=409)
    before = activity_json(activity)
    body = json.loads(request.body or "{}")
    activity.status = "locked" if body.get("lock", True) else "approved"
    activity.approved_by = body.get("actor", "analyst@demo")
    activity.approved_at = timezone.now()
    activity.save(update_fields=["status", "approved_by", "approved_at"])
    AuditEvent.objects.create(activity=activity, action=activity.status, actor=activity.approved_by, before=before, after=activity_json(activity))
    return JsonResponse(activity_json(activity))


@csrf_exempt
@require_http_methods(["POST"])
def reject_activity(request, pk):
    activity = get_object_or_404(NormalizedActivity, pk=pk)
    before = activity_json(activity)
    body = json.loads(request.body or "{}")
    activity.status = "rejected"
    activity.save(update_fields=["status"])
    AuditEvent.objects.create(
        activity=activity,
        action="rejected",
        actor=body.get("actor", "analyst@demo"),
        before=before,
        after=activity_json(activity),
        note=body.get("note", ""),
    )
    return JsonResponse(activity_json(activity))


def audit_events(request):
    tenant = demo_tenant()
    events = AuditEvent.objects.filter(activity__tenant=tenant).select_related("activity")[:100]
    return JsonResponse({"results": [
        {
            "id": event.id,
            "activity_id": event.activity_id,
            "record": event.activity.source_record_id,
            "action": event.action,
            "actor": event.actor,
            "note": event.note,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]})

