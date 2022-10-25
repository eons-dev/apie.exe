import eons
import os
import logging
import shutil
import jsonpickle
from pathlib import Path
from flask import request, Response
from .Exceptions import *

# APIE Functors extend Eons Functors in order to:
# 1. Improve Fetch() behavior when cascading multiple Functor executions.
# 2. Allow Fetching from a http request.
class Functor(eons.Functor):
	def __init__(this, name=eons.INVALID_NAME()):
		super().__init__(name)

		this.enableRollback = False

		# Default places to Fetch from.
		# Add to this list when extending Fetch().
		# Remove from this list to restrict Fetching behavior.
		# Reorder this list to make Fetch more efficient for your use case.
		# Also see FetchWith and FetchWithout for ease-of-use methods.
		this.fetchFrom = [
			'this',
			'args',
			'precursor',
			'request_args',
			'request_form',
			'request_json',
			'request_files',
			'executor',
			'environment',
		]

		# The request object to process
		this.request = None


	# Grab any known and necessary args from this.kwargs before any Fetch calls are made.
	# There should always be a request.
	def ParseInitialArgs(this):
		super().ParseInitialArgs()
		if (this.precursor):
			this.request = this.precursor.request
		else:
			this.request = this.kwargs.pop('request')


	def FetchFromRequest(this, field, varName, default):
		val = getattr(this.request, field).get(varName)
		if (val is not None):
			return val, True
		return default, False


	def fetch_location_request_args(this, varName, default, fetchFrom, attempted):
		return this.FetchFromRequest('args', varName, default)


	def fetch_location_request_form(this, varName, default, fetchFrom, attempted):
		if (not this.request.data):
			return default, False
		return this.FetchFromRequest('form', varName, default)


	def fetch_location_request_json(this, varName, default, fetchFrom, attempted):
		if (this.request.content_type != "application/json"):
			return default, False
		return this.FetchFromRequest('json', varName, default)


	def fetch_location_request_files(this, varName, default, fetchFrom, attempted):
		if (not this.request.files):
			return  default, False
		return this.FetchFromRequest('files', varName, default)
