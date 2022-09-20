import os
import logging
import apie

# No Auth allows all requests.
# THIS IS EXTREMELY UNSAFE!
class none(apie.Authenticator):
    def __init__(this, name="No Authentication Authenticator"):
        super().__init__(name)

    # Yep!
    def UserFunction(this):
        logging.debug(f"Allowing request for {this.path} with authentication: {this.auth}")
        return True