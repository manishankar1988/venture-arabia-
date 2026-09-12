from django.conf import settings


class SecurityHeadersMiddleware:
    """Adds Content-Security-Policy and Permissions-Policy headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # The admin uses inline scripts, so it gets a relaxed policy.
        if request.path.startswith("/" + settings.ADMIN_URL):
            response.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'",
            )
        else:
            response.setdefault("Content-Security-Policy", settings.CSP_POLICY)
        response.setdefault("Permissions-Policy", settings.PERMISSIONS_POLICY)
        return response
