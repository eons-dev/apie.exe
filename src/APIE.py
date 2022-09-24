import os
import logging
import shutil
import traceback
import eons
from flask import Flask, request
from waitress import serve
from pathlib import Path
from .Exceptions import *

class APIE(eons.Executor):

    def __init__(this):
        super().__init__(name="Application Program Interface with eons", descriptionStr="A readily extensible take on APIs.")

        # this.RegisterDirectory("ebbs")

        this.optionalKWArgs['host'] = "0.0.0.0"
        this.optionalKWArgs['port'] = 80
        this.optionalKWArgs['dev'] = False
        this.optionalKWArgs['clean_start'] = True
        this.optionalKWArgs['authenticator'] = "none"
        this.optionalKWArgs['preprocessor'] = ""

        this.supportedMethods = [
            'POST',
            'GET',
            'PUT',
            'DELETE',
            'PATCH'
        ]

        # *this is single-threaded. If we want parallel processing, we can create replicas.
        this.lastEndpoint = None

        # TODO: is it actually faster to keep instances in RAM?
        # This is required for staticKWArgs to be effective.
        this.cachedEndpoints = {}


    # Configure class defaults.
    # Override of eons.Executor method. See that class for details
    def Configure(this):
        super().Configure()

        this.defualtConfigFile = "apie.json"


    # Override of eons.Executor method. See that class for details
    def RegisterAllClasses(this):
        super().RegisterAllClasses()
        this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath("api")))
        this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath("auth")))


    # Acquire and run the given endpoint with the given request.
    def ProcessEndpoint(this, endpointName, request, **kwargs):
        if (endpointName in this.cachedEndpoints):
            return this.cachedEndpoints[endpointName](executor=this, request=request, **kwargs)
        
        endpoint = this.GetRegistered(endpointName, "api")
        this.cachedEndpoints.update({endpointName: endpoint})
        return endpoint(executor=this, request=request, **kwargs)


    # What to do when a request causes an exception to be thrown.
    def HandleBadRequest(this, request, error):
        message = f"Bad request: {str(error)}"
        return message, 400


    # Override of eons.Executor method. See that class for details
    def UserFunction(this):
        super().UserFunction()

        if (this.clean_start):
            this.Clean()

        this.auth = this.GetRegistered(this.authenticator, "auth")

        this.flask = Flask(this.name)

        @this.flask.route("/", defaults={"path": ""}, methods = this.supportedMethods)
        def root(path):
            return "It works!", 200

        @this.flask.route("/<string:path>", methods = this.supportedMethods)
        @this.flask.route("/<path:path>", methods = this.supportedMethods)
        def handler(path):
            try:
                if (this.auth(executor=this, path=path, request=request)):
                    endpoints = []
                    if (this.preprocessor):
                        endpoints.append(this.preprocessor)
                    endpoints.extend(path.split('/'))
                    this.lastEndpoint = None
                    logging.debug(f"Responding to request for {path}; request: {request}")
                    response = this.ProcessEndpoint(endpoints.pop(0), request, next=endpoints)
                    logging.debug(f"Got response: {response}")
                    return response
                else:
                    return this.auth.Unauthorized(path)
            except Exception as error:
                traceback.print_exc()
                logging.error(str(error))
                if (this.lastEndpoint):
                    try:
                        return this.lastEndpoint.HandleBadRequest(request, error)
                    except Exception:
                        pass
                return this.HandleBadRequest(request, error) #fine. We'll do it ourselves.

        options = {}
        options['app'] = this.flask
        options['host'] = this.host
        options['port'] = this.port

        # Only applicable if using this.flask.run(**options)
        # if (this.args.verbose > 0):
        #     options['debug'] = True
        #     options['use_reloader'] = False

        serve(**options)


    # Remove possibly stale modules.
    def Clean(this):
        repoPath = Path(this.repo['store'])
        if (repoPath.exists()):
            shutil.rmtree(this.repo['store'])
        repoPath.mkdir(parents=True, exist_ok=True)
