import os
import logging
import shutil
import jsonpickle
from pathlib import Path
import eons as e
from .Exceptions import *

class Endpoint(e.UserFunctor):
    def __init__(this, name=e.INVALID_NAME()):
        super().__init__(name)

        this.enableRollback = False


    # Call things!
    # Override this or die.
    # Empty Callers can be used with call.json to start call trees.
    def Call(this):
        pass


    # Override this to perform whatever success checks are necessary.
    # This will be called before running the next call step.
    def DidCallSucceed(this):
        return True


    # API compatibility shim
    def DidUserFunctionSucceed(this):
        return this.DidCallSucceed()


    # Hook for any pre-call configuration
    def PreCall(this):
        pass


    # Hook for any post-call configuration
    def PostCall(this):
        pass


    # Override of eons.Functor method. See that class for details
    def UserFunction(this):

        this.PreCall()

        logging.debug(f"<---- Calling {this.name} ---->")
        this.Call()
        logging.debug(f">---- Done Calling {this.name} ----<")

        this.PostCall()


