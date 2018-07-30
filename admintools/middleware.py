# Python Standard Library Imports

# Third Party / PIP Imports
import rollbar

# Django Imports
from django.contrib import messages

# HTK Imports
from htk.admintools.utils import is_allowed_to_emulate_users
from htk.admintools.utils import is_allowed_to_emulate


class HtkEmulateUserMiddleware(object):
    def process_request(self, request):
        """Replace the authenticated `request.user` if properly emulating
        """
        if is_allowed_to_emulate_users(request.user):
            from htk.apps.accounts.utils import get_user_by_id
            from htk.apps.accounts.utils import get_user_by_username

            user_id = request.COOKIES.get('emulate_user_id')
            username = request.COOKIES.get('emulate_user_username')

            is_attempting_to_emulate = user_id or username

            if is_attempting_to_emulate:
                if user_id:
                    targeted_user = get_user_by_id(user_id)
                elif username:
                    targeted_user = get_user_by_username(username)
                else:
                    rollbar.report_message('Impossible case: attempting to emulate another user but not specified')

                if targeted_user is None:
                    messages.error(request, 'Cannot Emulate: User does not exist', fail_silently=True)
                    pass
                else:
                    if is_allowed_to_emulate(request.user, targeted_user):
                        request.original_user = request.user
                        request.user = targeted_user
                    else:
                        messages.error(request, 'Cannot Emulate: Not allowed to emulate that user', fail_silently=True)
                        pass
            else:
                # not attempting to emulate
                pass
        else:
            messages.error(request, 'Cannot Emulate: Not allowed to emulate that user', fail_silently=True)
            pass


    def process_response(self, request, response):
        """Delete user emulation cookies if they should not be set
        """
        original_user = getattr(request, 'original_user', None)
        user = getattr(request, 'user', None)
        is_emulating = original_user is not None and user is not None
        if not is_emulating:
            response.delete_cookie('emulate_user_id')
            response.delete_cookie('emulate_user_username')

        return response
