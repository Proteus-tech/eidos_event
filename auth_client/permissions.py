# -*- coding: utf-8 -*-
from djangorestframework import status
from djangorestframework.response import ErrorResponse
from djangorestframework.permissions import BasePermission

from django.conf import settings

__all__ = (
    'IsAuthenticated',
)

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def check_permission(self, user):
        if not user.is_authenticated():
            request = self.view.request
            current_url = request.build_absolute_uri(request.path)
            raise ErrorResponse(
                status.HTTP_401_UNAUTHORIZED,
                    {'detail': 'The request requires user authentication.'},
                    {'WWW-Authenticate': 'DJANGO_API realm="POST:%s?next=%s"' % (settings.LOGIN_URL, current_url)}
            )