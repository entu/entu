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
    * data type ('boolean','decimal','date','datetime','file','integer','reference','string','text','secret')
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

[See INSTALL.md](INSTALL.md)


## License

Entu is open source and available under the [MIT license](LICENSE.md).
