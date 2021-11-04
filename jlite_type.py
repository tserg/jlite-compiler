from enum import Enum

from typing import (
    Any,
    Dict,
    List,
)

class TypeCheckError(Exception):
    """
    Exception class for errors encountered while type checking.

    ...

    Attributes
    ----------
    expression: str
    message: str

    """
    def __init__(
        self,
        expression: str,
        additional_message: str=''
    ) -> None:
        self.expression = expression
        self.message = "Type check error: "
        self.additional_message = additional_message

    def __str__(self) -> str:

        return f'{self.message} {self.expression}. {self.additional_message}'

class BasicType(Enum):
    """
    Type class for basic types
    """

    INT = 'Int'
    BOOL = 'Bool'
    STRING = 'String'
    VOID = 'Void'
    OBJECT = 'Object'

    def __str__(self) -> str:
        return str(self.value)

class FunctionType():
    """
    Type class for function types

    ...

    Attributes
    ----------
    basic_type_list: List[Any]

    """

    # List of basic types that are taken as arguments
    class_name: str
    basic_type_list: List[Any]
    return_type: Any

    def __init__(
        self,
        class_name: str,
        basic_type_list: List[Any],
        return_type: Any
    ) -> None:
        self.class_name = class_name
        self.basic_type_list = basic_type_list
        self.return_type = return_type

TYPE_CONVERSION_DICT: Dict[str, "BasicType"] = {
    'Int': BasicType.INT,
    'Bool': BasicType.BOOL,
    'String': BasicType.STRING,
    'Void': BasicType.VOID,
}
