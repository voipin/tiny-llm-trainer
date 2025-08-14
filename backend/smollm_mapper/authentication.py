from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication that doesn't enforce CSRF checks.
    Use this for API endpoints that are accessed via AJAX from trusted origins.
    """
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening