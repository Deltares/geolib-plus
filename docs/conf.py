# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(".."))  # isort:skip
import geolib_plus  # isort:skip

# -- Project information -----------------------------------------------------

project = "geolib+"
copyright = "2020, Deltares"
author = "Deltares"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "rst2pdf.pdfbuilder",
    "sphinxcontrib.bibtex",
    "sphinx.ext.imgmath",
    "releases",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "alabaster"
html_style = "custom.css"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Added
# The short X.Y version.
version = geolib_plus.__version__
# The full version, including alpha/beta/rc tags.
release = geolib_plus.__version__

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

html_theme_options = {
    "logo_name": False,
    "logo": "geolib.png",
    "show_powered_by": False,
    "show_related": False,
    "note_bg": "#FFF59C",
    "extra_nav_links": {
        "@Source code": "https://bitbucket.org/DeltaresGEO/geolib-plus/src",
        "@Issue Tracker": "https://issuetracker.deltares.nl/secure/RapidBoard.jspa?projectKey=GEOLIB",
        "@Project documentation": "https://publicwiki.deltares.nl/display/GEOLIB/GEOLIB+Home",
        "@Releases": "https://publicwiki.deltares.nl/display/GEOLIB/GEOLib+releases",
    },
    "show_related": False,
    "show_relbars": True,
}

# Custom sidebar templates, maps document names to template names.
html_sidebars: {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "donate.html",
    ]
}

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# Display todos
todo_include_todos = True

# Releases config
releases_release_uri = "https://publicwiki.deltares.nl/download/attachments/166462065/geolib_plus-%s-py3-none-any.whl?api=v2"
releases_issue_uri = "https://issuetracker.deltares.nl/browse/%s"
releases_unstable_prehistory = True

# Bibliography
bibtex_bibfiles = "bibliography.bib"
