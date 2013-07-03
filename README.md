# Entu

_Futuristic Data Management System_


## Key features

* It stores data in Entities (objects) and Entities have (text, numeric, date, file, …) properties
* Entities are fully customizable
    * what properties to show as name, description, etc
    * what properties to show in relation table
    * what properties to use for search and sort
    * allowed child Entities
    * what kind of custom actions it supports
    * ...
* Properties are fully customizable
    * label
    * description
    * data type
    * multiplicity
    * visibility in public search
    * ...
* In addition to stored properties, there are calculated properties to calculate/show Entity's (or related Entity's) properties
* Property can store one or multiple values
* Entities can be related with each other by system relations (child, seeder, leecher) or by custom ones
* User authentication is delegated to Google, Facebook, Twitter, MS Live or other providers
* Users have explicit rights (viewer, editor, owner) for every Entity - there are no roles


## Screenshot

![Screenshot](https://raw.github.com/argoroots/Entu/2013-07-01/static/images/screenshot.png "Screenshot")


## Dependencies

* [MySQL](http://www.mysql.com/)
* [Python](http://www.python.org/)
    * [Tornado](http://www.tornadoweb.org)
    * [python-mysqldb](http://mysql-python.sourceforge.net)
    * [python-magic](https://github.com/ahupp/python-magic)
    * [python-suds](https://fedorahosted.org/suds/)
    * [python-markdown2](https://github.com/trentm/python-markdown2)
    * [tornadomail](https://github.com/equeny/tornadomail)
    * [torndb](https://github.com/bdarnell/torndb)
    * [xmltodict](https://github.com/martinblech/xmltodict)
    * [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup)
    * [PyYAML](http://pyyaml.org)


## Used libraries/add-ons

* [Bootstrap](http://twitter.github.com/bootstrap/) + [Font Awesome More](http://gregoryloucas.github.com/Font-Awesome-More/)
* [jQuery](http://jquery.com/) + [jQuery UI](http://jqueryui.com/)
* [Elastic](http://unwrongest.com/projects/elastic/)
* [Datejs](http://www.datejs.com/)
* [Bootstrap File Input](https://github.com/grevory/bootstrap-file-input)
* [Select2](http://ivaynberg.github.com/select2)
