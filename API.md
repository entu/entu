# Entu API 2.0
All request will return JSON dictionary.

Authentication is possible in two ways:

* **user**, **policy** and **signature** GET/POST/PUT/DELETE arguments.
* **X-Auth-UserId** and **X-Auth-Token** header parameters.



## /api2/user

#### GET - get current user info
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)



## /api2/user/auth

#### POST - 1st step for user authentication
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
state|string|Yes||Random string for communication verification
redirect_url|string|No||URL where user is redirected after successful login 

Returns **state** and **auth_url** (/api2/user/auth/{token}). Check that **state** is what you sent and redirect user to **auth_url**. After successful login user is redirected back to url you sent in **redirect_url** argument. If **redirect_url** is not sent returns user object (in JSON)



## /api2/user/auth/{token}

#### GET - login screen
After successful login user is redirected back to url you sent in **redirect_url** argument. If **redirect_url** is not sent returns user object (in JSON).

#### POST - 2nd step for user authentication
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
state|string|Yes||Random string for communication verification. Must be same as used in 1st step (/api2/user/auth post request).

Returns user object. Use result.user.id as X-Auth-UserId and result.user.session_key as X-Auth-Token header parameter in future requests as this user.



## /api2/entity

#### GET - get entity list
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
definition|string|No||Entity definition keyname
query|string|No||Search string
limit|integer|No||How many entities to return
page|integer|No|1|
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)



## /api2/entity-{id}

#### GET - get entity (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

#### PUT - change entity (with given ID) properties
Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
*1st_property_definition*||Yes||
*2nd_property_definition*||No||
*..._property_definition*||No||
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy

#### POST - create new child entity (under entity with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
definition|string|Yes||Definition ID of the new entity
*1st_property_definition*||No||
*2nd_property_definition*||No||
*..._property_definition*||No||
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

#### DELETE - delete entity (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)



## /api2/file

#### POST - upload/create file
**NB!** If customer is configured to store files in Amazon S3 you must use **/api2/file/s3**!

Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
entity|integer|Yes||ID of the entity where to but this file
property|string|Yes||Property definition of the new file property
filename|string|Yes||File name
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

**Note:** Since the entire POST body will be treated as the file, any parameters must be passed as part of the request URL.  
**Note 2:** Providing a Content-Length header set to the size of the uploaded file is required so that the server can verify that it has received the entire file contents.  
**Note 3** Multipart/form-data is now also supported.



## /api2/file/s3

#### POST - get Amazon S3 upload url and formdata
Argument|Type|Required|Default|Description
:--|:-:|:-:|:--|:--
entity|integer|Yes||ID of the entity where to but this file
property|string|Yes||Property definition of the new file property
filename|string|Yes||File name
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

Append file to returned formdata (result.s3.data) and post all to S3 url (result.s3.url)



## /api2/file/url

#### POST - Upload file from url
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



## /api2/file-{id}

#### GET - get file (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)

#### DELETE - delete file (with given ID)
Argument|Type|Required|Default|Description
:--|:-:|:-:|:-:|:--
user|string|No||User ID
policy|string|No||Base64 encoded JSON dictionary where *conditions* is list of request arguments and *expiration* is expiration time (%Y-%m-%dT%H:%M:%SZ)
signature|string|No||Base64 encoded HMAC signature of policy (signed with key what is stored in entu-api-key property)
