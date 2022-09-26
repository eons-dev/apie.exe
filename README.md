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

You can specify custom interface and port like so:
```shell
apie --host localhost --port 8080
```

You may also specify:
* `authenticator` - your chosen authentication modules (see below).
* `clean_start` - whether or not to nuke cached Endpoints on startup.
* `dev` - if true, will cause this to start in development mode as opposed to prod; more info [below](#testing-debugging-and-development)
* `preprocessor` - an Endpoint to always run first; more info [below](#preprocessor)

### apie.json

APIE will look for a file called "apie.json" in the directory it is launched from. If such is found, the configuration values from it will be read and processed in accordance with the eons library. For example, `apie --clean_start False` is the same as `apie` with an apie.json containing `{"clean_start": false}`


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

Each and every request must be authenticated. You may use whatever authentication system you want (including the `none` and `from_config` modules provided in the `apie` package).

Your chosen authentication module must be of the `auth_` type if using [Eons Infrastructure Technologies](https://infrastructure.tech) (the default repository).  
To create your own authorization system, check out `inc/auth/auth_from_config.py` for a starting point.  
NOTE: Every `Authenticator` MUST return `True` or `False`.


### API Endpoints

Endpoints `.../are/all/of/these?but=not-these`; in other words each part of a request path is a separate Endpoint.

To provide functionality, `apie` will download the Endpoints for any request that is executed as part of processing that request.
To see where packages are downloaded from and additional options, check out the [eons python library](https://github.com/eons-dev/lib_eons).

Each Endpoint may modify the next by simply setting member variables. For example, you might have 3 Endpoints: `package`, `photo`, and `upload`; both `package` and `photo` set a member called `file_data`; `upload` then `Fetch`es (a method provided by eons) the `file_data` value and puts it somewhere; you can thus use `upload` with either predecessor (e.g. `.../package/upload` and `.../photo/upload`).

This style of dynamic execution allows you to develop your API separately from its deployment environment (i.e. each module is standalone) and should make all parts of development easier.

All Endpoint modules must be of the `api_` type if using [Eons Infrastructure Technologies](https://infrastructure.tech) (the default repository).  
To create your own Endpoints, check out `inc/api/api_external.py` for a starting point. 


#### Returns

**Only the last Endpoint is returned!**  
This is done to ensure that all information given is intended. If you want to provide information in your response, grab that information from the predecessors, using `Fetch()`.  
Return values are automatically set from the `this.response` member.  
All Endpoints MAY set `this.response['code']`: an [http status code](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) in the form of an `int`.

Every `Endpoint` should have a `this.mime` value. By default, it is `application/json`.  
For more on MIME Types, check out the [Mozilla documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types).

If the mime type is `application/json`, the data that are in `this.response['content_data']` will be converted into json upon return.


#### Security and Validation

In addition to authenticating each request, Endpoints may further restrict what can follow them via the `this.allowedNext` member (list).  
By specifying only a limited list of actions, even users who are allowed to call your Endpoint can't call things like `.../something/legitimate/now_dump_all_user_passwords/k_thx_bye`.  
You can add to the `allowedNext` member by `append(...)`ing to the list.

You may also require only certain http methods be used with your Endpoint. This is for sanity more than security. Restricting the `this.supportedMethods` member (also a list), you can prevent things like `curl -X DELETE host/create/my_resource`. The `supportedMethods` is prepopulated with all the [http methods listed above](#methods). You can remove methods from this list with `this.supportedMethods.remove(...)`.


#### Error Handling

APIE itself keeps track of the last Endpoint it called. This allows that Endpoint to handle errors in its own execution. 

If you would like to add custom error handling, override `HandleBadRequest()` in your Endpoint. By default this will print the error message, per a any python Exception and tells the user to call your Endpoint with `/help` (see [below](#help)).


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
