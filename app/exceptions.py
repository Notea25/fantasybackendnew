from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    status_code = 500
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)



class UserAlreadyExists(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "User Already Exists"


class IncorrectEmailOrPassword(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Incorrect Email Or Password"


class TokenExpired(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Token Expired"


class TokenAbsent(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Token Absent"


class IncorrectTokenFormat(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Incorrect Token Format"


class UserAbsent(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "User Absent"


class IncorrectTransaction(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Incorrect Transaction"


class CanNotUpdateBalance(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Can Not Update Balance"

class WrongSignature(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Wrong Signature"

class CanNotCreateAccount(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Can Not Create Account"

class Unauthorized(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Unauthorized"


class Deleted(BaseAppException):
    status_code = status.HTTP_204_NO_CONTENT
    detail = "Deleted"

class IncorrectTransactionId(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Incorrect Transaction Id"

class NotFound(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Not Found"