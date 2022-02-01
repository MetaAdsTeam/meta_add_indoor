class APIError(Exception):
    """Raised when API error occurs."""

    def __init__(self, message: str, code: int = 400, error_type: str = None):
        self.message = message
        self.code = code
        self.error_type = error_type
