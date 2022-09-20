import os
import logging
import shutil
import traceback
import eons as e
from flask import Flask, request
from waitress import serve
from pathlib import Path
from .Exceptions import *

class APIE(e.Executor):

    def __init__(this):
        super().__init__(name="Application Program Interface with eons", descriptionStr="A readily extensible take on APIs.")

        # this.RegisterDirectory("ebbs")

        this.optionalKWArgs['host'] = "0.0.0.0"
        this.optionalKWArgs['port'] = 80
        this.optionalKWArgs['clean_start'] = True
        this.optionalKWArgs['authenticator'] = "none"

        this.supportedMethods = [
            'POST',
            'GET',
            'PUT',
            'DELETE',
            'PATCH'
        ]


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
    def ProcessEndpoint(this, endpoint, request, **kwargs):
        endpoint = this.GetRegistered(endpoint, "api")
        return endpoint(executor=this, request=request, **kwargs)


    # What to do when a request causes an exception to be thrown.
    def HandleBadRequest(this, request):
        return "Bad request", 400


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
                if (this.auth(executor=this, path=path, auth=request.authorization)):
                    endpoints = path.split('/')
                    return this.ProcessEndpoint(endpoints.pop(0), request, next=endpoints)
                else:
                    return this.auth.Unauthorized()
            except Exception as error:
                traceback.print_exc()
                logging.error(str(error))
                return this.HandleBadRequest(request)

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