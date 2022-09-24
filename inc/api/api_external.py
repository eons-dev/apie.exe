import os
import logging
import apie
import requests

# External Endpoints make a request to another server and return the result.
class external(apie.Endpoint):
    def __init__(this, name="external"):
        super().__init__(name)

        this.requiredKWArgs.append('url')
        
        this.optionalKWArgs['method'] = "get"
        this.optionalKWArgs['authenticator'] = ""
        this.optionalKWArgs['data_map'] = None
        this.optionalKWArgs['headers'] = {}
        this.optionalKWArgs['data'] = {}
        this.optionalKWArgs['files'] = {}

        this.externalResponse = None

        this.helpText = '''\
Make a request to an external web endpoint.
This will:
    1. Map data from variables into fields for the request body per the 'data_map'
    2. Make an internal request dictionary called 'externalRequest'
    3. If possible, authenticate that request via the Authenticator set in 'authenticator'
    4. If the request was authenticated, the request will be made and the result will be stored in the response.

When sending the response, the result is decoded as ascii. This means sending binary files will require a base64 encoding, etc.
'''

    def MapData(this):
        if (this.data_map is None):
            return

        for key, val in this.data_map:
            this.data.update({key: this.Fetch(val)})

    def ConstructRequest(this):
        this.externalRequest = {
            'method': this.method,
            'url': this.url,
            'headers': this.headers,
            'data': this.data,
            'files': this.files
        }

    def AuthenticateRequest(this):
        if (not this.authenticator):
            return True

        # TODO: cache auth??
        auth = this.exeutor.GetRegistered(this.authenticator, "auth")
        return auth(this.externalRequest)

    def MakeRequest(this):
        this.externalResponse = requests.request(**this.externalRequest)

    def Call(this):
        this.MapData()
        this.ConstructRequest()
        this.MakeRequest()
        this.response['code'] = this.externalResponse.status_code
        this.response['headers'] = this.externalResponse.headers 
        this.response['files'] = this.externalResponse.headers ##########################
        this.response['content_string'] = this.externalResponse.content.decode('ascii')
