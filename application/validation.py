class BusinessValidationError(Exception):
    def __init__(self, status_code, error_code, error_message):
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(self.error_message)
