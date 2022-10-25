import eons
import os
import logging
import shutil
import jsonpickle
from pathlib import Path
from flask import request, Response
from .Exceptions import *
from .Functor import Functor

# Endpoints are what is run when a given request is successfully authenticated.
# Put all your actual API logic in these!
# Keep in mind that Endpoints will be made available in a just-in-time, as-needed basis. There is no need to preload logic, etc.
# That also means that each Endpoint should operate in isolation and not require any other Endpoint to function.
# The exception to this isolation is when Endpoints are intended to be called in sequence.
# Any number of Endpoints can be chained together in any order. The behavior of the first affects the behavior of the last.
# This allows you to create generic "upload" Endpoints, where what is uploaded is determined by the preceding Endpoint.
# For example, you might have 3 Endpoints: "package", "photo", and "upload"; both package and photo set a member called "file_data"; upload Fetches "file_data" and puts it somewhere; you can thus use upload with either precursor (e.g. .../package/upload and .../photo/upload).
# What is returned by an Endpoint is the very last Endpoint's return value. All intermediate values are skipped (so you can throw errors if calling things like .../package without a further action).
# NOTE: Endpoints should be published as api_s (i.e. projectType="api")
class Endpoint(Functor):
	def __init__(this, name=eons.INVALID_NAME()):
		super().__init__(name)

		this.enableRollback = False

		# Internal logic; used when calling 'help', etc.
		this.bypassCall = False

		# What methods can be used with this Endpoint?
		this.supportedMethods = [
			'POST',
			'GET',
			'PUT',
			'DELETE',
			'PATCH'
		]

		# Only the items listed here will be allowed as next Endpoints.
		# If this list is empty, all endpoints are allowed.
		# When creating your endpoints, make sure to adjust this!
		# Also, please keep 'help'. It helps.
		#
		# To allow all Endpoints, set this to [].
		this.allowedNext = ['help']

		this.next = []

		# Hop-by-hop headers are forbidden by WSGI.
		this.forbidden_headers = [
			'Keep-Alive',
			'Transfer-Encoding',
			'TE',
			'Connection',
			'Trailer',
			'Upgrade',
			'Proxy-Authorization',
			'Proxy-Authenticate',
		]

		# What should the return type of *this be?
		this.mime = 'application/json'

		# If the client can store the result of *this locally, let them know.
		# When querying this, it is best to use the IsCachable() method.
		this.cacheable = False

		# If compiling data, from this.response.content.data for example, the response.content.string of *this will be overwritten.
		# You can override this behavior and force the compiled data to be lost by setting clobberContent to False.
		# This is useful if you are forwarding json requests and don't want to parse then recompile the content.
		this.clobberContent = True

		# What is returned after Call()
		this.response = eons.util.DotDict()
		this.response.content = eons.util.DotDict()


# Please override this for each of your Endpoints.
	# RETURN a string that tells the user how to call *this.
	# It is recommended to return a static string, without Fetching anything.
	#
	# The 'help' Endpoint will print this text.
	# Setting this will inform users on how to use your Endpoint.
	# Help will automatically print the name of *this for you, along with optional and required args, supported methods, and allowed next
	def GetHelpText(this):
		return '''\
LOL! Look at you: needing help. Pathetic.
'''

	# Call things!
	# Override this or die.
	def Call(this):
		pass


	# Override this to perform whatever success checks are necessary.
	# Override of eons.Functor method. See that class for details
	def DidCallSucceed(this):
		return True


	# If an error is thrown while Call()ing *this, APIE will attempt to return this method.
	def HandleBadRequest(this, request, error):
		message = f"Bad request for {this.name}: {str(error)}. "
		if ('help' in this.allowedNext):
			message += "Try appending /help."
		return message, 400


	# Hook for any pre-call configuration
	# Override of eons.Functor method. See that class for details
	def PreCall(this):
		pass


	# Hook for any post-call configuration
	# Override of eons.Functor method. See that class for details
	def PostCall(this):
		pass


	# Because APIE caches endpoints, the last response given will be stored in *this.
	# Call this method to clear the stale data.
	def ResetResponse(this):
		this.response.code = 200
		this.response.headers = {}
		this.response.content.data = {}
		this.response.content.string = ""


	# Called right before *this returns.
	# Handles json pickling, etc.
	def ProcessResponse(this):
		if (this.clobberContent):
			if(this.mime == 'application/json'):
				if (len(this.response.content.string)):
					logging.info(f"Clobbering content.string ({this.response.content.string})")

				this.response.content.data.update({'cacheable': this.cacheable})
				this.response.content.string = jsonpickle.encode(this.response.content.data)

		if ('Content-Type' not in this.response.headers):
			this.response.headers.update({'Content-Type': this.mime})

		for header in this.forbidden_headers:
			try:
				this.response.headers.pop(header)
			except KeyError:
				pass

		return Response(
			response = this.response.content.string,
			status = this.response.code,
			headers = this.response.headers.items(),
			mimetype = this.mime, #This one is okay, I guess???
			content_type = None, #why is this here, we set it in the header. This is a problem in Flask.
			direct_passthrough = True # For speed??
		)


	# Override of eons.Functor method. See that class for details
	def Function(this):
		this.bypassCall = False
		if (this.next and this.next[-1] == 'help'):
			this.bypassCall = True
			return None

		this.ResetResponse()
		this.PreCall()
		this.Call()
		this.PostCall()
		return this.ProcessResponse()


	#### SPECIALIZED OVERRIDES. IGNORE THESE ####

	# API compatibility shim
	def DidFunctionSucceed(this):
		if (this.bypassCall):
			return True
		return this.DidCallSucceed()

	def PopulatePrecursor(this):
		super().PopulatePrecursor()

		# We want to let the executor know who we are as soon as possible, in case any errors come up in validation.
		this.executor.lastEndpoint = this

	#Grab any known and necessary args from this.kwargs before any Fetch calls are made.
	# This is executed first when calling *this.
	def ParseInitialArgs(this):
		super().ParseInitialArgs()


	def ValidateMethod(this):
		if (this.request.method not in this.supportedMethods):
			raise OtherAPIError(f"Method not supported: {this.request.method}")

	def ValidateNext(this, next):
		if (next and this.allowedNext and next not in this.allowedNext):
			logging.error(f"{next} is not allowed after {this.name}; only {this.allowedNext}")
			if (next in ['hack'] and not this.executor.dev):
				raise OtherAPIError(f"Hacking is forbidden on production servers.")
			else:
				raise OtherAPIError(f"Next Endpoint not allowed: {next}")
		return True

	def ValidateArgs(this):
		try:
			super().ValidateArgs()
		except eons.MissingArgumentError as e:
			logging.recovery(f"Error is irrelevant; user is seeking help ({str(e)})")
			# It doesn't matter if *this isn't valid if the user is asking for help.
			if (this.next and this.next[-1] == 'help'):
				return
			raise e
		


