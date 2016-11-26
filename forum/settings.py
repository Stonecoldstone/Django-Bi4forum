from django.conf import settings


def get(key, default):
    return getattr(settings, key, default)

FORUM_NAME = get('FORUM_NAME', 'Bi4forum')
FILE_MAX_SIZE = get('FILE_MAX_SIZE', 1024 * 1024)
POSTS_ON_PAGE = get('POSTS_ON_PAGE', 20)
THREADS_ON_PAGE = get('THREADS_ON_PAGE', 20)
AVATAR_SIZE = get('AVATAR_SIZE', (200, 200))
LOGIN_URL = get('LOGIN_URL', 'forum:login')
LOGIN_REDIRECT_URL = get('LOGIN_REDIRECT_URL', 'forum:main_page')