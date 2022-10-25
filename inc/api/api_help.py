import os
import logging
import apie

class help(apie.Endpoint):
	def __init__(this, name="Help for preceding API Endpoint"):
		super().__init__(name)

		this.mime = 'application/json'

	# Required Endpoint method. See that class for details.
	def Call(this):
		this.cacheable = this.precursor.cacheable #cacheable is automatically added to the response
		this.response.content.data.update({
			"endpoint": this.precursor.name,
			"supported_methods": this.precursor.supportedMethods,
			"allowed_next": this.precursor.allowedNext,
			"required_args": this.precursor.requiredKWArgs,
			"optional_args": this.precursor.optionalKWArgs,
			"get_args_from": this.precursor.fetchFrom,
			"help_text": this.precursor.GetHelpText()
		})

	# Override of eons.Functor method. See that class for details
	def Function(this):
		this.ResetResponse()
		this.Call()
		return this.ProcessResponse()
