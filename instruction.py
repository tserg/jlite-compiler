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
        instruction: Optional[str]='',
        parent: Optional["Instruction"]=None,
        child: Optional["Instruction"]=None
    ) -> None:
        self.line_no = line_no
        self.assembly_code = instruction
        self.child = child
        self.parent = parent

    def set_instruction(
        self,
        assembly_code: str
    ) -> None:
        self.assembly_code = assembly_code

    def set_child(self, instruction: "Instruction") -> None:
        self.child = instruction

    def insert_child(self, instruction: "Instruction") -> None:
        current_child = self.child

        self.child = instruction
        instruction.set_parent(self)

        instruction_last_child = instruction.get_last_child()

        instruction_last_child.set_child(current_child)
        current_child.set_parent(instruction_last_child)

    def set_parent(self, instruction: "Instruction") -> None:
        self.parent = instruction

    def get_last_child(self) -> "Instruction":
        if not self.child:
            return self

        return self.child.get_last_child()

    def pretty_print(self) -> None:
        sys.stdout.write(self.assembly_code)

        if self.child:
            self.child.pretty_print()
