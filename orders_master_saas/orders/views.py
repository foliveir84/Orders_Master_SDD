import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render

from orders_master.app_services.recalc_service import recalculate_proposal
from orders_master.app_services.session_service import process_orders_session
from orders_master.app_services.session_state import SessionState
from orders_master.constants import CSS, Columns, GroupLabels, Weights
from orders_master.formatting.excel_formatter import build_excel
from orders_master.formatting.rules import RULES

from orders.forms import RecalcForm, UploadForm
from orders.services.license import validate_localizacao
from orders.services.processing_session import ProcessingSession

logger = logging.getLogger(__name__)

_PRESET_WEIGHTS = {
    "CONSERVADOR": Weights.CONSERVADOR,
    "PADRAO": Weights.PADRAO,
    "AGRESSIVO": Weights.AGRESSIVO,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prepare_rows(df):
    """Convert a DataFrame into a list of row-dicts suitable for template rendering.

    Each dict contains:
      - ``cells``: mapping of column name to display value
      - ``row_classes``: CSS classes for the ``<tr>``
      - ``cell_classes``: mapping of column name to CSS class(es)
    """
    if df is None or df.empty:
        return [], []

    columns = list(df.columns)
    rows = []

    for _, pd_row in df.iterrows():
        row_classes = []
        cell_classes = {}
        cells = {}

        for col in columns:
            val = pd_row.get(col)
            # Format for display
            if val is None or (isinstance(val, float) is False and hasattr(val, "__class__") and val.__class__.__name__ == "NAType"):
                cells[col] = ""
            elif hasattr(val, "item"):
                # numpy scalar -> python scalar
                cells[col] = val.item()
            else:
                cells[col] = val

        # Apply RULES to determine CSS classes
        is_grupo = pd_row.get(Columns.LOCALIZACAO) == GroupLabels.GROUP_ROW

        for rule in RULES:
            # Precedence: Grupo row only gets rule 1
            if is_grupo and rule.precedence > 1:
                continue

            try:
                if rule.predicate(pd_row):
                    target_cols = rule.target_cells(df)
                    if rule.precedence == 1:
                        # Grupo -> row-level class
                        row_classes.append(CSS.GRUPO)
                    elif rule.precedence == 2:
                        # Nao Comprar -> cell-level class on target cells
                        for tc in target_cols:
                            cell_classes[tc] = cell_classes.get(tc, "") + " " + CSS.NAO_COMPRAR
                    else:
                        # Cell-level classes (Rutura, Validade, Anomalo)
                        css_class = {
                            3: CSS.RUTURA,
                            4: CSS.VALIDADE_CURTA,
                            5: CSS.PRECO_ANOMALO,
                        }.get(rule.precedence, "")
                        for tc in target_cols:
                            cell_classes[tc] = cell_classes.get(tc, "") + " " + css_class

            except Exception:
                logger.debug("Rule %s skipped for row", rule.name, exc_info=True)

        rows.append({
            "cells": cells,
            "row_classes": " ".join(row_classes).strip(),
            "cell_classes": cell_classes,
        })

    return rows, columns


def _get_session(request) -> ProcessingSession:
    """Return a ProcessingSession scoped to the current request's Django session."""
    return ProcessingSession(request.session.session_key or request.session.create())


def _get_weights(preset: str) -> tuple[float, ...]:
    return _PRESET_WEIGHTS.get(preset, Weights.PADRAO)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@login_required
def upload_view(request):
    """Upload Infoprex files and run the heavy processing pipeline."""
    if getattr(request, "subscription_expired", False):
        return render(request, "orders/subscription_expired.html", status=403)

    ps = _get_session(request)

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist("files")
            codes_file = request.FILES.get("codes_file") or None
            brands_files = request.FILES.getlist("brands_file")

            # Load config from DB for the current tenant
            from orders_master.config.labs_loader import load_labs_from_db
            from orders_master.config.locations_loader import load_locations_from_db

            tenant = getattr(request, "tenant", None)
            client_id = tenant.id if tenant else None
            labs_dict = load_labs_from_db(client_id)
            locations_aliases = load_locations_from_db(client_id)

            # Build labs_config (LabsConfig) and labs_selected from DB
            from orders_master.config.labs_loader import LabsConfig

            try:
                labs_config = LabsConfig(root=labs_dict)
            except Exception:
                labs_config = None

            labs_selected = list(labs_dict.keys())

            # License validation: check that at least one file matches a farmacia
            if tenant:
                from accounts.models import Farmacia

                active_farmacias = Farmacia.objects.filter(cliente=tenant, ativa=True)
                if active_farmacias.exists():
                    for f in files:
                        fname = getattr(f, "name", "").lower()
                        matched = validate_localizacao(fname, tenant)
                        if matched:
                            break
                    else:
                        # No file matched any farmacia — still proceed but warn
                        messages.warning(
                            request,
                            "Nenhuma farmácia reconhecida nos ficheiros. Verifique os nomes.",
                        )

            # BD Rupturas feature flag
            bd_rupturas_active = False
            if hasattr(request, "tenant") and request.tenant:
                try:
                    bd_rupturas_active = request.tenant.subscricao.bd_rupturas_ativa and request.tenant.subscricao.ativa
                except Exception:
                    bd_rupturas_active = False

            # Run the heavy pipeline
            state = SessionState()
            try:
                process_orders_session(
                    files=files,
                    codes_file=codes_file,
                    brands_files=brands_files,
                    labs_selected=labs_selected,
                    labs_config=labs_config,
                    locations_aliases=locations_aliases,
                    state=state,
                    bd_rupturas_active=bd_rupturas_active,
                )
            except Exception as exc:
                logger.exception("Erro no processamento")
                messages.error(request, f"Erro no processamento: {exc}")
                return render(request, "orders/upload.html", {"form": form})

            # Store results in ProcessingSession (cache)
            if not state.df_aggregated.empty:
                ps.store("df_aggregated", state.df_aggregated)
                ps.store("df_detailed", state.df_detailed)
                ps.store("df_master_products", state.df_master_products)
                ps.store_value("file_inventory", [
                    {
                        "filename": e.filename,
                        "farmacia": e.farmacia,
                        "n_linhas": e.n_linhas,
                        "duv_max": e.duv_max,
                        "avisos": e.avisos,
                        "status": e.status,
                        "error_message": e.error_message,
                    }
                    for e in state.file_inventory
                ])
                ps.store_value("scope_context", {
                    "n_produtos": state.scope_context.n_produtos,
                    "n_farmacias": state.scope_context.n_farmacias,
                    "descricao_filtro": state.scope_context.descricao_filtro,
                    "primeiro_mes": state.scope_context.primeiro_mes,
                    "ultimo_mes": state.scope_context.ultimo_mes,
                    "ano_range": state.scope_context.ano_range,
                    "meses": state.scope_context.meses,
                    "modo": state.scope_context.modo,
                })
                ps.store_value("shortages_data_consulta", state.shortages_data_consulta)
                ps.store_value("bd_rupturas_active", bd_rupturas_active)
                # Default initial view
                ps.store_value("detailed_view", False)
                ps.store_value("meses", 1.0)
                ps.store_value("preset", "PADRAO")
                ps.store_value("use_previous_month", False)

                messages.success(request, f"{len(files)} ficheiro(s) processado(s) com sucesso.")
                return redirect("orders:results")
            else:
                messages.warning(request, "Nenhum dado encontrado nos ficheiros.")
                return render(request, "orders/upload.html", {"form": form})
    else:
        form = UploadForm()

    return render(request, "orders/upload.html", {"form": form})


@login_required
def results_view(request):
    """Display processed results with the conditional table."""
    if getattr(request, "subscription_expired", False):
        return render(request, "orders/subscription_expired.html", status=403)

    ps = _get_session(request)

    # Retrieve the current DataFrame
    detailed_view = ps.get_value("detailed_view") or False
    df_key = "df_detailed" if detailed_view else "df_aggregated"
    df = ps.get(df_key)

    if df is None or df.empty:
        messages.info(request, "Sessão expirada ou sem dados. Faça upload novamente.")
        return redirect("orders:upload")

    rows, columns = _prepare_rows(df)
    scope = ps.get_value("scope_context") or {}
    file_inventory = ps.get_value("file_inventory") or []
    shortages_data = ps.get_value("shortages_data_consulta")
    bd_rupturas_active = ps.get_value("bd_rupturas_active") or False
    meses = ps.get_value("meses") or 1.0
    preset = ps.get_value("preset") or "PADRAO"
    use_previous_month = ps.get_value("use_previous_month") or False

    form = RecalcForm(initial={
        "detailed_view": detailed_view,
        "meses": meses,
        "preset": preset,
        "use_previous_month": use_previous_month,
    })

    context = {
        "rows": rows,
        "columns": columns,
        "scope": scope,
        "file_inventory": file_inventory,
        "shortages_data": shortages_data,
        "bd_rupturas_active": bd_rupturas_active,
        "form": form,
        "detailed_view": detailed_view,
    }
    return render(request, "orders/results.html", context)


@login_required
def recalc_view(request):
    """HTMX endpoint: recalculate proposals with new parameters."""
    ps = _get_session(request)

    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = RecalcForm(request.POST)
    if not form.is_valid():
        # Return current table unchanged on invalid form
        return _render_table_partial(ps)

    detailed_view = form.cleaned_data["detailed_view"]
    meses = form.cleaned_data["meses"]
    preset = form.cleaned_data["preset"]
    use_previous_month = form.cleaned_data["use_previous_month"]
    marcas_raw = form.cleaned_data.get("marcas", "")
    marcas = json.loads(marcas_raw) if marcas_raw else None

    weights = _get_weights(preset)

    # Save control state for future page reloads
    ps.store_value("detailed_view", detailed_view)
    ps.store_value("meses", meses)
    ps.store_value("preset", preset)
    ps.store_value("use_previous_month", use_previous_month)

    # Retrieve DataFrames for recalculation
    df_detailed = ps.get("df_detailed")
    df_master = ps.get("df_master_products")

    if df_detailed is None or df_detailed.empty:
        return HttpResponse("<tr><td colspan='99'>Sem dados. Faça upload.</td></tr>")

    # Run lightweight recalc
    scope_context_dict = ps.get_value("scope_context") or {}
    from orders_master.app_services.session_state import ScopeContext
    scope_ctx = ScopeContext(**{k: v for k, v in scope_context_dict.items() if k in ScopeContext.__dataclass_fields__})

    df_result = recalculate_proposal(
        df_detailed=df_detailed,
        detailed_view=detailed_view,
        df_master_products=df_master,
        months=meses,
        weights=weights,
        use_previous_month=use_previous_month,
        marcas=marcas,
        scope_context=scope_ctx,
    )

    # Store the recalculated DataFrame
    if detailed_view:
        ps.store("df_detailed", df_result)
    else:
        ps.store("df_aggregated", df_result)

    # Update scope in cache
    ps.store_value("scope_context", {
        "n_produtos": scope_ctx.n_produtos,
        "n_farmacias": scope_ctx.n_farmacias,
        "descricao_filtro": scope_ctx.descricao_filtro,
        "primeiro_mes": scope_ctx.primeiro_mes,
        "ultimo_mes": scope_ctx.ultimo_mes,
        "ano_range": scope_ctx.ano_range,
        "meses": scope_ctx.meses,
        "modo": scope_ctx.modo,
    })

    return _render_table_partial(ps, df_result)


def _render_table_partial(ps: ProcessingSession, df=None):
    """Render just the table + scope bar for HTMX swap."""
    if df is None:
        detailed_view = ps.get_value("detailed_view") or False
        df_key = "df_detailed" if detailed_view else "df_aggregated"
        df = ps.get(df_key)

    rows, columns = _prepare_rows(df)
    scope = ps.get_value("scope_context") or {}

    return render(None, "orders/_table_rows.html", {
        "rows": rows,
        "columns": columns,
        "scope": scope,
    })


@login_required
def download_excel_view(request):
    """Download the current results as a formatted Excel file."""
    ps = _get_session(request)

    detailed_view = ps.get_value("detailed_view") or False
    df_key = "df_detailed" if detailed_view else "df_aggregated"
    df = ps.get(df_key)

    if df is None or df.empty:
        messages.info(request, "Sem dados para exportar. Faça upload primeiro.")
        return redirect("orders:results")

    scope = ps.get_value("scope_context") or {}
    scope_tag = scope.get("descricao_filtro", "GRUPO")
    # Sanitize for filename
    scope_tag = scope_tag.replace(" ", "-")[:40]

    excel_bytes, filename = build_excel(df, scope_tag)

    response = HttpResponse(
        excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response