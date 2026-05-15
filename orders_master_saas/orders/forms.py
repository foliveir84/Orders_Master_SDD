from django import forms

from orders_master.constants import Limits, Weights


class MultipleFileInput(forms.FileInput):
    """FileInput that allows multiple file selection."""

    allow_multiple_selected = True

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs.setdefault("multiple", True)
        super().__init__(attrs=attrs)


class UploadForm(forms.Form):
    """Form for uploading Infoprex files, optional codes file, and brands file."""

    files = forms.FileField(
        widget=MultipleFileInput(attrs={"accept": ".xls,.xlsx"}),
        label="Ficheiros Infoprex",
    )
    codes_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"accept": ".txt"}),
        label="Lista de Códigos (TXT)",
    )
    brands_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"accept": ".csv"}),
        label="Ficheiro de Marcas (CSV)",
    )


class RecalcForm(forms.Form):
    """Form for recalculation controls (HTMX partial)."""

    detailed_view = forms.BooleanField(required=False, label="Vista Detalhada")
    meses = forms.FloatField(
        min_value=Limits.MESES_PREVISAO_MIN,
        max_value=Limits.MESES_PREVISAO_MAX,
        initial=Limits.MESES_PREVISAO_DEFAULT,
        widget=forms.NumberInput(attrs={
            "step": Limits.MESES_PREVISAO_STEP,
            "min": Limits.MESES_PREVISAO_MIN,
            "max": Limits.MESES_PREVISAO_MAX,
            "class": "w-20 text-right",
        }),
        label="Meses de Previsão",
    )
    preset = forms.ChoiceField(
        choices=[
            ("PADRAO", "Padrão"),
            ("CONSERVADOR", "Conservador"),
            ("AGRESSIVO", "Agressivo"),
        ],
        initial="PADRAO",
        widget=forms.Select(attrs={"class": "rounded border-gray-300 text-sm"}),
        label="Preset de Pesos",
    )
    use_previous_month = forms.BooleanField(required=False, label="Ignorar Mês Anterior")
    marcas = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="Marcas (JSON)",
    )