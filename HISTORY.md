## 2015-10-28
* Started to move everything to MongoDB
    * Authentication is now separate service
    * Requestlog
* Added [TAAT](http://taat.edu.ee) authentication
* Link to referenced entity in public view
* Support for MailGun tags
* Errors are logged to [Sentry](https://getsentry.com)

## 2015-09-15
* Entu is [dockerized](https://www.docker.com) now
* 79 commits full of fixes and small enhancements

## 2015-05-05
* Show item thumbnail in childs/relations table
* Small fixes and enhancements

## 2015-04-15
* Only object owner can delete entity
* Option to set custom text to public start page
* Show all Entity photos in public view
* Show object metainfo on image hover
* Lots of bugfixes

## 2015-03-25
* Erply API integration
* API2 authentication for standalone (web)apps
* Public search results redesign

## 2015-02-20
* Option to store files in Amazon S3
* Authenticate user by "X-Auth-UserId" and "X-Auth-Token" header
* User method on API2
* Lots of bugfixes

## 2015-01-07
* Fixed children/relations table sorting on Entity view
* Other small fixes

## 2014-12-03
* Return MD5 with file property (API2 Entity get)
* Rights can be assigned to any Entity with entu-user or entu-api-key
* Store image thumbnails on disk (and not in DB)
* Show current user authentication provider in preferences

## 2014-11-21
* Store uploaded files on disk (and not in DB)

## 2014-11-15
* Added publink to entity view
* Table-view limit is now configurable
* Mltipart/form-data file upload on API2
* Small fixes

## 2014-10-27
* Entity delete API2 method
* Maximum file size increased from 100MB to 1GB

## 2014-10-23
* API2 enhancements:
  * Entity rights management
  * Custom e-mail sending
* Markdown table support in text fields

## 2014-09-29
* CMDI-XML object importer
* Removed ScreenWerk player from Entu (to separate project)
* Bugfixes

## 2014-05-26
* Allow reimport existing library items from Ester
* Send emails thru mailgun.com
* Make, store and serve image thumbnails and not full images
* Handle JSON encoded body data on POST and PUT methods

## 2014-05-09
* Share Entities with URL

## 2014-04-30
* Reorganized and deleted obsolete JS and CSS libraries
* Small fixes

## 2014-04-29
* Smartphone optimised version to view Entities
* No bugfixes

## 2014-04-22
* API2 enhancements:
  * authentication with user, policy and signature
  * create and show Entity
  * upload and get file
  * updated [documentation](https://github.com/argoroots/Entu/blob/develop/API.md)
* Bugfixes as usual

## 2014-04-07
* Authenticate all users via www.entu.ee
* Background maintenance for sorting, formulas etc
* Some bugs got fixed

## 2014-03-18
* Get public Entities from API 2.0
* Digital signage (ScreenWerk) player enhancements:
  * background update with preset interval
  * play flash media
  * set layout in pixels
  * restart player at midnight
* New ESTER importer
* Bugfixes

## 2014-01-26
* Show all Entities (not just first 500) in search result
* API 2.0 first methods
* Major speed boost as we are moving to API 2.0
* Lots and lots and lots of bugfixes and enhancements

## 2013-11-08
* Show entity search results as table
* Sorting for entity childs table
* Option to set entity displaytable headers
* Duplicate Entities
* Lots of formula field enhancements
* Highlight mandatory fields and not completed entities
* Edit form improvements
* Bugfixes

## 2013-10-09
* Bugfixes

## 2013-09-23
* Ester search/import uses now Z39.50 protocol
* Ester search shows coverart (if found)
* Other small fixes and enhancements

## 2013-09-05
* Upload files by URL
* Small fixes

## 2013-09-04
* Add and delete Entity parents (relations only)
* CSV importer now autodetects file encoding and separator
* Other CSV importer fixes

## 2013-08-23
* Automatically fetch and save books, workbooks, etc images
* Bugfixes

## 2013-08-01
* Digital signage player enhancements
* Link files directly from Google Drive and Google+ photos
* Lots of file upload bugs fixed (now works with IE, FF and Opera)

## 2013-07-01
* Digital signage (ScreenWerk) player
* Configuration entities (prototype)
* Moved entity and property definitions translation to separate table
* All property types are now searchable
* Bugfixes

## 2013-05-01
* Show and allow edit Entities based on sharing and rights settings
* Additional right (to viewer, editor, owner) is right to add child Entities
* Bugfixes

## 2013-04-29
* View and set Entity sharing and rights
* Save all request info to app_requests table
* New 404 page

## 2013-03-22
* Host based database selection - one process can serve multiple hosts/databases
* Reference propery values are now links to referred entity
* Application code reorganized to subfolders/-apps
* Bugfixes

## 2013-02-18
* Estonian MobileID authentication
* Set menu auto hiding from user preferences
* Bugfixes

## 2013-02-12
* Search and import from ESTER by URL
* Minor design changes - hide menu, fullscreen view
* Edit user preferences
* Bugfixes

## 2013-02-06
* Search improvements
* Removed hardcoded 'Created' field from Entity childs table
* Show quota on start page

## 2013-01-21
* New login page
* Show Entities where Entity is set in reference property
* Bugfixes

## 2013-01-17
* [Public API](https://github.com/argoroots/Entu/wiki/API)
* Reference property
* Formula property
* Upload files directly from [Dropbox](https://www.dropbox.com)
* Design improvements
* Bugfixes

## 2012-12-10
* Download all files (from file property)
* Replace entity #id hash with /id url
* Show reference property values

## 2012-11-22
* Bugfixes

## 2012-11-09
* Multiple file upload

## 2012-11-08
* Mark Entities as deleted
* Bugfixes

## 2012-10-30
* Mark files (from file properties) as deleted

## 2012-10-17
* Changelog - All property changes are logged
* Option to open entiy after add (or stay on parent entity)
* Option to show add button in Entity list view (if default parent is set)

## 2012-10-08
* Bugfixes

## 2012-09-28
* Sorting

## 2012-09-25
* CSV import action
* New /status page to show app status
* Replaced ID fields with KEYNAMEs in definition tables
* Code cleanup and other fixes

## 2012-08-28
* JavaScript property changed to HTML property
* Text properties can use [markdown](http://daringfireball.net/projects/markdown/) formatting

## 2012-08-23
* JavaScript property
* [Ester](http://www.elnet.ee/ester/) import action

## 2012-07-12
* Use HTTPS
* Show organisation name in header

## 2012-07-10
* Select previous/next entity with up/down arrow keys

## 2012-07-09
* Advanced public searc
* Share entity by email

## 2012-06-29
* Show context for entities
* Public fields are differently colored
