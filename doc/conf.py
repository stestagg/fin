# -*- coding: utf-8 -*-

import sys, os

ROOT = os.path.abspath("..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, 'doc', '_themes'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']

templates_path = ['.templates']

source_suffix = '.rst'

master_doc = 'index'

# General information about the project.
project = u'fin'
copyright = u'Offset design consulting ltd'

import fin
version = fin.VERSION
# The full version, including alpha/beta/rc tags.
release = fin.VERSION

exclude_patterns = []

html_theme_path = ['_themes']
html_theme = 'flask'

html_static_path = ['.static']

htmlhelp_basename = 'findoc'


latex_elements = {}

latex_documents = [
  ('index', 'fin.tex', u'fin Documentation',
   u'Steve Stagg', 'manual'),
]

man_pages = [
    ('index', 'fin', u'fin Documentation',
     [u'Steve Stagg'], 1)
]

texinfo_documents = [
  ('index', 'fin', u'fin Documentation',
   u'Steve Stagg', 'fin', 'One line description of project.',
   'Miscellaneous'),
]
