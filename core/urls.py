"""URL configuration for Pathogens Portal project."""

# Third-party imports
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls

# Local imports
from core.views import healthz

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls, name="admin"),
    path("healthz/", healthz, name="healthz"),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path(settings.WAGTAILADMIN_URL, include(wagtailadmin_urls)),
    path("cms/", include("cms.urls")),
    # portal_data routes (listing + file browser + downloads) are now handled
    # by portal_data.models.PortalDataPage via RoutablePageMixin.  Wagtail
    # serves the page at whatever URL it occupies in the page tree, so no
    # explicit prefix is needed here.
    path("", include(wagtail_urls)),
]
