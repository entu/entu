# Entu - Futuristic Data Management System

![Screenshot](https://raw.github.com/argoroots/Entu/2013-07-01/static/images/screenshot.png "Screenshot")

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
    * data type ('boolean','decimal','date','datetime','file','integer','reference','string','text')
    * multiplicity
    * visibility in public search
    * ...
* In addition to stored properties, there are calculated properties to calculate/show Entity's (or related Entity's) properties
* Property can store one or multiple values
* Entities can be related with each other by system relations (child, seeder, leecher) or by custom ones
* User authentication is delegated to Google, Facebook, Twitter, MS Live or other providers
* Users have explicit rights (viewer, editor, owner) for every Entity - there are no roles


### LICENSE
The MIT License (MIT)

Copyright (c) 2013 Argo Roots and Mihkel Putrinš

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
