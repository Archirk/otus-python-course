class ValidationError(Exception):
    def __init__(self, msg):
        super(ValidationError, self).__init__(msg)
