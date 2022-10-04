import os
import logging
import apie

class help(apie.Endpoint):
    def __init__(this, name="Help for preceding API Endpoint"):
        super().__init__(name)

        this.mime = 'application/json'

    def Call(this):
        this.cacheable = this.predecessor.cacheable #cacheable is automatically added to the response
        this.response['content_data'].update({
            "endpoint": this.predecessor.name,
            "supported_methods": this.predecessor.supportedMethods,
            "allowed_next": this.predecessor.allowedNext,
            "required_args": this.predecessor.requiredKWArgs,
            "optional_args": this.predecessor.optionalKWArgs,
            "get_args_from_request": this.predecessor.fetchFromRequest,
            "help_text": this.predecessor.helpText
        })

    # Override of eons.Functor method. See that class for details
    def UserFunction(this):
        this.ResetResponse()
        this.Call()
        return this.ProcessResponse()
