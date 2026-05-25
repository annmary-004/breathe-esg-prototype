# Breathe ESG Ingestion Prototype

Django REST + React prototype for ingesting three enterprise ESG source shapes, normalizing activity data, and giving analysts a review queue before rows are locked for audit.

## Local run

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000`, click **Load sample data**, then review/approve rows.

## Demo credentials

No login is required for the prototype dashboard. The admin can be enabled with:

```powershell
python manage.py createsuperuser
```

## Deployment

The included `render.yaml` deploys this as a single Render web service. Set `SECRET_KEY` and `DEBUG=0` in Render. SQLite is used for prototype simplicity; for production, switch `DATABASES` to Postgres.

## API surface

- `POST /api/ingest/sample/` loads the included sample files.
- `POST /api/ingest/sap/`, `/utility/`, `/travel/` accept multipart CSV upload field `file`.
- `GET /api/activities/?status=pending&source=sap` lists normalized activities.
- `POST /api/activities/<id>/approve/` locks an activity for audit.
- `POST /api/activities/<id>/reject/` rejects an activity.
- `GET /api/audit/` returns recent audit events.
