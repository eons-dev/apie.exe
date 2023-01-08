import os
import logging
import apie

# No Auth allows all requests.
# THIS IS EXTREMELY UNSAFE!
class noauth(apie.Authenticator):
	def __init__(this, name="No Authentication Authenticator"):
		super().__init__(name)

	# Yep!
	def Authenticate(this):
		auth = None
		if (getattr(this.request, 'authorization')):
			auth = this.request.authorization
		if (auth is None):
			logging.debug(f"Allowing request for {this.path} without authentication")
		else:
			logging.debug(f"Allowing request for {this.path} with authentication: {auth}")
		return True
