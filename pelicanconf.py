#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
import os

AUTHOR = 'dokelung' # theme

SITENAME = 'dokelung.me' # theme
SITEURL = 'http://dokelung.me' # theme

TIMEZONE = 'Asia/Taipei'

DEFAULT_LANG = 'zh'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

DIRECT_TEMPLATES = ('index', 'categories', 'tags', 'archives', 'search')

# path settings =============================================================
PATH = 'content'

PLUGIN_PATHS = ['../pelican-plugins']

PLUGINS = ['tipue_search', 'just_table', "representative_image"]

STATIC_PATHS = ['images', 'articles']

ARTICLE_PATHS = ['articles']
ARTICLE_URL = 'category/{category}/{slug}/'
ARTICLE_SAVE_AS = 'category/{category}/{slug}/index.html'

PAGE_URL = 'pages/{slug}/'
PAGE_SAVE_AS = 'pages/{slug}/index.html'

THEME = '../jojo'

# jojo theme settings =======================================================

"""
put all photos under content/images and just specify the base name of it in
following settings
"""

# site settings
SHORTCUT_ICON = 'dokelung.jpg'

# right side panels
SOCIAL = {
    'style': {
        'size': 'medium', # small, medium, large
        'hover': True,    # True, False
        'button': False,  # True, False
    },
    # for SOCIAL, jojo supports uk-icon in uikit2
    # but jojo only recover following icons' color
    'icons': (
        ('envelope-square', 'dokelung@gmail.com'),
        # ('facebook-square', '#'),
        ('github-square', 'https://github.com/dokelung'),
        # ('google-plus-square', '#'),
        ('linkedin-square', 'https://www.linkedin.com/in/ko-lung-yuan-536b9aa3/'),
        # ('skype', '#'),
        # ('twitter-square', '#'),
        # ('weixin', '#'),
    )
}
AUTHOR_INFO = {
    'id': AUTHOR,
    'photo': 'dokelung.jpg',
    'intro_keywords': (
        ('a book author', 'https://github.com/its-django/mysite/wiki'),
        ('a pythoner', 'https://github.com/dokelung'),
    ),
    'intro': [
        'Hi, my name is Ko-Lung Yuan!',
        '你好，我是袁克倫，你可以叫我 dokelung，我是一名小小軟體工程師，專長是電子設計自動化。 愛學習也愛分享，寫書來推廣熱愛的知識一直是他的夢想。 本應與 C++ 共度一生，卻意外成為 Python 的終極狂熱者，幾乎生活上的大小事都想用 Python 解決(可惜吃飯和上廁所不行)，酷愛有關於 Python 的一切。'
    ],
    'url': os.path.join(SITEURL, 'pages', 'about-me'),
    'social': SOCIAL,
}

NEWEST_ARTICLES = 10 # set 0 to hide this panel

SIMPLE_PANELS = (
    {
        'badge': {
            'string': 'book',
            # type can be specified as '' or 'success' or 'warning' or 'danger'
            # by default, '' is blue, 'success' is green, 'warning' is orange and 'danger' is red
            # please reference to uikit2
            'type': 'danger',
        },
        'title': "It's django",
        'photo': 'its_django.jpg',
        'content': 'A book about python web framework Django',
        'link': ('Where to buy it?', '#'),
    },
    {
        'badge': {
            'string': 'book',
            'type': 'danger',
        },
        'title': "dokelung - Python 快速入門",
        'link': ('Read it!', 'https://www.gitbook.com/book/dokelung/dokelung-python-quickstart/details'),
    },
)

RELATED_LINKS = (
    ('Pelican', 'http://getpelican.com/'),
    ('Python.org', 'http://python.org/'),
    ('Jinja2', 'http://jinja.pocoo.org/'),
    ('mg', 'https://github.com/lucachr/pelican-mg'),
)

# left side buttons
SHARE_BUTTONS = True
CONTROL_BUTTONS = True

# top
NAV = {
    'sitename': SITENAME,
    'navitems': (
        {
            'primary': ('About me', AUTHOR_INFO['url']),
        },
        {
            'primary': ('Category', os.path.join(SITEURL, 'categories.html')),
            'secondary': (
                {'type':'header', 'name':'Programming'},
                {'link':('python', os.path.join(SITEURL, 'category', 'python.html')) },
                {'type':'divider'},
                {'link':('pelican', os.path.join(SITEURL, 'category', 'pelican.html')) },
                # {'link':('misc', os.path.join(SITEURL, 'category', 'misc.html'))},
            )
        },
        {
            'primary': ('Archives', os.path.join(SITEURL, 'archives.html')),
        },
    ),
    'tipue_search': True,
}

LOCATION = True

# footer
FOOTER = {
    'year': 2017,
    'author': AUTHOR,
    'license': {
        'name': 'The MIT License',
        'link': 'https://opensource.org/licenses/MIT',
    }
}

# just table settings
JTABLE_TEMPLATE = """
<table class="uk-table uk-table-striped">
    {% if caption %}
    <caption> {{ caption }} </caption>
    {% endif %}
    {% if th != 0 %}
    <thead>
    <tr>
        {% if ai == 1 %}
        <th> No. </th>
        {% endif %}
        {% for head in heads %}
        <th>{{ head }}</th>
        {% endfor %}
    </tr>
    </thead>
    {% endif %}
    <tbody>
        {% for body in bodies %}
        <tr>
            {% if ai == 1 %}
            <td> {{ loop.index }} </td>
            {% endif %}
            {% for entry in body %}
            <td>{{ entry }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </tbody>
</table>
"""

DISQUS_SITENAME = "dokelung-me"
DISQUS_CONFIG = True
