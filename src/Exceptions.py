# All APIer errors
class APIError(Exception): pass


# Exception used for miscellaneous API errors.
class OtherAPIError(APIError): pass