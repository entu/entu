# Entu API 2.0
All request will return JSON dictionary.

Authentication is possible in two ways:

* **user**, **policy** and **signature** GET/POST/PUT/DELETE arguments.
* **X-Auth-UserId** and **X-Auth-Token** header parameters.



## /api2/entity

### GET - get entity list
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
definition|string|No||Entity definition keyname
query|string|No||Search string
limit|integer|No||How many entities to return
page|integer|No|1|
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
200|OK|Returns entity list



## /api2/entity-{id}

### GET - get entity (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
200|OK|Returns entity
404|Not Found|Entity with given ID is not found

### PUT - change entity (with given ID) properties
Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
*1st_property_definition*||Yes||
*2nd_property_definition*||No||
*..._property_definition*||No||
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy

Result code|Status|Description
:-:|:--|:--
200|OK|Property is changed
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or change this entity or property
404|Not Found|Entity (or property) with given ID is not found

### POST - create new child entity (under entity with given ID)
Sorry, but this description is a mess - blame Argo.  

Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
definition|string|Yes||Definition ID of the new entity
*1st_property_definition*||No||
*2nd_property_definition*||No||
*..._property_definition*||No||
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
201|Created|Returns new entity ID
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or change this entity
404|Not Found|Entity with given ID is not found

### DELETE - delete entity (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
200|OK|Entity is deleted
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or delete this entity
404|Not Found|Entity with given ID is not found



## /api2/file

### POST - upload/create file
**Note:** Since the entire POST body will be treated as the file, any parameters must be passed as part of the request URL.  
**Note 2:** Providing a Content-Length header set to the size of the uploaded file is required so that the server can verify that it has received the entire file contents.  
**Note 3** Multipart/form-data is now also supported.

Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
entity|integer|Yes||ID of the entity where to but this file
property|string|Yes||Property definition of the new file property
filename|string|Yes||File name
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
201|Created|Returns new file ID
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or change this entity
404|Not Found|Entity with given ID is not found



## /api2/file/s3

### POST - get Amazon S3 upload url and formdata

Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
entity|integer|Yes||ID of the entity where to but this file
property|string|Yes||Property definition of the new file property
filename|string|Yes||File name
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
201|Created|Returns new file ID
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or change this entity
404|Not Found|Entity with given ID is not found



## /api2/file/url

### POST - Upload file from url

Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
entity|integer|Yes||ID of the entity where to but this file
property|string|Yes||Property definition of the new file property
url|string|Yes||Url where to get file
download|true/false|No||If true downloads file to Entu, otherwise creates just link
filename|string|No||File name. If not set uses file name from url
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
201|Created|Returns new file ID
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or change this entity
404|Not Found|Entity with given ID is not found



## /api2/file-{id}

### GET - get file (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
200|OK|Returns file
302|Redirect|Redirects to external file (Amazon S3, Google Drive, etc)
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access this file
404|Not Found|File with given ID is not found

### DELETE - delete file (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Result code|Status|Description
:-:|:--|:--
200|OK|File is deleted
400|Bad Request|Returns error message
403|Forbidden|User has no rights to access or delete this file or entity
404|Not Found|Entity with given ID is not found
