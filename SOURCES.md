# Sources Researched

## SAP fuel and procurement

Format chosen: SAP MM flat-file export using common SAP-style fields. Real SAP data may arrive through IDoc, OData, BAPI, or manually scheduled CSV exports. I chose flat file because it is a common onboarding compromise when API access is not ready.

What I learned and reflected in sample data:

- SAP exports commonly expose terse technical fields such as `BELNR`, `WERKS`, `BUDAT`, `MATNR`, `MENGE`, `MEINS`, and `BWART`.
- Plant codes require lookup tables before an analyst can understand the site.
- Dates and units vary across configurations.
- Movement types matter; not every material movement equals consumption.

What would break in a real deployment: material IDs without descriptions, non-English/custom fields, duplicate correction documents, partial reversals, currency conversion, and missing master data.

## Utility electricity

Format chosen: utility portal CSV export. This is a practical first source because facilities teams often export bill/usage data manually even when no formal API exists.

What I learned and reflected in sample data:

- Utility records usually include meter number, billing period, kWh, tariff/rate code, demand, charges, and account or bill identifiers.
- Billing periods do not always align with calendar months.
- Meter-to-facility mapping is essential and often separate from the bill.

What would break in a real deployment: PDF-only bills, interval data, multiple meters per facility, net metering, estimated reads, tariff changes, taxes, and market-based Scope 2 instruments.

## Corporate travel

Format chosen: Concur/Navan-like expense export CSV. Enterprise travel platforms can expose APIs, but CSV export is realistic for a prototype without client credentials.

What I learned and reflected in sample data:

- Travel activity arrives as mixed expense categories: flights, hotels, taxis, rail, and other spend.
- Flights may provide airport codes but not distance.
- Hotels use nights rather than distance.
- Different categories need different emission factors.

What would break in a real deployment: missing airport distance lookup, cabin class, multi-leg trips, cancellations/refunds, personal travel mixed with business travel, and duplicated booking/expense feeds.
