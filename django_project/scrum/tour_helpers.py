# tour_helpers.py

SESSION_KEY = 'show_tour_welcome'


def set_tour_welcome(request, user):
    """
    Call this right after a successful login to flag the welcome modal.
    """
    seen_key = f'tour_seen_{user.pk}'
    if not request.session.get(seen_key, False):
        request.session[SESSION_KEY] = True
        request.session[seen_key] = True


def clear_tour_welcome(request):
    """
    Clear the welcome flag after showing the modal.
    """
    request.session.pop(SESSION_KEY, None)


class TourMixin:
    """
    Add to any CBV to automatically handle tour session flag.
    """

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        clear_tour_welcome(self.request)
        return ctx


class TourMiddleware:
    """
    Middleware that detects a user's very first request after login
    and sets the session flag automatically.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        if request.user.is_authenticated:
            seen_key = f'tour_seen_{request.user.pk}'
            if not request.session.get(seen_key, False):
                request.session[SESSION_KEY] = True
                request.session[seen_key] = True

        response = self.get_response(request)
        return response