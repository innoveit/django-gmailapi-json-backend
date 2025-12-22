import django
from django.conf import settings


def pytest_configure():
    # Minimal settings for using django.core.mail in a library repo (no Django project).
    if not settings.configured:
        settings.configure(
            SECRET_KEY="tests",
            INSTALLED_APPS=[],
            DEFAULT_CHARSET="utf-8",
            USE_I18N=False,
            USE_TZ=False,
        )
    django.setup()


