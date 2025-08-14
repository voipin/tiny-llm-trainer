from django.contrib.auth import login
from django.contrib.auth.models import User


class AutoLoginMiddleware:
    """
    Middleware that automatically logs in the admin user for testing purposes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Auto-login as admin if not already authenticated
        if not request.user.is_authenticated:
            try:
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    login(request, admin_user)
            except Exception:
                pass  # Silently fail if admin user doesn't exist

        response = self.get_response(request)
        return response