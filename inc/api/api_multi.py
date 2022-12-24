import os
import logging
import json
import apie

# The multi Endpoint allows calling the same requested series several times, each with a different prefix appended to each Fetched variable.
# Currently, multi only allows variables to be Fetched differently between each call. No methods or logic may be propagated between calls.
class multi(apie.Endpoint):
	def __init__(this, name="multi"):
		super().__init__(name)

		# The domain defines what to vary along.
		# This should be a [] list.
		# Each entry in the domain will be appended to the Fetch requests of the current call.
		# For example if our domain is ['public', 'private'], an Endpoint following *this could Fetch 'url' from its precursor (*this); *this would then Fetch 'public_url' for the first call and 'private_url' for the second.
		this.requiredKWArgs.append('domain')

		# True if return status for each call should be included in the results.
		this.optionalKWArgs['forward_returns'] = True

		# What should the return value be by default?
		# Options are 'list' or 'dict' (or some subclass thereof)
		this.optionalKWArgs['combine_as'] = 'list'

		# True means a return of [a, b], [c, d] would become [a, b, c, d]
		# False means a return of [a, b], [c, d] would be left as [ [a, b], [c, d] ]
		# Only applicable if the mimetype of any return is 'application/json'
		# NOTE: only works if 'combine_as' is 'list'.
		this.optionalKWArgs['join_lists'] = True
		
		# If the same value is returned for multiple calls, do we return just the first (True) or all (False)?
		# NOTE: only works if 'combine_as' is 'list'.
		this.optionalKWArgs['prevent_duplicates'] = True

		# Internal vars
		this.cursor = None
		this.calling = False

	# Required Endpoint method. See that class for details.
	def GetHelpText(this):
		return f'''\
Combine the results of multiple JSON API calls into a single response.

Will call:
{this.Fetch('call')}
'''

	# Override Initialize to reset values
	def Initialize(this):
		super().Initialize()
		this.cursor = None
		this.calling = False


	def Call(this):
		this.calling = True

		returns = {}

		for element in this.domain:

			this.cursor = element

			# ret is a Flask Response object
			ret = this.executor.ProcessEndpoint(element, this.request, precursor=this)
			
			returns[element] = {
				'path': f"{element}/{'/'.join(this.next)}",
				'code': ret.status,
				'mime': ret.headers["Content-Type"],
				'raw': ret
			}

		combinedJson = eval(f"{this.combine_as}()")

		for element, ret in returns.items():
			if (ret['mime'] == 'application/json'):
				contentJson = json.loads(ret['raw'].data)
				if (isinstance(combinedJson, list)):
					if (this.join_lists):
						combinedJson += list(contentJson)
					else:
						combinedJson.append(list(contentJson))
				elif (isinstance(combinedJson, dict)):
					combinedJson.update(contentJson)
			else:
				# TODO: This handling can be improved. For instance, removing duplicate files is gonna be a lot of work.
				if (isinstance(combinedJson, list)):
					combinedJson.append(ret['raw'].data)
				elif (isinstance(combinedJson, dict)):
					combinedJson[element] = ret['raw'].data

		if (this.prevent_duplicates):
			combinedJson = list(set(combinedJson))

		if (this.forward_returns):
			returnKeys = ['path', 'code']
			rets = [{key: r[key] for key in returnKeys}.update({'headers': r['raw'].headers}) for r in returns.values()]

			if (isinstance(combinedJson, list)):
				combinedJson.append(rets)
			elif (isinstance(combinedJson, dict)):
				combinedJson['returns'] = rets

		this.response['content_data'] = combinedJson

		this.calling = False


	# Override Fetch to append the cursor to each query.
	# However, we only want to add this functionality AFTER we've Fetched the args for *this, i.e. only when downstream Endpoints call precursor.Fetch().
	# If the cursor prefixed query fails, return the unmodified Fetch call.
	def Fetch(this, varName, default=None, fetchFrom=None, start=True, attempted=None):
		if (this.calling):
			if (start):
				logging.debug(f"Fetching {varName} from {fetchFrom}...")
			val, success = super().Fetch(f"{this.cursor}_{varName}", default, fetchFrom, False, attempted)
			if (success):
				return val
			return super().Fetch(varName, default, fetchFrom, False, attempted)
		else:
			return super().Fetch(varName, default, fetchFrom, start, attempted)
