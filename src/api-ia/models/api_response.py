from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    code: int

    @classmethod
    def ok(cls, data: T, message: str = "OK"):
        return cls(success=True, message=message, data=data, code=200)

    @classmethod
    def error(cls, message: str, code: int):
        return cls(success=False, message=message, data=None, code=code)