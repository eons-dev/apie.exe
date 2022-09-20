import os
import logging
import shutil
import jsonpickle
from pathlib import Path
from flask import request
import eons as e
from .Exceptions import *

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
class Endpoint(e.UserFunctor):
    def __init__(this, name=e.INVALID_NAME()):
        super().__init__(name)

        this.enableRollback = False

        this.requiredKWArgs.append('request')
        
        this.optionalKWArgs['next'] = []
        this.optionalKWArgs['cachable'] = False
        this.optionalKWArgs['mode'] = 'json' #or html

        #this.response is returned by UserFunction().
        this.response = {}
        this.response['content_data'] = {}
        this.response['content_string'] = ""
        this.response['code'] = 200


    # Call things!
    # Override this or die.
    def Call(this):
        pass


    # Override this to perform whatever success checks are necessary.
    # Override of eons.Functor method. See that class for details
    def DidCallSucceed(this):
        return True


    # API compatibility shim
    def DidUserFunctionSucceed(this):
        return this.DidCallSucceed()


    # Hook for any pre-call configuration
    # Override of eons.Functor method. See that class for details
    def PreCall(this):
        pass


    # Hook for any post-call configuration
    # Override of eons.Functor method. See that class for details
    def PostCall(this):
        pass

    # Called right before *this returns.
    # Handles json pickling, etc.
    def ProcessResponse(this):
        if (this.mode == 'json'):
            if (len(this.response['content_string'])):
                logging.warning(f"Clobbering content_string ({this.response['content_string']})")

            this.response['content_string'].update({'cachable': this.cachable})
            this.response['content_string'] = jsonpickle.encode(this.response['content_data'])

    # Override of eons.Functor method. See that class for details
    def UserFunction(this):
        this.Call()
        if (not this.next):
            this.ProcessResponse()
            return this.response['content_data'], this.response['code']
        return this.CallNext()


    def CallNext(this):
        return this.executor.ProcessEndpoint(this.next.pop(0), this.request, predecessor=this, next=this.next)


    #### SPECIALIZED OVERRIDES. IGNORE THESE ####


    #Grab any known and necessary args from this.kwargs before any Fetch calls are made.
    def ParseInitialArgs(this):
        super().ParseInitialArgs()
        if ('predecessor' in this.kwargs):
            this.predecessor = this.kwargs.pop('predecessor')
        else:
            this.predecessor = None


    # Will try to get a value for the given varName from:
    #    first: this
    #    second: the endpoint preceding *this
    #    third: the executor (args > config > environment)
    # RETURNS the value of the given variable or None.
    def Fetch(this,
        varName,
        default=None,
        enableThis=True,
        enableExecutor=True,
        enableArgs=True,
        enableExecutorConfig=True,
        enableEnvironment=True,
        enablePrecedingEndpoint=True):
            
        # Duplicate code from eons.UserFunctor in order to establish precedence.
        if (enableThis and hasattr(this, varName)):
            logging.debug("...got {varName} from self ({this.name}).")
            return getattr(this, varName)

        if (enablePrecedingEndpoint and this.predecessor is not None):
            val = this.predecessor.Fetch(varName, default, enableThis, enableExecutor, enableArgs, enableExecutorConfig, enableEnvironment, enablePrecedingEndpoint)
            if (val is not None):
                logging.debug(f"...got {varName} from predecessor.")
                return val
        else: #No need to call the super method multiple times if the predecessor already did.
            return super().Fetch(varName, default, enableThis, enableExecutor, enableArgs, enableExecutorConfig, enableEnvironment)
