import os
import logging
import apie

class test(apie.Endpoint):
    def __init__(this, name="Test API Endpoint"):
        super().__init__(name)

    def Call(this):
        if (not this.next):
            logging.info(f"Final Endpoint got request: {this.request}")
        else:
            logging.info(f"Test preceding {this.next[0]}")

        tthis.response['content_data'] |= {"test:": "Successful!"}
