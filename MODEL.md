# Data Model

The core model is `NormalizedActivity`: one reviewed emissions/activity row, tied to exactly one `Tenant` and one `SourceFile`.

## Entities

- `Tenant`: multi-tenant boundary. Every source file, facility, and activity belongs to a tenant.
- `Facility`: tenant-specific plant/site lookup. SAP and utility source rows often carry only a plant or meter code, so mapping is explicit.
- `SourceFile`: source-of-truth envelope. It stores source type, original filename, checksum, received timestamp, and processing status.
- `NormalizedActivity`: canonical activity row used by analysts and auditors.
- `AuditEvent`: immutable-ish history of ingestion, approval, rejection, and future edits.

## Why this shape

Analysts need to know both the normalized answer and where it came from. `NormalizedActivity.raw_payload` keeps the exact source row, while `normalized_payload` stores parser decisions such as plant code, movement type, meter number, airport pair, or tariff. That makes review defensible without needing to reopen the original file for every question.

Scope classification is row-level:

- Scope 1: SAP stationary/mobile fuel consumption.
- Scope 2: purchased electricity from utility exports.
- Scope 3: procurement spend and business travel.

Unit normalization is stored on the normalized row: `quantity`, `unit`, `emission_factor`, and `co2e_kg`. For example, SAP gallons become litres, utility electricity becomes kWh, and travel remains km or hotel nights.

## Audit and locking

Rows start as `pending` or `failed`. Pending rows can be approved and moved to `locked`; failed rows must be corrected or rejected. `AuditEvent` captures `before`, `after`, actor, note, and timestamp so the review action is traceable.

## Multi-tenancy

This prototype uses one demo tenant but the schema is tenant-scoped throughout. In a production API, tenant would be resolved from authenticated user membership or a tenant header, and all queries would be filtered through that context.
