import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='cmsplugin-media-center',
    url='https://github.com/MagicSolutions/cmsplugin-media-center',
    version='0.0.1',
    description='Django CMS plugin/app for creating galeries.',
    long_description=README,
    install_requires=[
        'django-cms>=2.4.3',
        'cmsplugin-filer>=0.9.5',
        'django-orderedmodel>=0.1.5',
    ],
    dependency_links=[
        'git+https://github.com/MagicSolutions/django-orderedmodel.git@0.1.5#egg=django-orderedmodel-0.1.5',
    ],
    packages=find_packages(),
    package_data={'': ['LICENSE']},
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
