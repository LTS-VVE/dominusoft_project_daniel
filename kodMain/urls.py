from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentication
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),

    # Main pages
    path("", include("pages.urls")),

    # Applications
    path("", include("tickets.urls")),
    path("njohuri/", include("knowledge.urls")),
    path("ngjarje/", include("events.urls")),
    path("burime/", include("resources.urls")),
    path("anetaret/", include("accounts.member_urls")),

    # Block management
    path("dataviewer/", include("dataviewer.urls"))
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )