import os
import logging
import apie

# The From Config Authenticator reads authentication settings from the apie.json
class from_config(apie.Authenticator):
    def __init__(this, name="From Config Authenticator"):
        super().__init__(name)


    def UserFunction(this):
        logging.debug(f"Allowing request for {this.path} with authentication: {this.auth}")
        return True

        #TODO
