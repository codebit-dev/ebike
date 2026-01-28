from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path("admin/", admin.site.urls),  # Disabled - not using Django admin panel
    path("", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("inventory/", include("inventory.urls")),
    path("approvals/", include("approvals.urls")),
    path("sales/", include("sales.urls")),
    path("attendance/", include("attendance.urls")),
    path("services/", include("services.urls")),
    path("reports/", include("reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

