import simplejson as json
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class SystemMenu(MPTTModel):
    caption = models.CharField("Caption", max_length=100, blank=True, null=True)
    description = models.CharField("Description", max_length=255, blank=True, null=True)
    order = models.IntegerField("Order", default=0, blank=True, null=True)
    separator = models.BooleanField("Separator", default=False)
    enabled = models.BooleanField("Enabled", default=True)
    icon = models.CharField("Icon", max_length=50, blank=True, null=True)
    route = models.CharField("Route", max_length=255, blank=True, null=True)
    scopes = models.CharField("Scopes", max_length=255, blank=True, null=True, help_text="Access scopes separeted by commas")
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.caption or (("-" * 20) if self.separator else None) or  "No description"

    class MPTTMeta:
        order_insertion_by = ['order']


def as_dict(cls):
    return build_menu_entries(cls.objects)


def build_menu_entries(node_manager):
    return [new_menu_node(n) for n in node_manager.all()]


def new_menu_node(menu_obj):
    children = build_menu_entries(menu_obj.children)
    return dict(
        {
            "caption": menu_obj.caption,
            "description": menu_obj.description,
            "icon": menu_obj.icon,
            "enabled": menu_obj.enabled,
            "separator": menu_obj.separator,
            "route": menu_obj.route,
        },
        **({"children": children} if children else {})
    )
