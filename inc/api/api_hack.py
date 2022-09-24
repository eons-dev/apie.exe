import os
import logging
import apie

# Hacking allows you to change the behavior of other Endpoints.
# This is similar to test mocking and is likewise useful for testing and debugging.
# Actual features coming soon.
class hack(apie.Endpoint):
    def __init__(this, name="hack"):
        super().__init__(name)

    def Call(this):
        this.response['content_data'] |= {"server": "hacked"}

        #TODO...
