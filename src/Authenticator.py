import os
import logging
import shutil
import jsonpickle
from pathlib import Path
import eons as e
from .Exceptions import *

# Authenticator is a Functor which validates whether or not a request is valid.
# The inputs will be the method and path of the request and the request authentication.
# If you need to check whether the request parameters, data, files, etc. are valid, please do so in your endpoint.
# By limiting what we pass to an Authenticator, we speed up the authentication process for all requests.
# Because this class will be invoked often, we have made some performant modifications to the default UserFunctor methods.
# NOTE: All logic for *this should be in UserFunction. There are no extra functions called (e.g. PreCall, PostCall, etc.)
# UserFunction should either return False or raise an exception if the provided request is invalid and should return True if it is.
class Authenticator(e.UserFunctor):
    def __init__(this, name="Authenticator"):
        super().__init__(name)

        this.requiredKWArgs.append('path')
        
        this.optionalKWArgs['auth'] = None


    # Override of eons.Functor method. See that class for details
    # NOTE: All logic for *this should be in UserFunction. There are no extra functions called (e.g. PreCall, PostCall, etc.)
    # UserFunction should either return False or raise an exception if the provided request is invalid and should return True if it is.
    def UserFunction(this):
        return True

    # This will be called whenever an unauthorized request is made.
    def Unauthorized(this):
        return "Unauthorized", 401

    # Override of eons.Functor method. See that class for details
    def ValidateArgs(this):
        for rkw in this.requiredKWArgs:
            if (hasattr(this, rkw)):
                continue

            fetched = this.Fetch(rkw)
            if (fetched is not None):
                this.Set(rkw, fetched)
                continue

            # Nope. Failed.
            errStr = f"{rkw} required but not found."
            logging.error(errStr)
            raise MissingArgumentError(f"argument {rkw} not found in {this.kwargs}") #TODO: not formatting string??

        for okw, default in this.optionalKWArgs.items():
            if (hasattr(this, okw)):
                continue

            this.Set(okw, this.Fetch(okw, default=default))

    # Override of eons.Functor method. See that class for details
    def __call__(this, **kwargs) :
        this.kwargs = kwargs
        
        this.ParseInitialArgs()
        this.ValidateArgs()
        return this.UserFunction()
        