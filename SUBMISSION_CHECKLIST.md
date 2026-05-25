# Submission Checklist

Use this when sending the assignment back.

## Required links

- GitHub repository URL: add after pushing this folder to GitHub.
- Deployed app URL: add after deploying with `render.yaml`.
- Credentials: no login required for the demo app.

## What this project contains

- Working Django app with JSON REST endpoints.
- React analyst review dashboard.
- Ingestion for three source types:
  - SAP fuel/procurement flat-file CSV.
  - Utility portal electricity CSV.
  - Concur/Navan-like travel CSV.
- Sample realistic data in `sample_data/`.
- Multi-tenant data model.
- Scope 1/2/3 categorization.
- Source-of-truth tracking through `SourceFile` and raw payload storage.
- Unit normalization.
- Audit events for ingestion, approval, locking, and rejection.
- Required documents:
  - `MODEL.md`
  - `DECISIONS.md`
  - `TRADEOFFS.md`
  - `SOURCES.md`

## Render deploy steps

1. Push this folder to GitHub.
2. Open Render and create a new Blueprint or Web Service from the repository.
3. Render will read `render.yaml`.
4. After deploy, open the live URL and click **Load sample data**.
5. Send the GitHub URL and live URL by email.

## Repository access

Share the GitHub repository with:

- saurav@breatheesg.com
- rahul@breatheesg.com
- shivang@breatheesg.com
