import sys

from typing import (
    Optional,
)

class Instruction:

    line_no: int
    parent: Optional["Instruction"]
    child: Optional["Instruction"]
    assembly_code: str

    def __init__(
        self,
        line_no: int,
        parent: Optional["Instruction"]=None,
        child: Optional["Instruction"]=None
    ) -> None:
        self.line_no = line_no
        self.assembly_code = ''

    def set_instruction(
        self,
        assembly_code: str
    ) -> None:
        self.assembly_code = assembly_code

    def pretty_print(self) -> None:
        sys.stdout.write(self.assembly_code)
        sys.stdout.write("\n")
