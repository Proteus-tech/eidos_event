from django_request_local.middleware import RequestLocal

def get_current_user_url():
    request = RequestLocal.get_current_request()
    if request:
        return request.COOKIES.get('remote_user')
    # cannot find request
    return ''