from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from accounts.models import Cliente, Farmacia, Subscricao, UserProfile


# ── Inlines ──────────────────────────────────────────────────────────


class FarmaciaInline(admin.TabularInline):
    model = Farmacia
    extra = 1
    fields = ("nome", "localizacao_key", "alias", "ativa", "licenciada_ate")


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Perfil"
    verbose_name_plural = "Perfil"
    fields = ("cliente", "role")


# ── ModelAdmins ───────────────────────────────────────────────────────


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "nif", "email", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "nif", "email")
    inlines = [FarmaciaInline]
    actions = ["activate", "deactivate"]

    @admin.action(description="Ativar clientes seleccionados")
    def activate(self, request, queryset):
        queryset.update(ativo=True)

    @admin.action(description="Desativar clientes seleccionados")
    def deactivate(self, request, queryset):
        queryset.update(ativo=False)


@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    list_display = ("alias", "nome", "cliente", "localizacao_key", "ativa", "licenciada_ate")
    list_filter = ("ativa", "cliente")
    search_fields = ("nome", "alias", "localizacao_key")
    raw_id_fields = ("cliente",)
    actions = ["activate", "deactivate"]

    @admin.action(description="Ativar farmacias seleccionadas")
    def activate(self, request, queryset):
        queryset.update(ativa=True)

    @admin.action(description="Desativar farmacias seleccionadas")
    def deactivate(self, request, queryset):
        queryset.update(ativa=False)


@admin.register(Subscricao)
class SubscricaoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "plano", "bd_rupturas_ativa", "data_inicio", "data_fim", "ativa")
    list_filter = ("plano", "ativa", "bd_rupturas_ativa")
    raw_id_fields = ("cliente",)


# ── Extend UserAdmin with UserProfile inline ──────────────────────────

# Unregister the default User admin so we can re-register with our inline
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = list(UserAdmin.inlines) + [UserProfileInline]