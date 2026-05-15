from django.contrib import admin

from orders.models import ConfigLaboratorio, ConfigLocalizacao, ConfigPesoPreset


@admin.register(ConfigLaboratorio)
class ConfigLaboratorioAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(ConfigLocalizacao)
class ConfigLocalizacaoAdmin(admin.ModelAdmin):
    list_display = ("search_term", "alias", "escopo")
    list_filter = ("cliente",)
    search_fields = ("search_term", "alias")

    @admin.display(description="Escopo")
    def escopo(self, obj):
        return "Global" if not obj.cliente else str(obj.cliente.nome)


@admin.register(ConfigPesoPreset)
class ConfigPesoPresetAdmin(admin.ModelAdmin):
    list_display = ("nome", "pesos_display")
    search_fields = ("nome",)

    @admin.display(description="Pesos")
    def pesos_display(self, obj):
        return obj.pesos