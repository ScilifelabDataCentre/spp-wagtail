"""URL configuration for the portal_data app.

All URL routing has moved to ``portal_data.models.PortalDataPage`` via
Wagtail's ``RoutablePageMixin``.  This file can be deleted once you are
satisfied no external code imports from it.
"""

app_name = "portal_data"
urlpatterns: list = []
