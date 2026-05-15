from django.contrib.auth.models import User
from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    actualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Farmacia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="farmacias")
    nome = models.CharField(max_length=200)
    localizacao_key = models.CharField(
        max_length=100,
        help_text="Valor exacto do campo LOCALIZACAO no Infoprex (ex: 'FARMACIA GUIA')",
    )
    alias = models.CharField(max_length=100, help_text="Nome de apresentacao (ex: 'Guia')")
    ativa = models.BooleanField(default=True)
    licenciada_ate = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["cliente", "localizacao_key"]
        ordering = ["alias"]
        verbose_name_plural = "farmacias"

    def __str__(self):
        return f"{self.alias} ({self.cliente.nome})"


class Subscricao(models.Model):
    class Plano(models.TextChoices):
        BASICO = "BAS", "Basico"
        PROFISSIONAL = "PRO", "Profissional"
        ENTERPRISE = "ENT", "Enterprise"

    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name="subscricao")
    plano = models.CharField(max_length=3, choices=Plano.choices, default=Plano.BASICO)
    bd_rupturas_ativa = models.BooleanField(
        default=False, help_text="Extra pago: acesso a BD Esgotados Infarmed"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.get_plano_display()}"


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        COMPRAS = "compras", "Responsavel de Compras"
        FARMACIA = "farmacia", "Farmacia"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="utilizadores")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COMPRAS)

    def __str__(self):
        return f"{self.user.username} ({self.cliente.nome})"