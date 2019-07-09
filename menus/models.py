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
    root = cls.objects.first().get_root()
    entries = build_menu_entries(root)
    return entries


def build_menu_entries(node_instance):
    instance = node_instance
    entries = []
    while instance:
        node, instance = new_menu_node(instance)
        entries.append(node)
    return entries


def new_menu_node(node_instance):
    children = get_children(node_instance)
    return dict(
        {
            "caption": node_instance.caption,
            "description": node_instance.description,
            "icon": node_instance.icon,
            "enabled": node_instance.enabled,
            "separator": node_instance.separator,
            "route": node_instance.route,
        },
        **({"children": children} if children else {})
    ), node_instance.get_next_sibling()


def get_children(node_instance):
    children = node_instance.get_children()
    if children:
        return build_menu_entries(children.first())
    return None
