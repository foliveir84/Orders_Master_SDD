"""
Tenant middleware for multi-tenant SaaS support.

Resolves the current tenant from the authenticated user's profile and
attaches it to the request object as ``request.tenant``.
"""


class TenantMiddleware:
    """Resolve and attach the current tenant to the request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.tenant = request.user.profile.cliente
            except Exception:
                request.tenant = None
        response = self.get_response(request)
        return response