from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("api/bootstrap/", views.bootstrap, name="bootstrap"),
    path("api/summary/", views.summary, name="summary"),
    path("api/activities/", views.activities, name="activities"),
    path("api/activities/<int:pk>/approve/", views.approve_activity, name="approve_activity"),
    path("api/activities/<int:pk>/reject/", views.reject_activity, name="reject_activity"),
    path("api/ingest/sample/", views.ingest_sample, name="ingest_sample"),
    path("api/ingest/<str:source_type>/", views.ingest_upload, name="ingest_upload"),
    path("api/audit/", views.audit_events, name="audit_events"),
]
