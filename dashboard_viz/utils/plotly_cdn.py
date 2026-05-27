"""Plotly.js CDN helpers aligned with the installed Plotly Python package."""

import re
from functools import lru_cache

import plotly.io as pio
import structlog

LOGGER = structlog.get_logger(__name__)

_PLOTLYJS_SCRIPT_PATTERN = re.compile(
    r'<script.*?src="([^"]+plotly[^"]+\.js)".*?integrity="(.*?)".*?</script>',
)


@lru_cache
def get_plotlyjs_cdn_param(param: str) -> str | None:
    """Return the Plotly.js CDN URL or SRI hash for the installed Plotly version.

    Args:
        param: ``"url"`` for the script URL, or ``"hash"`` for the integrity value.

    Returns:
        The requested CDN parameter, or ``None`` if extraction fails.
    """
    if param not in ("url", "hash"):
        LOGGER.warning("plotly_cdn.invalid_param", param=param)
        return None

    html_string = pio.to_html({}, full_html=False, include_plotlyjs="cdn")
    match = _PLOTLYJS_SCRIPT_PATTERN.search(html_string)
    if not match:
        LOGGER.warning("plotly_cdn.script_tag_not_found")
        return None

    index = 0 if param == "url" else 1
    return match.group(index + 1)
