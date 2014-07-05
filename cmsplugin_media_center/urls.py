from django.conf.urls import patterns, url

from cmsplugin_media_center.views import picture_view


urlpatterns = patterns(
    '',
    url(r'^(?P<category>[\w-]+)/$', picture_view, name='picture_category'),
)
