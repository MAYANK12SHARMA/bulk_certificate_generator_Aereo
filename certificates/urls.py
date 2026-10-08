from django.urls import path
from .views import (
    CertificateDetailView,
    CertificateDownloadView,
    GenerationJobCertificatesView,
    GenerationJobCreateView,
    GenerationJobDetailView,
    GetAllGenerationJobsView,
)

urlpatterns = [
    path("jobs/", GenerationJobCreateView.as_view(), name="job-create"),
    path("jobs-details/", GetAllGenerationJobsView.as_view(), name="job-list"),
    path("jobs/<uuid:job_id>/", GenerationJobDetailView.as_view(), name="job-detail"),
    path(
        "jobs/<uuid:job_id>/certificates/",
        GenerationJobCertificatesView.as_view(),
        name="job-certificates",
    ),
    path(
        "certificates/<uuid:certificate_id>/",
        CertificateDetailView.as_view(),
        name="certificate-detail",
    ),
    path(
        "certificates/<uuid:certificate_id>/download/",
        CertificateDownloadView.as_view(),
        name="certificate-download",
    ),
]
