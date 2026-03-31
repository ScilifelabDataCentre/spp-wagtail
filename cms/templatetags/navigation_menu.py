"""Template tags related to header."""

import structlog
from django import template
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models.query import QuerySet

from cms.snippets import NavigationMainMenu, NavigationMenu

LOGGER = structlog.get_logger(__name__)

register = template.Library()


@register.simple_tag
def get_menu(slug: str) -> QuerySet[NavigationMainMenu]:
    """Return menu items for a given slug with pages and sub-menu prefetched.

    Avoids N+1 queries when rendering menus in templates. Returns an empty
    queryset if no menu is found.

    Args:
        slug (str): Unique slug identifying the menu (e.g., "header", "footer").

    Returns:
        QuerySet[NavigationMainMenu]: Menu items queryset. Empty if menu not found.

    Example:
        {% load navigation_menu %}
        {% get_menu "header" as menu_items %}
        {% for item in menu_items %}
            <a href="{{ item.link }}">{{ item.title }}</a>
            {% if item.has_submenu %}
                {% for sub_item in item.sub_menu_items.all %}
                    <a href="{{ sub_item.link }}">{{ sub_item.title }}</a>
                {% endfor %}
            {% endif %}
        {% endfor %}
    """

    # TODO: Later if needed add caching to avoid DB query for every request

    try:
        menu = NavigationMenu.objects.prefetch_related(
            "main_menu_items__page", "main_menu_items__sub_menu_items__page"
        ).get(slug=slug)
        menu_items = menu.main_menu_items.all()
        return menu_items
    except ObjectDoesNotExist as e:
        LOGGER.warning(f"Couldn't find navigation menu for slug '{slug}':\n{e}")
    except MultipleObjectsReturned as e:
        LOGGER.warning(f"Found duplicates entries for slug '{slug}':\n{e}")
    except Exception as e:
        LOGGER.warning(f"Problem fetching navigation items for slug '{slug}':\n{e}")

    # Return empty QuerySet
    return NavigationMainMenu.objects.none()
