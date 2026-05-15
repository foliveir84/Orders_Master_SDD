import logging

from accounts.models import Cliente, Farmacia

logger = logging.getLogger(__name__)


def validate_localizacao(localizacao: str, cliente: Cliente) -> Farmacia | None:
    """Match an Infoprex LOCALIZACAO value against the client's active farmacias.

    Uses case-insensitive substring matching in both directions so that
    partial names or extra qualifiers in either direction still resolve.

    Returns the matching Farmacia or None.
    """
    localizacao_lower = localizacao.lower()
    for farmacia in Farmacia.objects.filter(cliente=cliente, ativa=True):
        if farmacia.localizacao_key.lower() in localizacao_lower:
            return farmacia
        if localizacao_lower in farmacia.localizacao_key.lower():
            return farmacia
    return None