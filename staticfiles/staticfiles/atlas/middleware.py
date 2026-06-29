from django.utils.timezone import now
from datetime import timedelta
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
