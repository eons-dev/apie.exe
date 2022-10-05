import eons
import os
import logging
import shutil
import jsonpickle
from pathlib import Path
from flask import request, Response
from .Exceptions import *

# APIE Functors extend Eons Functors in order to:
# 1. Improve Fetch() behavior when cascading multiple Functor executions.
# 2. Allow Fetching from a http request.
class Functor(eons.UserFunctor):
    def __init__(this, name=eons.INVALID_NAME()):
        super().__init__(name)

        this.enableRollback = False

        # If you'd like to only check for your values in certain places, adjust this list.
        # These will call the corresponding methods as described in the docs: https://flask.palletsprojects.com/en/2.2.x/api/#flask.Request.args
        this.fetchFromRequest = [
            'args',
            'form',
            'json',
            'files'
        ]

    #Grab any known and necessary args from this.kwargs before any Fetch calls are made.
    # This is executed first when calling *this.
    def ParseInitialArgs(this):
        super().ParseInitialArgs()

        this.request = this.kwargs.pop('request')

        if ('predecessor' in this.kwargs):
            this.predecessor = this.kwargs.pop('predecessor')
        else:
            this.predecessor = None



    # Will try to get a value for the given varName from:
    #    first: this
    #    second: the Functor preceding *this
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
        enablePredecessor=True,
        enableRequest=True):
            
        # Duplicate code from eons.UserFunctor in order to establish precedence.
        if (enableThis and hasattr(this, varName)):
            logging.debug(f"...got {varName} from {this.name}.")
            return getattr(this, varName)

        if (enablePredecessor and this.predecessor is not None):
            # enableThis is hardcoded as True of enablePredecessor but only for the predecessor.
            val = this.predecessor.Fetch(varName, default, True, enableExecutor, enableArgs, enableExecutorConfig, enableEnvironment, enablePredecessor, enableRequest)
            if (val is not None):
                # logging.debug(f"...got {varName} from predecessor.") # Too many logs.
                return val

        # Checking this when the predecessor already did is wasteful but we don't know what they're looking at or looking for, so let's do it again.
        if (enableRequest):
            for field in this.fetchFromRequest:
                if (field == 'json' and this.request.content_type != "application/json"):
                    continue
                if (field == 'forms' and not this.request.data):
                    continue
                if (field == 'files' and not this.request.files):
                    continue
                
                # TODO: there's a better way to do this. You can pass the field arg to this.request somehow...
                val = getattr(this.request, field).get(varName)
                if (val is not None):
                    logging.debug(f"...got {varName} from request.")
                    return val

            return super().Fetch(varName, default, enableThis, enableExecutor, enableArgs, enableExecutorConfig, enableEnvironment)

