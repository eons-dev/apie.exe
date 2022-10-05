import eons
import os
import logging
import shutil
import jsonpickle
from pathlib import Path
from flask import request, Response
from .Exceptions import *
from .Functor import Functor

# Endpoints are what is run when a given request is successfully authenticated.
# Put all your actual API logic in these!
# Keep in mind that Endpoints will be made available in a just-in-time, as-needed basis. There is no need to preload logic, etc.
# That also means that each Endpoint should operate in isolation and not require any other Endpoint to function.
# The exception to this isolation is when Endpoints are intended to be called in sequence.
# Any number of Endpoints can be chained together in any order. The behavior of the first affects the behavior of the last.
# This allows you to create generic "upload" Endpoints, where what is uploaded is determined by the preceding Endpoint.
# For example, you might have 3 Endpoints: "package", "photo", and "upload"; both package and photo set a member called "file_data"; upload Fetches "file_data" and puts it somewhere; you can thus use upload with either predecessor (e.g. .../package/upload and .../photo/upload).
# What is returned by an Endpoint is the very last Endpoint's return value. All intermediate values are skipped (so you can throw errors if calling things like .../package without a further action).
# NOTE: Endpoints should be published as api_s (i.e. projectType="api")
class Endpoint(Functor):
    def __init__(this, name=eons.INVALID_NAME()):
        super().__init__(name)

        this.enableRollback = False

        this.supportedMethods = [
            'POST',
            'GET',
            'PUT',
            'DELETE',
            'PATCH'
        ]

        # Only the items listed here will be allowed as next Endpoints.
        # If this list is empty, all endpoints are allowed.
        # When creating your endpoints, make sure to adjust this!
        # Also, please keep 'help'. It helps.
        this.allowedNext = ['help']

        this.next = []

        # Hop-by-hop headers are forbidden by WSGI.
        this.forbidden_headers = [
            'Keep-Alive',
            'Transfer-Encoding',
            'TE',
            'Connection',
            'Trailer',
            'Upgrade',
            'Proxy-Authorization',
            'Proxy-Authenticate',
        ]

        # What should the return type of *this be?
        this.mime = 'application/json'

        # If the client can store the result of *this locally, let them know.
        # When querying this, it is best to use the IsCachable() method.
        this.cacheable = False

        # If compiling data, from this.response['content_data'] for example, the response['content_string'] of *this will be overwritten.
        # You can override this behavior and force the compiled data to be lost by setting clobberContent to False.
        # This is useful if you are forwarding json requests and don't want to parse then recompile the content.
        this.clobberContent = True

        # The 'help' Endpoint will print this text.
        # Setting this will inform users on how to use your Endpoint.
        # Help will automatically print the name of *this for you, along with optional and required args, supported methods, and allowed next
        this.helpText = '''\
I'm just a generic endpoint. Not much I can do for ya. :\
'''

    # Call things!
    # Override this or die.
    def Call(this):
        pass


    # Override this to perform whatever success checks are necessary.
    # Override of eons.Functor method. See that class for details
    def DidCallSucceed(this):
        return True


    # If an error is thrown while Call()ing *this, APIE will attempt to return this method.
    def HandleBadRequest(this, request, error):
        message = f"Bad request for {this.name}: {str(error)}. "
        if ('help' in this.allowedNext):
            message += "Try appending /help."
        return message, 400


    # Hook for any pre-call configuration
    # Override of eons.Functor method. See that class for details
    def PreCall(this):
        pass


    # Hook for any post-call configuration
    # Override of eons.Functor method. See that class for details
    def PostCall(this):
        pass

    # Because APIE caches endpoints, the last response given will be stored in *this.
    # Call this method to clear the stale data.
    def ResetResponse(this):
        this.response = {}
        this.response['code'] = 200
        this.response['headers'] = {}
        this.response['content_data'] = {}
        this.response['content_string'] = ""

    # Called right before *this returns.
    # Handles json pickling, etc.
    def ProcessResponse(this):
        if (this.clobberContent):
            if(this.mime == 'application/json'):
                if (len(this.response['content_string'])):
                    logging.info(f"Clobbering content_string ({this.response['content_string']})")

                this.response['content_data'].update({'cacheable': this.cacheable})
                this.response['content_string'] = jsonpickle.encode(this.response['content_data'])

        if ('Content-Type' not in this.response['headers']):
            this.response['headers'].update({'Content-Type': this.mime})

        for header in this.forbidden_headers:
            try:
                this.response['headers'].pop(header)
            except KeyError:
                pass

        return Response(
            response = this.response['content_string'],
            status = this.response['code'],
            headers = this.response['headers'].items(),
            mimetype = this.mime, #This one is okay, I guess???
            content_type = None, #why is this here, we set it in the header. This is a problem in Flask.
            direct_passthrough = True # For speed??
        )


    # Override of eons.Functor method. See that class for details
    def UserFunction(this):
        # Skip execution when the user is asking for help.
        if (this.next and this.next[-1] == 'help'):
            return this.CallNext()

        this.ResetResponse()
        
        this.Call()
        
        if (not this.DidCallSucceed()):
            raise OtherAPIError(f"{this.name} failed.")
        
        if (not this.next):
            return this.ProcessResponse()
        
        return this.CallNext()


    def CallNext(this):
        return this.executor.ProcessEndpoint(this.next.pop(0), this.request, predecessor=this, next=this.next)


    #### SPECIALIZED OVERRIDES. IGNORE THESE ####

    # API compatibility shim
    def DidUserFunctionSucceed(this):
        return this.DidCallSucceed()


    #Grab any known and necessary args from this.kwargs before any Fetch calls are made.
    # This is executed first when calling *this.
    def ParseInitialArgs(this):
        super().ParseInitialArgs()

        # We want to let the executor know who we are as soon as possible, in case any errors come up in validation.
        this.executor.lastEndpoint = this

        if ('next' in this.kwargs):
            this.next = this.kwargs.pop('next')
        else:
            this.next = []

    def ValidateMethod(this):
        if (this.request.method not in this.supportedMethods):
            raise OtherAPIError(f"Method not supported: {this.request.method}")

    def ValidateNext(this):
        if (this.next and this.next[0] not in this.allowedNext):
            if (this.next[0] in ['hack'] and not this.executor.dev):
                raise OtherAPIError(f"Hacking is forbidden on production servers.")
            else:
                raise OtherAPIError(f"Next Endpoint not allowed: {this.next[0]}")

    def ValidateArgs(this):
        try:
            super().ValidateArgs()
        except eons.MissingArgumentError as e:
            # It doesn't matter if *this isn't valid if the user is asking for help.
            if (this.next and this.next[-1] == 'help'):
                return
            raise e

        this.ValidateMethod()
        this.ValidateNext()
        


