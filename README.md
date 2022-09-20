# Application Program Interface with Eons

This program makes serving [RESTful APIs](https://restfulapi.net/) easy!

APIE is built on [eons](https://github.com/eons-dev/lib_eons) and uses [Eons Infrastructure Technologies](https://infrastructure.tech) to deliver modular functionality just-in-time.


## Installation
`pip install apie`


## Usage

To run an `apie` server simply:
```shell
pip install apie
apie
```

You can specify custom interface and port like so:
```shell
apie --host localhost --port 8080
```

You may also specify:
* `clean_start` - whether or not to nuke cached Endpoints on startup
* `authenticator` - your chosen authentication modules (see below).


### Methods

You may use any of the following http methods:

* GET
* POST
* PUT
* DELETE
* PATCH


### Authorization

The goal of authorizing requests is to prevent every api from becoming the same, since Endpoints are executed on-demand (see below), and to impose the obviously needed security.
If a request is not authorized, no Endpoint is called. This means you can limit which Endpoints are callable and who can call them.

Each and every request must be authenticated. You may use whatever authentication system you want (including the `none` provided in the `apie` package).

Your chosen authentication module must be of the `auth_` type if using [Eons Infrastructure Technologies](https://infrastructure.tech) (the default repository).  
To create your own authorization system, check out `inc/auth/auth_none.py` for a starting point. 
NOTE: Every `Authenticator` MUST return `True` or `False`.


### API Endpoints

Endpoints `.../are/all/of/these?but=not-these`; in other words each part of a request path is a separate Endpoint.

To provide functionality, `apie` will download the Endpoints for any request that is executed as part of processing that request.
To see where packages are downloaded from and additional options, check out the [eons python library](https://github.com/eons-dev/lib_eons).

Each Endpoint may modify the next by simply setting member variables. For example, you might have 3 Endpoints: `package`, `photo`, and `upload`; both `package` and `photo` set a member called `file_data`; `upload` then `Fetch`es (a method provided by eons) the `file_data` value and puts it somewhere; you can thus use `upload` with either predecessor (e.g. `.../package/upload` and `.../photo/upload`).

This style of dynamic execution allows you to develop your API separately from its deployment environment and should make all parts of development easier.

All Endpoint modules must be of the `api_` type if using [Eons Infrastructure Technologies](https://infrastructure.tech) (the default repository).  
To create your own Endpoints, check out `inc/api/api_test.py` for a starting point. 
Every `Endpoint` has a mode that is either `json` or `http`.

**Only the last Endpoint is returned!**  
This is done to ensure that all information given is intended. If you want to provide information in your response, grab that information from the predecessors, using `Fetch()`.  
Return values are automatically set from the `this.response` member.  
All Endpoints MAY set `this.response['code']`: an [http status code](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) in the form of an `int`.


#### JSON Endpoints

JSON Endpoints SHOULD set `this.response['content_data']` (a dictionary).

They SHOULD NOT set `this.response['content_string']`.


#### HTTP Endpoints

JSON Endpoints SHOULD set `this.response['content_sting']` (a string).


## REST Compatibility

To be "RESTful" means to abide the following principles.


### Uniform interface
> "A resource in the system should have only one logical URI, and that should provide a way to fetch related or additional data"

Each combination of Endpoints yields a unique execution path (e.g. `.../package/upload` operates on different resources than `.../photo/upload`).

Reusing the same Endpoint should provide the same functionality (e.g. `upload` should not start downloading things).

Endpoints should not provide duplicate functionality (besides, don't write the same line of code twice anyway!).

> "Once a developer becomes familiar with one of your APIs, [they] should be able to follow a similar approach for other APIs."


### Client–server
> "Servers and clients may also be replaced and developed independently, as long as the interface between them is not altered."

Done.


### Stateless
> "It will treat every request as new. No session, no history."

While you can break this paradigm by, say, storing requests in a database that you query on subsequent requests, try not to vary your behavior based on past interactions.

> "No client context shall be stored on the server between requests. The client is responsible for managing the state of the application."


### Cacheable
> "In REST, caching shall be applied to resources when applicable, and then these resources MUST declare themselves cacheable"

To aid in caching, every `json` Endpoint will declare itself as "cachable" or not based on the `this.cachable` member value. If your response can be cached client-side, set `this.cachable = True` (and `this.mode = 'json'`)


### Layered system

You can make calls to any other services you'd like within your Endpoints and Authenticators.


### Code on demand (optional)
> "you are free to return executable code to support a part of your application"

What you return is entirely up to you.