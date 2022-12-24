import os
import logging
import shutil
import traceback
import eons
from flask import Flask, request
from waitress import serve
from pathlib import Path
from .Exceptions import *

class APIE(eons.Executor):

	def __init__(this):
		super().__init__(name="Application Program Interface with Eons", descriptionStr="A readily extensible take on APIs.")

		# this.RegisterDirectory("ebbs")

		this.optionalKWArgs['host'] = "0.0.0.0"
		this.optionalKWArgs['port'] = 80
		this.optionalKWArgs['dev'] = False
		this.optionalKWArgs['clean_start'] = True
		this.optionalKWArgs['authenticator'] = "noauth"
		this.optionalKWArgs['preprocessor'] = ""

		this.supportedMethods = [
			'POST',
			'GET',
			'PUT',
			'DELETE',
			'PATCH'
		]

		# Used in Function()
		this.auth = None
		this.flask = None

		# *this is single-threaded. If we want parallel processing, we can create replicas.
		this.lastEndpoint = None

		this.defaultConfigFile = "apie.json"

	# Override of eons.Executor method. See that class for details
	def RegisterIncludedClasses(this):
		super().RegisterIncludedClasses()
		this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath("api")))
		this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath("auth")))
		

	# Override of eons.Executor method. See that class for details
	def RegisterAllClasses(this):
		super().RegisterAllClasses()


	# Acquire and run the given endpoint with the given request.
	def ProcessEndpoint(this, endpointName, request, **kwargs):

		# Parse Endpoint syntax.
		# "[..., ...]something" => multi(domain=[..., ...], next="something")
		if (endpointName.startswith('[')):
			if ('domain' in kwargs):
				raise APIError(f"Domain already exists in multicall; domain={kwargs['domain']}; multicall={endpointName}")

			domainStrEndPos = endpointName.find(']')+1
			domainStr = endpointName[:domainStrEndPos]
			if ('next' in kwargs):
				kwargs['next'] = [endpointName[domainStrEndPos:]].extend(kwargs['next'])
			else:
				kwargs['next'] = endpointName[domainStrEndPos:]

			# Trim '(' and ')', then make list.
			kwargs['domain'] = domainStr[1:-1].split(',')

			endpointName = "multi"

		if (endpointName in this.cachedFunctors):
			return this.cachedFunctors[endpointName](executor=this, request=request, **kwargs)

		endpoint = this.GetRegistered(endpointName, "api")
		this.cachedFunctors.update({endpointName: endpoint})
		return endpoint(executor=this, request=request, **kwargs)


	# What to do when a request causes an exception to be thrown.
	def HandleBadRequest(this, request, error):
		message = f"Bad request: {str(error)}"
		return message, 400


	# Override of eons.Executor method. See that class for details
	def Function(this):
		super().Function()

		if (this.clean_start):
			this.Clean()

		this.auth = this.GetRegistered(this.authenticator, "auth")

		this.flask = Flask(this.name)

		@this.flask.route("/", defaults={"path": ""}, methods = this.supportedMethods)
		def root(path):
			return "It works!", 200

		@this.flask.route("/<string:path>", methods = this.supportedMethods)
		@this.flask.route("/<path:path>", methods = this.supportedMethods)
		def handler(path):
			try:
				if (this.auth(executor=this, path=path, request=request)):
					endpoints = []
					if (this.preprocessor):
						endpoints.append(this.preprocessor)
					if (path.endswith('/')):
						path = path[:-1]
					endpoints.extend(path.split('/'))
					this.lastEndpoint = None
					logging.debug(f"Responding to request for {path}; request: {request}")
					response = this.ProcessEndpoint(endpoints.pop(0), request, next=endpoints)
					logging.debug(f"Got headers: {response.headers}")
					logging.debug(f"Got response: {response}")
					return response
				else:
					return this.auth.Unauthorized(path)
			except Exception as error:
				traceback.print_exc()
				logging.error(str(error))
				if (this.lastEndpoint):
					try:
						return this.lastEndpoint.HandleBadRequest(request, error)
					except Exception:
						pass
				return this.HandleBadRequest(request, error) #fine. We'll do it ourselves.

		options = {}
		options['app'] = this.flask
		options['host'] = this.host
		options['port'] = this.port

		# Only applicable if using this.flask.run(**options)
		# if (this.args.verbose > 0):
		#	 options['debug'] = True
		#	 options['use_reloader'] = False

		serve(**options)


	# Remove possibly stale modules.
	def Clean(this):
		repoPath = Path(this.repo['store'])
		if (repoPath.exists()):
			shutil.rmtree(this.repo['store'])
		repoPath.mkdir(parents=True, exist_ok=True)
