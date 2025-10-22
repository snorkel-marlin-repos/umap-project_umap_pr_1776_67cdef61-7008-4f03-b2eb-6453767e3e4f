from django.conf import settings as djsettings

from . import VERSION


def settings(request):
    return {
        "UMAP_FEEDBACK_LINK": djsettings.UMAP_FEEDBACK_LINK,
        "SITE_NAME": djsettings.SITE_NAME,
        "SITE_URL": djsettings.SITE_URL,
        "ENABLE_ACCOUNT_LOGIN": djsettings.ENABLE_ACCOUNT_LOGIN,
        "UMAP_READONLY": djsettings.UMAP_READONLY,
        "UMAP_DEMO_SITE": djsettings.UMAP_DEMO_SITE,
    }


def version(request):
    return {"UMAP_VERSION": VERSION}
