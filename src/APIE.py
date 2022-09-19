import os
import logging
import eons as e
from flask import Flask
from .Exceptions import *

class APIE(e.Executor):

    def __init__(this):
        super().__init__(name="Application Program Interface with eons", descriptionStr="A readily extensible take on APIs.")

        # this.RegisterDirectory("ebbs")

        this.optionalKWArgs['host'] = "0.0.0.0"
        this.optionalKWArgs['port'] = 80


    #Configure class defaults.
    #Override of eons.Executor method. See that class for details
    def Configure(this):
        super().Configure()

        this.defualtConfigFile = "apie.json"


    #Override of eons.Executor method. See that class for details
    def RegisterAllClasses(this):
        super().RegisterAllClasses()
        # this.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build"))


    #Override of eons.Executor method. See that class for details
    def UserFunction(this):
        super().UserFunction()
        this.flask = Flask(this.name)

        @this.flask.route("/")
        def test():
            return "<p>Hello, World!</p>"

        options = {}
        options['host'] = this.host
        options['port'] = this.port

        if (this.args.verbose > 0):
            options['debug'] = True
            options['use_reloader'] = False
        
        this.flask.run(**options)
