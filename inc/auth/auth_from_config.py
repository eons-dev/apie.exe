import os
import logging
import apie
import re

# The From Config Authenticator reads authentication settings from the apie.json
class from_config(apie.Authenticator):
	def __init__(this, name="From Config Authenticator"):
		super().__init__(name)

		this.staticKWArgs.append('anonymous_endpoints')


	def CanEndpointBeAccessedAnonymously(this):
		for endpoint in this.anonymous_endpoints:
			if (re.match(endpoint, this.path)):
				logging.debug(f"Found match for {this.path} in anonymous endpoint: {endpoint}.")
				return True
		logging.debug(f"No match for {this.path} in anonymous endpoints.")		
		return False

	def Authenticate(this):
		if (this.CanEndpointBeAccessedAnonymously()):
			logging.debug(f"Allowing anonymous access to {this.path}.")
			return True

		# Currently, there is no actual authentication allowed.
		return False
