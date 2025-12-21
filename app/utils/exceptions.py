from fastapi import HTTPException, status

class BaseAppException(HTTPException):
    status_code = 500
    detail = ""
    def __init__(self, msg=None):
        if msg:
            self.detail = msg
        super().__init__(status_code=self.status_code, detail=self.detail)

class AlreadyExistsException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists in database"

class ExternalAPIErrorException(BaseAppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "External API error"

class FailedOperationException(BaseAppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Operation failed"

class UserNotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"

class InvalidSignatureException(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid signature"

class UnauthorizedException(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Unauthorized"

class ResourceDeletedException(BaseAppException):
    status_code = status.HTTP_204_NO_CONTENT
    detail = "Resource deleted"

class ResourceNotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"

class NotAllowedException(BaseAppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Operation not allowed"

class InvalidDataException(BaseAppException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid data provided"

class AuthenticationFailedException(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication failed"

class UsernameGenerationFailedException(BaseAppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Failed to generate unique username"

class ForbiddenException(BaseAppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Forbidden"

class CustomLeagueException(BaseAppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "User can create only one USER custom league"
