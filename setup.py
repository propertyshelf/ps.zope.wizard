# -*- coding: utf-8 -*-
"""Setup for ps.zope.wizard package."""

from setuptools import (
    find_packages,
    setup,
)

version = '0.1.dev0'
description = 'A z3c.form based wizard for Zope.'
long_description = ('\n'.join([
    open('README.rst').read(),
    'Contributors',
    '------------\n',
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
]))

install_requires = [
    'setuptools',
    # -*- Extra requirements: -*-
    'z3c.form',
    'zope.session',
]

setup(
    name='ps.zope.wizard',
    version=version,
    description=description,
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Zope3",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Zope",
    ],
    keywords='zope zope3 wizard z3c.form',
    author='Propertyshelf, Inc.',
    author_email='development@propertyshelf.com',
    url='https://github.com/propertyshelf/ps.zope.wizard',
    download_url='http://pypi.python.org/pypi/ps.zope.wizard',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['ps', 'ps.zope'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'unittest2',
            'z3c.form [test]',
            'zc.buildout',
            'zope.browserpage',
            'zope.publisher',
            'zope.testing',
            'zope.traversing',
        ],
    ),
    install_requires=install_requires,
    entry_points="""
    # -*- Entry points: -*-
    """,
)
