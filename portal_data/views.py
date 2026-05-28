"""Django views for the portal_data app.

All routing and view logic has moved to ``portal_data.models.PortalDataPage``
via Wagtail's ``RoutablePageMixin``.  This module is kept as a package stub so
that any existing imports do not break immediately, but it no longer defines
``DataTypeList``, ``StudyFiles``, or ``DownloadStudyFile``.
"""
