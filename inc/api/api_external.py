import os
import logging
import apie
import requests
from urllib.parse import urlparse

# External Endpoints make a request to another server and return the result.
class external(apie.Endpoint):
    def __init__(this, name="external"):
        super().__init__(name)

        this.requiredKWArgs.append('url')
        
        this.optionalKWArgs['method'] = "get"
        this.optionalKWArgs['authenticator'] = ""
        this.optionalKWArgs['query_map'] = None #get parameters
        this.optionalKWArgs['data_map'] = None #request body
        this.optionalKWArgs['headers'] = None #None => request.headers; {} => {}
        this.optionalKWArgs['data'] = {}
        this.optionalKWArgs['files'] = {}
        this.optionalKWArgs['decode'] = 'ascii'

        this.clobberContent = False

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
        this.path = urlparse(this.url).path[1:]

        if (this.data_map):
            for key, val in this.data_map.items():
                this.data.update({key: this.Fetch(val)})
        
        if (this.query_map):
            this.url += '?'
            for key, val in this.query_map.items():
                this.url += f"{key}={this.Fetch(val)}&"
            this.url = this.url[:-1] #trim the last "&"

    def ConstructRequest(this):
        this.externalRequest = {
            'method': this.method,
            'url': this.url,
            'headers': this.headers,
            'data': this.data,
            'files': this.files
        }
        if (this.headers is None):
            this.externalRequest['headers'] = this.request.headers

    def AuthenticateRequest(this):
        if (not this.authenticator):
            return True

        # TODO: cache auth??
        this.auth = this.executor.GetRegistered(this.authenticator, "auth")
        return this.auth(executor=this.executor, path=this.path, request=this.externalRequest, predecessor=this)

    def MakeRequest(this):
        this.externalResponse = requests.request(**this.externalRequest)

    def Call(this):
        this.MapData()
        this.ConstructRequest()
        if (not this.AuthenticateRequest()):

            this.response['content_string'], this.response['code'] = this.auth.Unauthorized(this.path)
            #TODO: Headers?
            return
        this.MakeRequest()
        this.response['code'] = this.externalResponse.status_code
        this.response['headers'] = this.externalResponse.headers 
        if (this.decode):
            this.response['content_string'] = this.externalResponse.content.decode(this.decode)
        else:
            this.response['content_string'] = this.externalResponse.content
