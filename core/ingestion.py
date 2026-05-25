import csv
import hashlib
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path

from django.db import transaction

from .models import AuditEvent, Facility, NormalizedActivity, SourceFile, Tenant


PLANT_LOOKUP = {
    "BLR01": ("Bengaluru Assembly Plant", "IN"),
    "PUN02": ("Pune Components Plant", "IN"),
    "HAM01": ("Hamburg Sales Office", "DE"),
}

EMISSION_FACTORS = {
    "diesel_l": Decimal("2.680"),
    "petrol_l": Decimal("2.310"),
    "electricity_kwh_in": Decimal("0.716"),
    "electricity_kwh_de": Decimal("0.381"),
    "flight_km": Decimal("0.158"),
    "hotel_night": Decimal("24.000"),
    "taxi_km": Decimal("0.192"),
    "rail_km": Decimal("0.041"),
    "procurement_usd": Decimal("0.290"),
}


def demo_tenant():
    tenant, _ = Tenant.objects.get_or_create(slug="acme-industrials", defaults={"name": "ACME Industrials"})
    for code, (name, country) in PLANT_LOOKUP.items():
        Facility.objects.get_or_create(tenant=tenant, code=code, defaults={"name": name, "country": country})
    return tenant


def parse_date(value):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def dec(value):
    if value is None or str(value).strip() == "":
        return None
    cleaned = str(value).strip().replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def checksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rows_from_text(text):
    return list(csv.DictReader(StringIO(text)))


def ingest_text(source_type, filename, text, tenant=None):
    tenant = tenant or demo_tenant()
    parser = {"sap": parse_sap, "utility": parse_utility, "travel": parse_travel}[source_type]

    with transaction.atomic():
        source = SourceFile.objects.create(
            tenant=tenant,
            source_type=source_type,
            filename=filename,
            checksum=checksum(text),
        )
        created = []
        for index, row in enumerate(rows_from_text(text), start=1):
            activity = parser(row, index, source, tenant)
            activity.status = "failed" if any(flag.startswith("error:") for flag in activity.flags) else "pending"
            activity.save()
            AuditEvent.objects.create(
                activity=activity,
                action="ingested",
                after={"status": activity.status, "flags": activity.flags},
                note=f"Imported from {filename}",
            )
            created.append(activity)
        source.status = "processed_with_errors" if any(a.status == "failed" for a in created) else "processed"
        source.save(update_fields=["status"])
        return source, created


def parse_sap(row, index, source, tenant):
    # Handles a realistic ugly SAP flat-file export with mixed English/German headers.
    record_id = row.get("BELNR") or row.get("DocumentNo") or f"sap-{index}"
    plant_code = row.get("WERKS") or row.get("Plant")
    material = (row.get("MATNR") or row.get("Material") or "").lower()
    movement = row.get("BWART") or row.get("MovementType") or ""
    unit_raw = (row.get("MEINS") or row.get("Unit") or "").upper()
    qty = dec(row.get("MENGE") or row.get("Quantity"))
    amount = dec(row.get("WRBTR") or row.get("Amount"))
    date = parse_date(row.get("BUDAT") or row.get("PostingDate"))
    flags = []

    facility = Facility.objects.filter(tenant=tenant, code=plant_code).first()
    if not facility:
        flags.append(f"error: unknown SAP plant code {plant_code}")
    if not date:
        flags.append("error: unreadable SAP posting date")

    if "diesel" in material:
        category, scope, factor_key = "stationary fuel - diesel", "scope_1", "diesel_l"
    elif "petrol" in material or "gasoline" in material:
        category, scope, factor_key = "stationary fuel - petrol", "scope_1", "petrol_l"
    else:
        category, scope, factor_key = "purchased goods and services", "scope_3", "procurement_usd"

    normalized_qty = qty
    normalized_unit = "L"
    if category.startswith("purchased"):
        normalized_qty = amount
        normalized_unit = "USD"
    elif unit_raw in {"GAL", "GALLON"} and qty is not None:
        normalized_qty = qty * Decimal("3.78541")
        flags.append("converted US gallons to litres")
    elif unit_raw not in {"L", "LTR", "LITER", "LITRE"}:
        flags.append(f"warning: unexpected SAP fuel unit {unit_raw}")

    if movement not in {"101", "261", "201"}:
        flags.append(f"warning: SAP movement type {movement} may not represent consumption")
    if normalized_qty is None:
        flags.append("error: missing quantity or amount")
    if normalized_qty and normalized_qty > Decimal("50000"):
        flags.append("review: unusually high activity quantity")

    factor = EMISSION_FACTORS[factor_key]
    co2e = normalized_qty * factor if normalized_qty is not None else None
    return NormalizedActivity(
        tenant=tenant,
        source_file=source,
        facility=facility,
        source_type="sap",
        source_record_id=record_id,
        category=category,
        scope=scope,
        activity_start=date,
        activity_end=date,
        quantity=normalized_qty,
        unit=normalized_unit,
        co2e_kg=co2e,
        emission_factor=factor,
        currency=row.get("WAERS") or row.get("Currency") or "",
        supplier=row.get("LIFNR") or row.get("Vendor") or "",
        raw_payload=row,
        normalized_payload={"plant_code": plant_code, "movement_type": movement, "material": material},
        flags=flags,
    )


def parse_utility(row, index, source, tenant):
    record_id = row.get("bill_id") or row.get("invoice_number") or f"utility-{index}"
    meter = row.get("meter_number") or row.get("meter")
    plant_code = row.get("facility_code")
    start = parse_date(row.get("period_start"))
    end = parse_date(row.get("period_end"))
    kwh = dec(row.get("usage_kwh"))
    demand_kw = dec(row.get("peak_demand_kw"))
    country = (row.get("country") or "IN").upper()
    facility = Facility.objects.filter(tenant=tenant, code=plant_code).first()
    flags = []

    if not facility:
        flags.append(f"error: unknown facility code {plant_code}")
    if not start or not end:
        flags.append("error: utility billing period missing or unreadable")
    elif start.day != 1 or end.day not in {28, 29, 30, 31}:
        flags.append("review: billing period does not align cleanly to calendar month")
    if kwh is None:
        flags.append("error: usage_kwh missing")
    if demand_kw and kwh and demand_kw > Decimal("0") and kwh / demand_kw < Decimal("20"):
        flags.append("review: low load factor for reported peak demand")

    factor = EMISSION_FACTORS["electricity_kwh_de" if country == "DE" else "electricity_kwh_in"]
    return NormalizedActivity(
        tenant=tenant,
        source_file=source,
        facility=facility,
        source_type="utility",
        source_record_id=record_id,
        category="purchased electricity",
        scope="scope_2",
        activity_start=start,
        activity_end=end,
        quantity=kwh,
        unit="kWh",
        co2e_kg=kwh * factor if kwh is not None else None,
        emission_factor=factor,
        supplier=row.get("utility_name") or "",
        raw_payload=row,
        normalized_payload={"meter_number": meter, "tariff": row.get("tariff_code"), "peak_demand_kw": str(demand_kw or "")},
        flags=flags,
    )


def parse_travel(row, index, source, tenant):
    record_id = row.get("expense_id") or row.get("booking_id") or f"travel-{index}"
    category_raw = (row.get("expense_type") or row.get("category") or "").lower()
    start = parse_date(row.get("trip_start") or row.get("date"))
    end = parse_date(row.get("trip_end") or row.get("date"))
    distance = dec(row.get("distance_km"))
    nights = dec(row.get("nights"))
    flags = []

    if "flight" in category_raw:
        category, unit, qty, factor_key = "business travel - air", "km", distance, "flight_km"
        if qty is None and row.get("origin_airport") and row.get("destination_airport"):
            flags.append("review: distance missing; airport pair available for future distance lookup")
    elif "hotel" in category_raw:
        category, unit, qty, factor_key = "business travel - hotel", "night", nights, "hotel_night"
    elif "taxi" in category_raw or "ground" in category_raw or "rideshare" in category_raw:
        category, unit, qty, factor_key = "business travel - taxi", "km", distance, "taxi_km"
    elif "rail" in category_raw or "train" in category_raw:
        category, unit, qty, factor_key = "business travel - rail", "km", distance, "rail_km"
    else:
        category, unit, qty, factor_key = "business travel - other", "km", distance, "taxi_km"
        flags.append("review: unmapped travel expense type")

    if not start:
        flags.append("error: missing travel date")
    if qty is None:
        flags.append("error: missing distance or nights")
    if qty and category.endswith("air") and qty > Decimal("16000"):
        flags.append("review: unusually long flight distance")

    factor = EMISSION_FACTORS[factor_key]
    return NormalizedActivity(
        tenant=tenant,
        source_file=source,
        source_type="travel",
        source_record_id=record_id,
        category=category,
        scope="scope_3",
        activity_start=start,
        activity_end=end,
        quantity=qty,
        unit=unit,
        co2e_kg=qty * factor if qty is not None else None,
        emission_factor=factor,
        currency=row.get("currency") or "",
        supplier=row.get("vendor") or row.get("airline") or "",
        raw_payload=row,
        normalized_payload={
            "origin_airport": row.get("origin_airport"),
            "destination_airport": row.get("destination_airport"),
            "employee_region": row.get("employee_region"),
        },
        flags=flags,
    )


def ingest_sample_files():
    tenant = demo_tenant()
    SourceFile.objects.filter(tenant=tenant).delete()
    sample_dir = Path(__file__).resolve().parent.parent / "sample_data"
    results = []
    for source_type, filename in [
        ("sap", "sap_flat_file.csv"),
        ("utility", "utility_portal_export.csv"),
        ("travel", "concur_travel_export.csv"),
    ]:
        text = (sample_dir / filename).read_text(encoding="utf-8")
        source, created = ingest_text(source_type, filename, text, tenant)
        results.append({"source_type": source_type, "filename": filename, "rows": len(created), "status": source.status})
    return results


