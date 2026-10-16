class GUIException(BaseException):
    pass

class InvalidNameException(BaseException):
    pass

class WikiDatabaseError(Exception):
    pass

class DataIntegrityError(Exception):
    pass

class DataValidationError(Exception):
    pass

class WikiOperationError(Exception):
    pass