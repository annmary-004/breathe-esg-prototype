# Tradeoffs

1. No authentication or role model.

   The schema is tenant-ready, but the prototype uses a demo tenant and analyst identity. I skipped auth so the review workflow, data model, and ingestion logic could stay visible and easy to test.

2. No row-edit correction UI.

   Failed rows are shown and can be rejected, but not corrected inline. I would add a controlled edit form with field-level audit events next, especially for plant mapping and missing travel distance.

3. No production emissions factor service.

   The prototype uses fixed factors in code to demonstrate normalization and review. A real deployment needs versioned factor sets, region/year selection, source citations, and approval of factor changes.
