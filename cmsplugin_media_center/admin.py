from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from orderedmodel.admin import OrderedStackedInline
from orderedmodel.mptt_admin import OrderedMPTTModelAdmin

from cmsplugin_media_center.models import Picture, PictureCategory
from cmsplugin_media_center.utils.admin import ActionsForObjectAdmin


class PictureInline(OrderedStackedInline):
    model = Picture
    extra = 1


class PictureCategoryAdmin(OrderedMPTTModelAdmin, ActionsForObjectAdmin):
    prepopulated_fields = {'slug': ('title', )}
    inlines = [PictureInline]
    list_display = ('title', 'is_visible', 'is_published')
    fields = ('parent', 'title', 'description', 'slug', 'is_published', 'is_visible')
    readonly_fields = ('is_visible', 'is_published')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(PictureCategoryAdmin, self).change_view(
            request,
            object_id,
            form_url='',
            extra_context={'has_publish_permission': request.user.has_perm('cmsplugin_media_center.publish_permission')})

    def make_published(self, request, queryset):
        if request.user.has_perm('cmsplugin_media_center.publish_permission'):
            for item in queryset:
                item.is_published = True
                item.save()
                self.log_change(request, item, 'Item published by %s' % request.user)
        else:
            raise PermissionDenied()
    make_published.short_description = _('Publish')

    def make_unpublished(self, request, queryset):
        if request.user.has_perm('news_and_promotions.publish_permission'):
            for item in queryset:
                item.is_published = False
                item.save()
                self.log_change(request, item, 'Item unpublished by %s' % request.user)
        else:
            raise PermissionDenied()
    make_unpublished.short_description = _('Unpublish')

    actions = ['make_published', 'make_unpublished']

admin.site.register(Picture)
admin.site.register(PictureCategory, PictureCategoryAdmin)
