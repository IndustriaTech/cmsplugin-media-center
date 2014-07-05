from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from cmsplugin_media_center.models import PictureCategory, MediaPlugin


class CMSMediaPlugin(CMSPluginBase):
    model = MediaPlugin
    module = _("Media center")
    name = _('Pictures Gallery')
    render_template = ''

    def render(self, context, instance, placeholder):
        category = None
        template = instance.template

        if 'category' in context:
            try:
                category = PictureCategory.objects.get_visible(slug=context['category'])
            except PictureCategory.DoesNotExist:
                raise Http404

            context.update({
                'category': category,
                'photo_list': category.pictures.all(),
            })

        context['category_list'] = categories_queryset(template=template, category=category)
        self.render_template = 'cmsplugin_media_center/templates/pictures/{}.html'.format(template)
        return context

plugin_pool.register_plugin(CMSMediaPlugin)


def categories_queryset(template, category=None):
    if template == 'list':
        return PictureCategory.objects.whole_tree()
    else:
        from_node, depth = category, 0 if category is None else 1
        return PictureCategory.objects.show_subtree(from_node=from_node, depth=depth)
