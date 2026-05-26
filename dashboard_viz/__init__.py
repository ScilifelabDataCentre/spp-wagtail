"""Dashboard visualization services."""

from .registry import generate_figures
from .utils import figure_to_json

__all__ = [
    "figure_to_json",
    "generate_figures",
]
