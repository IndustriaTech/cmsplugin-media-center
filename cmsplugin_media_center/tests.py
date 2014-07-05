from django.test import TestCase

from cmsplugin_media_center.models import PictureCategory, Picture


class CMSPluginMediaCenterTests(TestCase):

    fixtures = ['auth_fixtures', 'filer_fixtures', 'media_center_fixtures']

    def setUp(self):
        self.published_parent_without_pictures = PictureCategory.objects.get(pk=11)
        self.published_parent_with_pictures = PictureCategory.objects.get(pk=3)
        self.not_published_parent_with_published_children = PictureCategory.objects.get(pk=12)

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

    def test_visibility_published_parent_unpublished_children(self):
        """
        Check visibility of published and unpublished folders with or without children and/or images.
        """
        is_visible = self.published_parent_without_pictures.check_visibility()
        self.assertEqual(is_visible, False)

        is_visible = self.published_parent_with_pictures.check_visibility()
        self.assertEqual(is_visible, True)

        is_visible = self.not_published_parent_with_published_children.check_visibility()
        self.assertEqual(is_visible, False)

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


class CMSPluginMediaCenterManagerTests(TestCase):

    fixtures = ['auth_fixtures', 'filer_fixtures']

    def setUp(self):
        pass

    def tearDown(self):
        pass


class CMSPluginMediaCenterPluginTests(TestCase):

    fixtures = ['auth_fixtures', 'filer_fixtures']

    def setUp(self):
        pass

    def tearDown(self):
        pass
