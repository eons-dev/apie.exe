import os
import logging
import eons as e
from .Exceptions import *

class EBBS(e.Executor):

    def __init__(this):
        super().__init__(name="Application Program Interface with eons", descriptionStr="A readily extensible take on APIs.")

        # this.RegisterDirectory("ebbs")


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
    def AddArgs(this):
        super().AddArgs()
        this.argparser.add_argument('-h','--host', type = str, metavar = '127.0.0.1', default = '0.0.0.0', help = 'host ip to accept connections through', dest = 'host')
        this.argparser.add_argument('-p','--port', type = str, metavar = '80', help = 'port to run on', dest = 'port')


    #Override of eons.Executor method. See that class for details
    def UserFunction(this):
        super().UserFunction()
        
