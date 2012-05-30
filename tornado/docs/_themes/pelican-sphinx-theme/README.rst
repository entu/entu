Pelican sphinx theme
####################

This is the sphinx theme used on http://docs.notmyidea.org/alexis/pelican/.
It have been originally developed for pelican but you can use it for your own
projects by changing your sphinx settings file.

The theme is proposed under a simple BSD licence (see LICENSE)

How to use this theme ?
=======================

To use this sphinx theme you have to:

* Download it and put it in a folder available to your sphinx documentation.
  Say `_themes`
* Update the configuration to use it::

    sys.path.append(os.path.abspath('_themes'))
    html_theme_path = ['_themes']
    html_theme = 'pelican-sphinx-theme'

That's should be it
