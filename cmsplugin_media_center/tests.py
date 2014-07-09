from django.test import TestCase

from cmsplugin_media_center.models import PictureCategory, Picture


class CMSPluginMediaCenterTests(TestCase):

    fixtures = ['auth_fixtures', 'filer_fixtures', 'media_center_fixtures']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fixtures_loaded(self):
        self.assertNotEqual(PictureCategory.objects.count(), 0)

    def test_category_visibility_unpublished(self):
        """
        We add category which is unpublished.
        Wether it has pictures or not it must not be visible
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=False,
                                              is_visible=True,
                                              slug="test")
        self.assertFalse(test.is_visible)

        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = test
        some_picture.save()
        self.assertFalse(test.is_visible)

    def test_published_category_without_pictures(self):
        """
        It must not be visible as it does not have pictures
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=True,
                                              slug="test")
        self.assertFalse(test.is_visible)

    def test_published_category_with_pictures(self):
        """
        We create picture category which is_published and is_visible False
        If we add picture to it is_visible must be True
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = test
        some_picture.save()
        self.assertTrue(test.is_visible)

    def test_add_visible_subdirecotry_and_picture_to_master_category(self):
        """
        We have master category and subdirectory to it. Both published.
        If we add picture to the master category:
        - master directory is_visible must be True
        - subdirectory is_visible must be False
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")

        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        is_visible=True,
                                                        parent=test)
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = test
        some_picture.save()
        self.assertTrue(test.is_visible)
        self.assertFalse(inner_category.is_visible)

    def test_change_subdirectory_visibility_must_update_parent(self):
        """
        We have master category and subdirectory to it. Both published. Both with is_visible False
        If we add picture to the subidrectory it and its parent must be is_visible True
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")

        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        is_visible=False,
                                                        parent=test)
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = inner_category
        some_picture.save()
        self.assertTrue(test.is_visible)
        self.assertTrue(inner_category.is_visible)

    def test_recursivity_of_category_is_visible_resolving(self):
        """
        We run part of the upper tests but making sub sub directory..
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")

        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)

        inner_inner_category = PictureCategory.objects.create(title="inner_inner_category",
                                                              is_published=True,
                                                              slug="inner-inner-category",
                                                              parent=inner_category)

        some_picture = Picture.objects.get(pk=1)
        old_category, some_picture.folder = some_picture.folder, inner_inner_category
        some_picture.save()
        self.assertTrue(PictureCategory.objects.get(pk=test.pk).is_visible)
        self.assertTrue(PictureCategory.objects.get(pk=inner_category.pk).is_visible)
        self.assertTrue(PictureCategory.objects.get(pk=inner_inner_category.pk).is_visible)
        some_picture.folder = old_category
        some_picture.save()
        self.assertFalse(PictureCategory.objects.get(pk=test.pk).is_visible)
        self.assertFalse(PictureCategory.objects.get(pk=inner_category.pk).is_visible)
        self.assertFalse(PictureCategory.objects.get(pk=inner_inner_category.pk).is_visible)

    def test_remove_sibling(self):
        """
        If we have master category which is visible because it poses subcategory with pictures,
        removing the subdirectory must edit the is_visible attribute of the master category
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)

        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = inner_category
        some_picture.save()
        self.assertTrue(test.is_visible)
        self.assertTrue(inner_category.is_visible)

        inner_category.delete()
        self.assertFalse(test.is_visible)

    def test_return_category_if_no_cover_pictures_exist(self):
        """
        When category does not poses picture which is_cover we still must return
        one of the pictures it poses as a cover
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        picture_1, picture_2 = Picture.objects.get(pk=1), Picture.objects.get(pk=2)
        picture_1.is_cover = picture_2.is_cover = False
        picture_1.folder = picture_2.folder = test
        picture_1.save()
        picture_2.save()
        self.assertEqual(type(test.get_cover()), type(picture_1))

    def test_picture_as_a_cover_category_cover_must_be_it(self):
        """
        If we have bunch of pictures in a category get_cover method must return
        the one which is set to be cover
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        Picture.objects.update(is_cover=False, folder=test)

        self.assertNotEqual(test.pictures.count(), 0)
        picture = Picture.objects.get(pk=3)
        picture.is_cover = True
        picture.save()
        self.assertEqual(test.get_cover(), picture)

    def test_get_visible_descendants_method_visible_child_instant_parent_unpublished(self):
        """
        We have:

        -A1-
            |
          -A2-
             |
            -X-

        where A1 is published and visible (has pictures in itself)
        where A2 is NOT published.
        X is both published and visible (has pictures in itself)

        A1.get_visible_descendants() must return empty QuerySet as X is not
        visible descendant because its parent is not visible.
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        test_category_pic = Picture.objects.get(pk=1)
        test_category_pic.folder = test
        test_category_pic.save()
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=False,
                                                        slug="inner-category",
                                                        parent=test)
        inner_inner_category = PictureCategory.objects.create(title="inner_inner_category",
                                                              is_published=True,
                                                              slug="inner-inner-category",
                                                              parent=inner_category)
        inner_inner_category_pic = Picture.objects.get(pk=2)
        inner_inner_category_pic.folder = inner_inner_category
        inner_inner_category_pic.save()

        self.assertFalse(inner_category.is_visible)
        self.assertTrue((test.is_visible and inner_inner_category.is_visible))

        self.assertSequenceEqual([test], list(test.get_visible_descendants()))

    def test_get_visible_descendants_method_visible_child_parent_parent_unpublished(self):
        """
        We have:

        -A1-
            |
          -A2-
             |
            -A3-
               |
              -X-

        where A1 is published and visible (has pictures in itself)
        where A2 is NOT published.
        where A3 is published and visible (it has X descendant which has pictures in it)
        where X is both published and visible (has pictures in itself)

        A1.get_visible_descendants() must return (A1) as
        none of A2, A3 and X are visible descendant
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        test_category_pic = Picture.objects.get(pk=1)
        test_category_pic.folder = test
        test_category_pic.save()
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=False,
                                                        slug="inner-category",
                                                        parent=test)
        inner_inner_category = PictureCategory.objects.create(title="inner_inner_category",
                                                              is_published=True,
                                                              slug="inner-inner-category",
                                                              parent=inner_category)
        inner_inner_inner_category = PictureCategory.objects.create(
            title="inner_inner_inner_category",
            is_published=True,
            slug="inner-inner-inner-category",
            parent=inner_inner_category)

        inner_inner_inner_category_pic = Picture.objects.get(pk=2)
        inner_inner_inner_category_pic.folder = inner_inner_inner_category
        inner_inner_inner_category_pic.save()

        self.assertFalse(inner_category.is_visible)
        self.assertTrue((test.is_visible and
                         inner_inner_category.is_visible and
                         inner_inner_inner_category.is_visible))

        self.assertSequenceEqual([test], list(test.get_visible_descendants()))

    def test_get_visible_descendants_whole_descendants_tree(self):
        """
        We have:

        -A1-
            |
          -A2-
             |
            -A3-
               |
              -X-

        where A1 is published and visible (has pictures in itself)
        where A2 is published and visible (has subcategory with picture in it)
        where A3 is published and visible (it has X descendant which has pictures in it)
        where X is both published and visible (has pictures in itself)

        A1.get_visible_descendants() must return A1, A2, A3 and X
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)
        inner_inner_category = PictureCategory.objects.create(title="inner_inner_category",
                                                              is_published=True,
                                                              slug="inner-inner-category",
                                                              parent=inner_category)
        inner_inner_inner_category = PictureCategory.objects.create(
            title="inner_inner_inner_category",
            is_published=True,
            slug="inner-inner-inner-category",
            parent=inner_inner_category)

        inner_inner_inner_category_pic = Picture.objects.get(pk=2)
        inner_inner_inner_category_pic.folder = inner_inner_inner_category
        inner_inner_inner_category_pic.save()

        self.assertTrue((test.is_visible and
                         inner_category.is_visible and
                         inner_inner_category.is_visible and
                         inner_inner_inner_category.is_visible))

        self.assertSequenceEqual([test, inner_category, inner_inner_category,
                                  inner_inner_inner_category],
                                 list(test.get_visible_descendants()))

    def test_get_visible_descendants_returns_the_node_if_is_visible_and_published(self):
        """
        test if get_visible_descendants by default includes self
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")

        self.assertSequenceEqual([], list(test.get_visible_descendants()))
        test_category_pic = Picture.objects.get(pk=1)
        test_category_pic.folder = test
        test_category_pic.save()
        self.assertSequenceEqual([test], list(test.get_visible_descendants()))

    def test_delete_category_if_updates_parent(self):
        """
        If we have category that is visible only because it has
        child with pictures in it.. deleting the child must update
        the parent direcoty and set its visibility to False
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = inner_category
        some_picture.save()
        self.assertTrue(test.is_visible)
        inner_category.delete()
        self.assertFalse(test.is_visible)

    def test_is_shown_method_self_visible_and_all_descendants_visible(self):
        """
        Category is_shown must return True if the category
        is visible and all its parents are visible too
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)
        inner_inner_category = PictureCategory.objects.create(title="inner_inner_category",
                                                              is_published=True,
                                                              slug="inner-inner-category",
                                                              parent=inner_category)
        inner_inner_inner_category = PictureCategory.objects.create(
            title="inner_inner_inner_category",
            is_published=True,
            slug="inner-inner-inner-category",
            parent=inner_inner_category)
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = inner_inner_inner_category
        some_picture.save()
        self.assertTrue(all(x.is_shown() for x in [test,
                                                   inner_category,
                                                   inner_inner_category,
                                                   inner_inner_inner_category]))

    def test_is_shown_method_self_visible_but_some_parent_is_not_visible(self):
        """
        Category is_shown must return False if not all parents are visible
        """
        """
        Category is_shown must return True if the category
        is visible and all its parents are visible too
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)
        inner_inner_category = PictureCategory.objects.create(title="inner_inner_category",
                                                              is_published=True,
                                                              slug="inner-inner-category",
                                                              parent=inner_category)
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = inner_inner_category
        some_picture.save()
        inner_category.is_published = False
        inner_category.save()
        self.assertTrue(inner_inner_category.is_visible)
        self.assertFalse(inner_inner_category.is_shown())

    def test_is_shown_method_if_self_is_not_visible(self):
        """
        Category is_shown method must return False if category is not visible
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              slug="test")
        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        parent=test)

        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = test
        some_picture.save()
        self.assertFalse(inner_category.is_visible)
        self.assertFalse(inner_category.is_shown())


class CMSPluginMediaCenterPictureTests(TestCase):

    fixtures = ['auth_fixtures', 'filer_fixtures', 'media_center_fixtures']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add_picture_to_unpublished_subdirectory(self):
        """
        We have directory and subdirectory, with unpublished subirectory.
        Adding pictures to the subdirectory must not change master directory is_visible attribute
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")

        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=False,
                                                        slug="inner-category",
                                                        is_visible=True,
                                                        parent=test)
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = inner_category
        some_picture.save()
        self.assertFalse(test.is_visible)
        self.assertFalse(inner_category.is_visible)

    def test_change_picture_category(self):
        """
        We have category which is_visible True thanks to a picture it poses and
        we move this picture to point to different category.
        Our initial picture category in the db must be updated (become is_visible False)
        Our newly attached cateogory to the picture must be changed also (become is_visible True)
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")

        other_category = PictureCategory.objects.create(title="other_test",
                                                        is_published=True,
                                                        is_visible=False,
                                                        slug="other-test")
        some_picture = Picture.objects.get(pk=1)
        some_picture.folder = test
        some_picture.save()

        self.assertFalse(PictureCategory.objects.get(pk=other_category.pk).is_visible)
        self.assertTrue(PictureCategory.objects.get(pk=test.pk).is_visible)
        some_picture.folder = other_category
        some_picture.save()
        self.assertFalse(PictureCategory.objects.get(pk=test.pk).is_visible)
        self.assertTrue(PictureCategory.objects.get(pk=other_category.pk).is_visible)

    def test_change_subdirectory_category_picture(self):
        """
        We have inner category with picture which causes parent directory to be is_visible True
        because it has picture in it.

        If we change the picture category, both subdirectory and parent directory must be
        is_visible True
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")

        inner_category = PictureCategory.objects.create(title="inner_category",
                                                        is_published=True,
                                                        slug="inner-category",
                                                        is_visible=True,
                                                        parent=test)
        some_picture = Picture.objects.get(pk=1)
        old_category, some_picture.folder = some_picture.folder, inner_category
        some_picture.save()
        self.assertTrue(PictureCategory.objects.get(pk=test.pk).is_visible)
        self.assertTrue(PictureCategory.objects.get(pk=inner_category.pk).is_visible)
        some_picture.folder = old_category
        some_picture.save()
        self.assertFalse(PictureCategory.objects.get(pk=test.pk).is_visible)
        self.assertFalse(PictureCategory.objects.get(pk=inner_category.pk).is_visible)

    def test_save_brand_new_picture_in_category_must_update_category(self):
        """
        We have category that does not have pictuers in it. It is_visible is False.
        We create brand new picture and attach it to this category. Category must become visible
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")
        self.assertFalse(test.is_visible)
        from filer.models import Image
        some_image = Image.objects.create()
        new_picture = Picture.objects.create(folder=test, image=some_image)
        new_picture.save()
        self.assertTrue(test.is_visible)

    def test_delete_picture_must_update_folder_adequately(self):
        """
        If we delete picture its folder must be resaved to adjust is_visible adequately
        """
        test = PictureCategory.objects.create(title="test",
                                              is_published=True,
                                              is_visible=False,
                                              slug="test")
        from filer.models import Image
        some_image = Image.objects.create()
        new_picture = Picture.objects.create(folder=test, image=some_image)
        new_picture.save()
        self.assertTrue(test.is_visible)
        new_picture.delete()
        self.assertFalse(test.is_visible)


class CMSPluginMediaCenterManagerTests(TestCase):

    fixtures = ['auth_fixtures', 'filer_fixtures']

    def setUp(self):
        """
        root_1
              \
               inner_root_1
                            \
                            inner_inner_root_1

        root_2
              \
               inner_root_2
                           \
                            inner_inner_root_2

        root_3
        """

        self.root_1 = PictureCategory.objects.create(title="root_1",
                                                     is_published=True,
                                                     slug="root-1")
        self.inner_root_1 = PictureCategory.objects.create(title="inner_root_1",
                                                           is_published=True,
                                                           slug="inner-root-1",
                                                           parent=self.root_1)
        self.inner_inner_root_1 = PictureCategory.objects.create(title="inner_inner_root_1",
                                                                 is_published=True,
                                                                 slug="inner-inner-root-1",
                                                                 parent=self.inner_root_1)
        self.root_2 = PictureCategory.objects.create(title="root_2",
                                                     is_published=True,
                                                     slug="root-2")
        self.inner_root_2 = PictureCategory.objects.create(title="inner_root_2",
                                                           is_published=True,
                                                           slug="inner-root-2",
                                                           parent=self.root_2)
        self.inner_inner_root_2 = PictureCategory.objects.create(title="inner_inner_root_2",
                                                                 is_published=True,
                                                                 slug="inner-inner-root-2",
                                                                 parent=self.inner_root_2)
        self.root_3 = PictureCategory.objects.create(title="root_3",
                                                     is_published=True,
                                                     slug="root-3")

        self.all_categories = [
            self.root_1,
            self.inner_root_1,
            self.inner_inner_root_1,
            self.root_2,
            self.inner_root_2,
            self.inner_inner_root_2,
            self.root_3
        ]

    def add_picture_to_every_category(self):
        from filer.models import Image
        some_image = Image.objects.create()
        for category in self.all_categories:
            Picture.objects.create(folder=category, image=some_image)

    def clear_pictures_from_every_category(self):
        fake_category = PictureCategory.objects.create(title="fake",
                                                       is_published=True,
                                                       slug="fake")
        for category in self.all_categories:
            category.pictures.update(folder=fake_category)

        for picture in Picture.objects.all():
            picture.save()
        fake_category.delete()

    def tearDown(self):
        pass
        self.clear_pictures_from_every_category()

    def test_whole_tree_to_not_raise_exception_if_no_visible_category_exists(self):
        self.assertSequenceEqual([], PictureCategory.objects.whole_tree())

    def test_if_whole_tree_is_displaying_correctly(self):
        self.add_picture_to_every_category()
        self.assertSequenceEqual(self.all_categories, PictureCategory.objects.whole_tree())

    def test_show_subtree_shows_whole_tree_if_no_args_provided(self):
        self.add_picture_to_every_category()
        self.assertSequenceEqual(self.all_categories,
                                 PictureCategory.objects.show_subtree())

    def test_show_subtree_with_from_node_arg(self):
        self.add_picture_to_every_category()
        self.assertSequenceEqual([self.root_1,
                                  self.inner_root_1,
                                  self.inner_inner_root_1],
                                 PictureCategory.objects.show_subtree(from_node=self.root_1))

    def test_show_subtree_with_depth_arg_0(self):
        self.add_picture_to_every_category()
        self.assertSequenceEqual([self.root_1,
                                  self.root_2,
                                  self.root_3],
                                 PictureCategory.objects.show_subtree(depth=0))

    def test_show_subtree_with_depth_arg_provided(self):
        self.add_picture_to_every_category()
        self.assertSequenceEqual([self.root_1,
                                  self.inner_root_1,
                                  self.root_2,
                                  self.inner_root_2,
                                  self.root_3],
                                 PictureCategory.objects.show_subtree(depth=1))

    def test_show_subtree_with_depth_arg_and_include_self_provided(self):
        self.add_picture_to_every_category()
        self.assertSequenceEqual([self.inner_root_1, self.inner_root_2],
                                 PictureCategory.objects.show_subtree(include_self=False, depth=1))

    def test_get_visible(self):
        self.add_picture_to_every_category()
        self.assertEqual(self.root_1, PictureCategory.objects.get_visible(slug="root-1"))

    def test_get_visible_when_category_not_shown_must_raise_doesnotexist(self):
        from filer.models import Image
        some_image = Image.objects.create()
        picture = Picture.objects.create(folder=self.inner_root_1, image=some_image)
        picture.save()
        self.root_1.is_published = False
        self.root_1.save()

        with self.assertRaises(PictureCategory.DoesNotExist):
            PictureCategory.objects.get_visible(slug=self.inner_root_1.slug)
