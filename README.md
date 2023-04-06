# Application Program Interface with Eons

Whether you want to make a [RESTful API](https://restfulapi.net/) or a fully functional web app, `apie` will help you build quickly and reliably: the eons way!

APIE is built on [eons](https://github.com/eons-dev/lib_eons) and uses [Eons Infrastructure Technologies](https://infrastructure.tech) to deliver modular functionality just-in-time.

The goal of developing http servers this way is to separate complex logic into a number of distinct, independent, and reusable Endpoints. This makes development easier through direct application of the [Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy) and ensures your systems are intuitive for users to apply to novel contexts after learning them once.

## Installation
`pip install apie`


## Usage

To run an `apie` server simply:
```shell
apie
```

APIE will bind to port 80 by default, which is not typically allowed for non-root users. In order to bypass this, you must use a different port. You can specify custom interface and port from the command line like so:
```shell
apie --host localhost --port 8080
```

You may also specify:
* `authenticator` - your chosen authentication modules (see below).
* `clean_start` - whether or not to nuke cached Endpoints on startup.
* `dev` - if true, will cause this to start in development mode as opposed to prod; more info [below](#testing-debugging-and-development)
* `preprocessor` - an Endpoint to always run first; more info [below](#preprocessor)

### apie.json

APIE will look for a file called "apie.json" in the directory it is launched from. If such is found, the configuration values from it will be read and processed in accordance with the eons library. For example, `apie --clean_start False` is the same as `apie` with an apie.json containing `{"clean_start": false}`. Note, command line variables will override configuration file variables (which override environment variables).

Here is an example `apie.json`:
```json
{
    "verbosity": 3,
    "no_repo": true,
    "clean_start": false,
    "port": 8080
}
```


### Parallelism

Currently, APIE only supports single-threaded operation. However, if your Authenticator and all your Endpoints maintain REST compatibility, you can run as many replicas of `apie` as you'd like!


### Methods

You may use any of the following http methods:

* GET
* POST
* PUT
* DELETE
* PATCH


## Design

### Authorization

The goal of authorizing requests is to prevent every api from becoming the same, since Endpoints are executed on-demand (see below), and to impose the obviously needed security.
If a request is not authorized, no Endpoint is called. This means you can limit which Endpoints are callable and who can call them.

Each and every request must be authenticated. You may use whatever authentication system you want (including the `noauth` and `from_config` modules provided in the `apie` package).

Your chosen authentication module must be of the `auth_` type if using [Eons Infrastructure Technologies](https://infrastructure.tech) (the default repository).  
To create your own authorization system, check out [auth_from_config.py](inc/auth/auth_from_config.py) for a starting point.  
NOTE: Every `Authenticator` MUST return `True` or `False`.


### API Endpoints

Endpoints `.../are/all/of/these?but=not-these`; in other words each part of a request path is a separate Endpoint.

To provide functionality, `apie` will download the Endpoints for any request that is executed as part of processing that request.
To see where packages are downloaded from and additional options, check out the [eons python library](https://github.com/eons-dev/lib_eons).

Each Endpoint may modify the next by simply setting member variables and methods ([per the eons implicit inheritance system](https://github.com/eons-dev/lib_eons/#implicit-inheritance)). For example, you might have 3 Endpoints: `package`, `photo`, and `upload`; both `package` and `photo` set a member called `file_data`; `upload` then `Fetch`es ([a method provided by eons](https://github.com/eons-dev/lib_eons/#inputs-through-configuration-file-and-fetch)) the `file_data` value and puts it somewhere; you can thus use `upload` with either precursor (e.g. `.../package/upload` and `.../photo/upload`).

This style of dynamic execution allows you to develop your API separately from its deployment environment (i.e. each module is standalone) and should make all parts of development easier.

#### Returns

**Only the last Endpoint is returned!**  
This is done to ensure that all information given is intended. If you want to provide information in your response, grab that information from the precursors, using `Fetch()`.  
Return values are automatically set from the `this.response` member.  
All Endpoints may set `this.response.code`: an [http status code](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) in the form of an `int`.

Every `Endpoint` should have a `this.mime` value. By default, it is `application/json`.  
For more on MIME Types, check out the [Mozilla documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types).

If the mime type is `application/json`, the data that are in `this.response.content.data` will be converted into a json string upon return.


#### Security and Validation

In addition to authenticating each request, Endpoints may further restrict what can follow them via the `this.allowedNext` member (list).  
By specifying only a limited list of actions, even users who are allowed to call your Endpoint can't call things like `.../something/legitimate/now_dump_all_user_passwords/k_thx_bye`.  
You can add to the `allowedNext` member by `append(...)`ing to the list.

You may also require only certain http methods be used with your Endpoint. This is for sanity more than security. Restricting the `this.supportedMethods` member (also a list), you can prevent things like `curl -X DELETE host/create/my_resource`. The `supportedMethods` is prepopulated with all the [http methods listed above](#methods). You can remove methods from this list with `this.supportedMethods.remove(...)`.


#### Error Handling

APIE itself keeps track of the last Endpoint it called. This allows that Endpoint to handle errors in its own execution. 

If you would like to add custom error handling, override `HandleBadRequest()` in your Endpoint. By default this will print the error message, per the python Exception and tells the user to call your Endpoint with `/help` (see [below](#help)).


### Syntax

APIE supports some unique syntax which can be specified in the request path.

#### Multi

A "Multicall" will make the same call for each element in a domain. This is essentially a foreach loop.  
Domains can be specified by prepending "[first_element,second_element]" to the desired Endpoint.  

Requirements:
1. The first character must be a '['.
2. Each element must be separated by a comma (',') WITHOUT a space (i.e. ', ' is wrong but ',' is right).
3. The domain must end with a ']'
4. There must be a valid Endpoint after the domain.

For example, `.../[public,private]list` would call `list` first with `public_` prepended to all Fetched arguments, then likewise with `private_`. If `list` needs a "url" arg, the first call would be made with `public_url` and the second would be made with `private_url`. The results of both would be combined (assuming the Content-Type is 'application/json') and a single list would be returned.

For more information, see the [multi Endpoint](inc/api/api_multi.py).

While not yet tested, multi-multi calls should work. For example `.../[one,two][red,blue]fish` should equate to `one/red/fish`, `one/blue/fish`, `two/red/fish`, `two/blue/fish`.  

Nested multicalls are not yet supported (e.g. `.../[one[red,blue],two['green','yellow']]fish` will not work at the moment).  

## REST Compatibility

To be "RESTful" means to abide the following principles.  
More information can be found at [restfulapi.net](https://restfulapi.net/)


### Uniform interface
> "A resource in the system should have only one logical URI, and that should provide a way to fetch related or additional data"

Each combination of Endpoints yields a unique execution path (e.g. `.../package/upload` operates on different resources than `.../photo/upload`).

Reusing the same Endpoint should provide the same functionality (e.g. `upload` should not start downloading things).

Endpoints should not provide duplicate functionality (besides, don't write the same line of code twice anyway!).

> "Once a developer becomes familiar with one of your APIs, [they] should be able to follow a similar approach for other APIs."


### Client–server
> "Servers and clients may also be replaced and developed independently, as long as the interface between them is not altered."

In addition to interacting with other machines over the net, the client-server paradigm is expanded to server-side processing through the use of standalone Endpoints. Each Endpoint should follow its own, independent development lifecycle and be interchangeable with any other Endpoint that provides the same up (`preceding`) and down (`next`) stream interfaces.


### Stateless
> "[The server] will treat every request as new. No session, no history."

This part is optional and what ultimately defines RESTful compatibility in APIE.  
If you wish to maintain state, use a custom Authenticator as described [below](#web-apps-user-sessions-and-the-static-auth).

> "No client context shall be stored on the server between requests. The client is responsible for managing the state of the application."


### Cacheable
> "In REST, caching shall be applied to resources when applicable, and then these resources MUST declare themselves cacheable"

To aid in caching, every `json` Endpoint will declare itself as "cacheable" or not based on the `this.cacheable` member value. If your response can be cached client-side, set `this.cacheable = True` (and `this.mime = 'application/json'`)


### Layered system

You can make calls to any other services you'd like within your Endpoints and Authenticators.


### Code on demand (optional)
> "you are free to return executable code to support a part of your application"

What you return is entirely up to you.


## Web Apps, User Sessions, and the Static Auth

If a RESTful application is inappropriate for your use case, you can still use apie. The only thing that changes is which Authenticator you employ. The Authenticator you choose is instantiated on startup, stored in the `auth` member of APIE, and lasts the life of the program. 

Because the Authenticator checks each and every request, you can use it to change the path executed, store a history of the user's requests, etc.

Both the Authenticator and each Endpoint can access apie from the `executor` member. This means each Endpoint has access to the the Authenticator (i.e. `this.executor.auth`). 

Combining all this, to make your app stateful, all you have to do is build an Authenticator to track the state you'd like.


## Testing, Debugging, and Development

There is a special `hack` Endpoint that is enabled when apie is run with `--dev True` (or equivalent, e.g. "dev": true in config).  
Hacking allows you to mock the functionality of downstream Endpoints.  
This behavior is not fully implemented but will be available soon.  


## Additional Features


### Preprocessor

You can set an Endpoint to be run before any other and which will not be included in the request path by specifying `preprocessor`.  
For example, with `{"preprocessor": "myapp"}` in your apie.json, a call to `.../access/whatever/` would be silently expanded to `.../myapp/access/whatever`
This is useful if you want to change Endpoints to fit a scheme suitable to your deployment, gain extra introspection, and much more.  


### Help

By default, you can call `.../anything/help` to get information on how to use `anything`. Data are returned as a json.


### From Config Authenticator

Included in the apie package is the `from_config` Authenticator. This allows you to store a static authentication scheme locally.  
This does not help with dynamic user access but does allow you to limit what Endpoints you allow access to.


## Resource Paradigm

One possible means of using apie is through the Resource Paradigm. This concept frames all apie requests as manipulations of resources. 

Resources can be anything but will generally be correlated with data structures of similar shape. For example, "user" might be a resource, where each user has a name, email, and password. These 3 fields define the shape of a user datum.

Manipulations take place through Operations and Operation Implementations. Operations are simple and define a consistent interface for use across many different resources. For example, the `list` operation is always paginated, so you can `.../user/list?page=2` or `.../whatever_else/list?per_page=100`. The list operation itself simply defines what arguments can be provided, gives some standard help text for users, and establishes basic features. How `list` actually works is entirely dependent on the implementation specified in the apie configuration. For example, if you `list` files stored on the server, you might use a `local` implementation to read and reply with inode data from the local filesystem; whereas, listing items from a database would use a `database` implementation, and so on.

The apie resource paradigm looks something like:
![image showing the layers of the apie resource paradigm](apie_resource-paradigm.png)
