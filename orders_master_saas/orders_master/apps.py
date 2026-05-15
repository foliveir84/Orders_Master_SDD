from django.apps import AppConfig


class OrdersMasterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders_master"
    label = "orders_master"
    verbose_name = "Orders Master Domain"