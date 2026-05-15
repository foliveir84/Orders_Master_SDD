from django.db import models

from accounts.models import Cliente


class ConfigLaboratorio(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    codigos_cla = models.JSONField(help_text='Lista de codigos CLA. Ex: ["137", "2651"]')
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "configlaboratorios"

    def __str__(self):
        return self.nome


class ConfigLocalizacao(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Se null, e uma config global (aplica-se a todos)",
        related_name="localizacoes",
    )
    search_term = models.CharField(
        max_length=200, help_text="Termo de pesquisa no campo LOCALIZACAO do Infoprex"
    )
    alias = models.CharField(max_length=100, help_text="Nome de apresentacao")

    class Meta:
        unique_together = ["cliente", "search_term"]
        ordering = ["search_term"]
        verbose_name_plural = "configlocalizacaos"

    def __str__(self):
        escopo = "Global" if not self.cliente else str(self.cliente.nome)
        return f"[{escopo}] {self.search_term} -> {self.alias}"


class ConfigPesoPreset(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    pesos = models.JSONField(help_text="Lista de 4 pesos. Ex: [0.4, 0.3, 0.2, 0.1]")

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "configpesopresets"

    def __str__(self):
        return self.nome


class SessaoProcessamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    utilizador = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    num_ficheiros = models.IntegerField()
    num_produtos = models.IntegerField()
    num_farmacias = models.IntegerField()
    lab_selecionados = models.JSONField(default=list)
    modo_detalhado = models.BooleanField(default=False)
    meses_previsao = models.FloatField(default=1.0)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Sessao {self.criado_em:%Y-%m-%d %H:%M} — {self.cliente.nome}"