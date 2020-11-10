class XimilarClientException(Exception):
    def __init__(self, code, msg=None):
        Exception.__init__(self, msg)

        self.code = code
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class XimilarClientInvalidDataException(XimilarClientException):
    """
    Raised when invalid input data occur
    """

    def __init__(self, msg=None):
        super().__init__(400, msg or "Invalid data")
