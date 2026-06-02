"""Decorator functions that can be applied to in the CMS page utilities."""

from collections.abc import Callable
from functools import wraps

from django.shortcuts import render
from django.utils.http import urlencode


def htmx_request_with_url_update(template_attr: str = "htmx_template") -> Callable:
    """Update the URL for HTMX requests while rendering a specific template."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):  # noqa: ANN001, ANN202
            if request.htmx:
                template_name = getattr(self, template_attr)

                query = request.GET.copy()
                query.pop("search", None)

                clean_url = (
                    f"{request.path}?{urlencode(query, doseq=True)}" if query else request.path
                )

                response = render(request, template_name, self.get_context(request))
                response["HX-Replace-Url"] = clean_url
                return response

            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator
