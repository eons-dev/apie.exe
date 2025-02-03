import os
import logging
import apie

# Hacking allows you to change the behavior of other Endpoints.
# This is similar to test mocking and is likewise useful for testing and debugging.
class hack(apie.Endpoint):
	def __init__(this, name="hack"):
		super().__init__(name)

		this.allowedNext = [] # all.

	# Required Endpoint method. See that class for details.
	def GetHelpText(this):
		return '''\
The quieter you are, the more you are able to hear.
'''

	# Required Endpoint method. See that class for details.
	def Call(this):
		setFrom = ['args']
		if (this.request.content_type == "application/json"):
			setFrom.append('json')
		elif (this.request.data):
			setFrom.append('forms')

		for set in setFrom:
			for key, val in getattr(this.request, set).to_dict():
				this.Set(key, val) # will log.

	# Ensure the hacked Endpoint uses what we've set here.
	def CallNext(this):
		next = this.next.pop(0)
		endpoint = this.executor.GetRegistered(next, "api")
		originalFetchFrom = endpoint.fetchFrom

		# Move precursor to the top, so that we can make the next Endpoint Fetch our hacked values.
		try:
			endpoint.fetchFrom.remove('precursor')
		except:
			# Ignore key errors, etc.
			pass
		endpoint.fetchFrom = ['precursor'].extend(endpoint.fetchFrom)

		this.executor.cachedFunctors.update({next: endpoint})

		ret = None
		try:
			ret = this.executor.ProcessEndpoint(next, this.request, precursor=this, next=this.next)
		except Exception as e:
			ret = None
			this.response.content.message = f"Hack failed: {str(e)}"
			this.response.code = 401
		endpoint.fetchFrom = originalFetchFrom
		if (ret is not None):
			return ret
		return this.ProcessResponse()
