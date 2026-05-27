"""Convert stored Plotly JSON to embeddable HTML fragments."""

import json
import logging
from typing import Any

import plotly.io as pio

logger = logging.getLogger(__name__)


def plot_html_from_json(
    data: dict[str, Any] | str | None,
    *,
    height: str | int = "100%",
    skip_invalid: bool = False,
    include_plotlyjs: str | bool = False,
) -> str | None:
    """Build a Plotly HTML fragment from pre-computed figure JSON.

    Args:
        data: Plotly figure dict or JSON string with ``data`` and ``layout`` keys.
        height: Passed to Plotly's ``to_html`` as ``default_height``.
        skip_invalid: When True, invalid JSON properties are ignored.
        include_plotlyjs: Passed to Plotly's ``to_html`` (False when JS is loaded once).

    Returns:
        HTML fragment for template embedding, or None if conversion fails.
    """
    if data is None:
        logger.warning("plot_html_from_json called with None data")
        return None

    try:
        jstring = data if isinstance(data, str) else json.dumps(data)
        fig = pio.from_json(jstring, skip_invalid=skip_invalid)
        return fig.to_html(
            full_html=False,
            default_height=height,
            include_plotlyjs=include_plotlyjs,
        )
    except ValueError:
        logger.warning("Invalid Plotly JSON for plot HTML conversion", exc_info=True)
    except Exception:
        logger.warning("Failed to build plot HTML from JSON", exc_info=True)
    return None
