from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


class PicturesHook(CMSApp):
    name = _("Pictures")
    urls = ["cmsplugin_media_center.urls"]
apphook_pool.register(PicturesHook)
