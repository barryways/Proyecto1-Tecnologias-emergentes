import logging
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")
_logger = logging.getLogger(__name__)

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    code: int

    @classmethod
    def ok(cls, data: T, message: str = "OK"):
        return cls(success=True, message=message, data=data, code=200)

    @classmethod
    def error(
            cls,
            message: str,
            method: str,
            code: int,
            e: Exception,
        ):
        _logger.error(f"- en <{method}>, excepcion: {e}>")
        return cls(success=False, message=message, data=None, code=code)