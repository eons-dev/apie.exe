import os
import logging
import shutil
import jsonpickle
from pathlib import Path
import eons
from .Exceptions import *
from .Functor import Functor

# Authenticator is a Functor which validates whether or not a request is valid.
# The inputs will be the path of the request and the request itself.
# If you need to check whether the request parameters, data, files, etc. are valid, please do so in your Endpoint.
# Because this class will be invoked often, we have made some performant modifications to the default UserFunctor methods.
# NOTE: All logic for *this should be in UserFunction. There are no extra functions called (e.g. PreCall, PostCall, etc.)
# UserFunction should either return False or raise an exception if the provided request is invalid and should return True if it is.
class Authenticator(Functor):
    def __init__(this, name="Authenticator"):
        super().__init__(name)

    # Override of eons.Functor method. See that class for details
    # NOTE: All logic for *this should be in UserFunction. There are no extra functions called (e.g. PreCall, PostCall, etc.)
    # UserFunction should either return False or raise an exception if the provided request is invalid and should return True if it is.
    def UserFunction(this):
        return True

    # This will be called whenever an unauthorized request is made.
    def Unauthorized(this, path):
        logging.debug(f"Unauthorized: {this.name} on {path}")
        return "Unauthorized", 401

    # Override of eons.Functor method. See that class for details
    def ParseInitialArgs(this):
        super().ParseInitialArgs()

        this.path = this.kwargs.pop('path')

    # Override of eons.Functor method. See that class for details
    # Slimmed down for performance
    def __call__(this, **kwargs):
        this.kwargs = kwargs
        
        this.ParseInitialArgs()
        this.ValidateArgs()
        return this.UserFunction()
