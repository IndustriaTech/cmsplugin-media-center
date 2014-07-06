# cmsplugin-media-center

[![Build Status](https://travis-ci.org/MagicSolutions/cmsplugin-media-center.svg?branch=master)](https://travis-ci.org/MagicSolutions/cmsplugin-media-center)
[![Coverage Status](https://coveralls.io/repos/MagicSolutions/cmsplugin-media-center/badge.png?branch=master)](https://coveralls.io/r/MagicSolutions/cmsplugin-media-center?branch=master)


This app needs:
- [django-cms](https://github.com/divio/django-cms) (obviously)
- [cmsplugin-filer](https://github.com/stefanfoulis/cmsplugin-filer)
- [django-orderedmodel](https://github.com/MagicSolutions/django-orderedmodel)

They will be automatically installed so no worries.


## SetUp

    pip install git+git://github.com/MagicSolutions/cmsplugin-media-center.git --process-dependency-links

--process-dependency-links is added because of the django-orderedmodel package (it is good to be the one from the MagicSolution's organization)

You should have these in installed apps:

    INSTALLED_APPS = (
        .....
        'easy_thumbnails',
        .....
        'filer',
        'cmsplugin_filer_file',
        'cmsplugin_filer_folder',
        'cmsplugin_filer_image',
        'cmsplugin_filer_teaser',
        .....
        'orderedmodel',
        'cmsplugin_media_center',
    )

And these in THUMBNAIL_PROCESSORS:

    THUMBNAIL_PROCESSORS = (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    )

Run the migrations:

    python manage.py migrate filer
    python manage.py migrate cmsplugin_carousel

Andd off you go.

## Demo
