class MissingOptionsException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class InvalidOptionException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class ConflictingEnvironmentsException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors
