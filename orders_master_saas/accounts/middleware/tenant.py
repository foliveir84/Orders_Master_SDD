"""
Tenant middleware for multi-tenant SaaS support.

Resolves the current tenant from the authenticated user's profile and
attaches it to the request object as ``request.tenant``.
Also sets ``request.subscription_expired`` when the active subscription
has passed its end date.
"""

from datetime import date


class TenantMiddleware:
    """Resolve and attach the current tenant to the request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.tenant = request.user.profile.cliente
                sub = request.tenant.subscricao
                if sub and sub.ativa and sub.data_fim and sub.data_fim < date.today():
                    request.subscription_expired = True
                else:
                    request.subscription_expired = False
            except Exception:
                request.tenant = None
                request.subscription_expired = False
        response = self.get_response(request)
        return response