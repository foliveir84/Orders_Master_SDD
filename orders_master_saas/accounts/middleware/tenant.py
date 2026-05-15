"""
Tenant middleware for multi-tenant SaaS support.

Resolves the current tenant from the request and attaches it to the
request object. Full implementation will be provided in MIG-3.2.
"""


class TenantMiddleware:
    """Resolve and attach the current tenant to the request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO: MIG-3.2 - implement tenant resolution from subdomain or user profile
        request.tenant = None
        response = self.get_response(request)
        return response