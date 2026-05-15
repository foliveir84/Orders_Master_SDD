from django import template

register = template.Library()


@register.filter
def get(dictionary, key):
    """Lookup a key in a dict, returning empty string on failure.

    Useful in templates where ``row.cell_classes|get:col`` avoids
    KeyError / AttributeError when a column has no special class.
    """
    if dictionary is None:
        return ""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""


@register.filter
def join(lst, separator=" "):
    """Join a list into a string with the given separator."""
    if not lst:
        return ""
    return separator.join(str(x) for x in lst)