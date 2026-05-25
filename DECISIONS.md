# Decisions

## SAP source

I chose a SAP MM flat-file/CSV export rather than OData or BAPI. For a four-day prototype this is the most realistic first ingestion path because enterprise onboarding often starts with scheduled SAP exports shared by finance or operations, not direct API access. The sample uses SAP-like columns: `BELNR`, `WERKS`, `BUDAT`, `MATNR`, `MENGE`, `MEINS`, `BWART`, `WRBTR`, `WAERS`, and `LIFNR`.

Handled subset: fuel consumption and procurement spend. The parser supports mixed date formats, litres/gallons, movement type warnings, vendor tracking, and plant-code lookup.

Ignored subset: IDoc hierarchy, SAP authorization, material master joins, tax treatment, currency conversion, and PO/invoice reconciliation.

PM questions: Which SAP module/export is available first? Are plant codes stable? Do we receive material descriptions or only material IDs? Who owns the plant lookup table?

## Utility source

I chose portal CSV export for electricity. Facilities teams often download bills or usage CSVs from utility portals; PDF extraction is valuable but noisier and less suitable for the first review prototype.

Handled subset: meter number, billing period, kWh, peak demand, tariff code, country, cost, and currency. The parser flags non-calendar billing periods and unknown facilities.

Ignored subset: PDF bill extraction, time-of-use intervals, renewable certificates, taxes, and demand-charge calculations.

PM questions: Do analysts need location-based, market-based, or both Scope 2 methods? How often are utility exports pulled? Is meter-to-facility mapping already available?

## Travel source

I chose a Concur-like expense CSV because travel APIs are usually gated by enterprise credentials. The sample follows categories commonly seen in expense platforms: flight, hotel, taxi, and rail-like rows.

Handled subset: expense ID, dates, expense category, airport pair, distance, nights, vendor, amount, and currency. The parser flags missing distance when airport codes exist.

Ignored subset: live Concur OAuth/API sync, airport distance lookup, cabin class, radiative forcing multipliers, and employee PII.

PM questions: Which travel platform does the client use? Are distances available? Should we use booking data or reimbursed expenses as source of truth?
