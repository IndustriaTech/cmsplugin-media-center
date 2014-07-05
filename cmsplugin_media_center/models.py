from functools import reduce

from django.db import models
from django.db.models import Min
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from filer.fields.image import FilerImageField
from mptt.models import TreeForeignKey
from mptt.managers import TreeManager
from orderedmodel import OrderedMPTTModel


class PictureCategoryManager(TreeManager):
    def get_visible(self, *args, **kwargs):
        category = self.filter(*args, **kwargs).get()
        if category.is_shown():
            return category
        raise self.model.DoesNotExist

    def whole_tree(self):
        roots = self.filter(parent=None, is_visible=True)
        return reduce(lambda x, y: x | y, (root.get_visible_descendants() for root in roots))

    def show_subtree(self, include_self=True, from_node=None, depth=None):
        """
        If from_node argument is omitted we start from roots
        """
        nodes = self.filter(parent=None, is_visible=True) if from_node is None else [from_node]
        return reduce(lambda x, y: x | y, (
            node.get_visible_descendants(include_self=include_self, depth=depth) for node in nodes))


class PictureCategory(OrderedMPTTModel):

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    title = models.CharField(_(u'Title'), max_length=255)
    description = models.TextField(verbose_name=_(u'Description'), blank=True, default='')
    slug = models.SlugField(unique=True, max_length=255, db_index=True)
    is_published = models.BooleanField(_(u'Published'), default=False, db_index=True)
    is_visible = models.BooleanField(_(u'Visible'), default=False)
    objects = PictureCategoryManager()

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('Picture Category')
        verbose_name_plural = _('Picture Categories')
        permissions = (
            ('publish_permission', "Can publish picture categories"),
        )

    def __unicode__(self):
        return unicode(self.title)

    def has_visible_children(self):
        return any(child.check_visibility() for child in self.children.all().iterator())

    def check_visibility(self):
        """
        Returns True when category is published and:
            - it has pictures in it or
            - it's children are visible(published with pictures or subcategories)
            - or both.
        """
        if self.is_leaf_node():
            return self.is_published and self.pictures.exists()
        else:
            return self.is_published and (self.pictures.exists() or self.has_visible_children())

    def save(self, *args, **kwargs):
        visibility = self.check_visibility()
        changed = False
        if visibility != self.is_visible:
            self.is_visible = visibility
            changed = True
        super(PictureCategory, self).save(*args, **kwargs)
        if changed and self.parent and self.parent.is_visible != self.is_visible:
            self.parent.save()

    def get_cover(self):
        if self.pictures.exists():
            return self.pictures.order_by('-is_cover', 'pk')[0]

    def get_visible_descendants(self, include_self=True, depth=None):
        """
        Visible descendants are one that are visible and all their parents are visible too
        It is imporant for this method to always return a QuerySet of objects
        """
        if depth == 0:
            return PictureCategory.objects.filter(pk=self.pk)
        _depth = self.get_descendants().exclude(is_visible=True).aggregate(lvl=Min('level'))['lvl']
        depth, _depth = depth or 100, _depth or 100
        depth = depth + self.level if depth + self.level < _depth else _depth - 1
        return self.get_descendants(include_self=include_self).filter(is_visible=True,
                                                                      level__lte=depth)

    def is_shown(self):
        """
        If self is_visible and all its parents are visible too self is_shown() = True
        """
        return (self.is_visible and
                self.get_ancestors().count() ==
                self.get_ancestors().filter(is_visible=True).count())


@receiver(post_delete, sender=PictureCategory)
def update_visibility_on_delete(sender, instance, **kwargs):
    """
    We must update is_visible of all parent categories in case they are
    visible because of this subcategory we are deleting at this very moment
    """
    if instance.parent:
        instance.parent.save()


class Picture(models.Model):
    folder = models.ForeignKey(PictureCategory, related_name='pictures')
    image = FilerImageField(related_name='+')
    title = models.CharField(verbose_name=_('Title'), max_length=255, blank=True, default='')
    description = models.TextField(verbose_name=_('Description'), blank=True, default='')
    is_cover = models.BooleanField(default=False, verbose_name=_('Use as cover'))

    class Meta:
        verbose_name = _('Picture')
        verbose_name_plural = _('Pictures')

    def __unicode__(self):
        if self.title:
            return unicode(self.title)
        else:
            return "Picture {}".format(self.pk)

    def __init__(self, *args, **kwargs):
        super(Picture, self).__init__(*args, **kwargs)
        self._update_current_folder(self)

    def _update_current_folder(self, instance):
        instance._current_folder = self.folder_id

    def save(self, *args, **kwargs):
        if self._current_folder is None:
            self._update_current_folder(self)
        super(Picture, self).save(*args, **kwargs)


@receiver(post_save, sender=Picture)
def set_category_visibility_on_save(sender, instance, **kwargs):
    if instance._current_folder != instance.folder_id:
        PictureCategory.objects.get(pk=instance._current_folder).save()
        instance._update_current_folder(instance)
    if not instance.folder.is_visible and instance.folder.is_published:
        instance.folder.save()


@receiver(post_delete, sender=Picture)
def set_category_visibility_on_delete(sender, instance, **kwargs):
    try:
        if instance.folder.is_published:
            instance.folder.save()
    except PictureCategory.DoesNotExist:
        pass


class MediaPlugin(CMSPlugin):
    MEDIA_SKINS = (
        ('list', _('List view')),
        ('thumbnails', _('Thumbnail view')),
    )
    template = models.CharField(choices=MEDIA_SKINS, max_length=20, default='list')
