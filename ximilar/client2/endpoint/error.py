"""Module defines error specific to Ximilar endpoints"""


class Error(Exception):
    """
    Wrapper for XimilarEndpoint errors.
    """

    def __init__(self, message: str, /, *, code: int = None, body: str = None):
        super().__init__(message)
        self.code = code
        self.body = body

    @staticmethod
    def token_missing():
        """We can't really do anything without a token"""
        return Error("token or jwttoken must be present")

    @staticmethod
    def content_type(content_type):
        """XimilarEndpoint always expects JSON and it was not it."""
        return Error(f"Unexpected response content type: {content_type}")

    @staticmethod
    def http_error(code, body):
        """There was an error we don't know how to interpret."""
        return Error(f"Error returned from HTTP layer: {code}", code=code, body=body)
