from urllib.parse import urlparse
from datetime import timedelta
from django.utils.timezone import now
from atlas.models import Referral, User


class ReferralMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ref_code = request.GET.get('ref') or request.COOKIES.get('atlas_ref')
        if ref_code:
            response = self.get_response(request)
            if not request.COOKIES.get('atlas_ref'):
                response.set_cookie('atlas_ref', ref_code, max_age=timedelta(days=40), httponly=True)
            return response
        return self.get_response(request)


class LandingSourceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'atlas_src' not in request.COOKIES:
            src = request.META.get('HTTP_REFERER', '') or 'direct'
            landing = request.build_absolute_uri(request.path)
            response.set_cookie('atlas_src', src, max_age=timedelta(days=30), samesite='Lax')
            response.set_cookie('atlas_landing', landing, max_age=timedelta(days=30), samesite='Lax')
        return response
