import sys

from typing import (
    Optional,
)

DUAL_OP = {
    '+': 'add ',
    '-': 'sub ',
    '*': 'mul ',
    '||': 'orr ',
    '&&': 'and ',
}

REL_OP = {
    '>': 'bgt ',
    '>=': 'bge ',
    '<': 'blt ',
    '<=': 'ble ',
    '==': 'beq ',
    '!=': 'bne '
}

class Instruction:

    line_no: Optional[int]
    parent: Optional["Instruction"]
    child: Optional["Instruction"]
    assembly_code: Optional[str]

    rd: Optional[str]
    rm: Optional[str]
    rn: Optional[str]
    immediate: Optional[int]
    offset: Optional[int]
    base_offset: Optional[str]

    def __init__(
        self,
        instruction: Optional[str]=None,
        parent: Optional["Instruction"]=None,
        child: Optional["Instruction"]=None,
        rd: Optional[str]=None,
        rm: Optional[str]=None,
        rn: Optional[str]=None,
        immediate: Optional[int]=None,
        base_offset: Optional[str]=None,
        offset: Optional[int]=None
    ) -> None:
        self.line_no = None
        self.assembly_code = instruction
        self.child = child
        self.parent = parent

        self.rd = rd
        self.rm = rm
        self.rn = rn
        self.immediate = immediate
        self.base_offset = base_offset
        self.offset = offset

    def set_instruction_line_no(self, line_no: int) -> None:

        self.line_no = line_no

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

        if self.assembly_code:
            sys.stdout.write(self.assembly_code)

        else:

            sys.stdout.write(self.__str__())
            sys.stdout.write("\n")

        if self.child:
            self.child.pretty_print()

    def __str__(self) -> str:

        return self.assembly_code

class LabelInstruction(Instruction):

    label: str

    def __init__(
        self,
        label: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.label = label

    def __str__(self) -> str:

        result = self.label + ":"

        return result

    def pretty_print(self) -> None:

        sys.stdout.write("\n")
        sys.stdout.write(self.__str__())
        sys.stdout.write("\n")

        if self.child:
            self.child.pretty_print()

class BranchInstruction(Instruction):

    label: str

    def __init__(
        self,
        label: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.label = label

class UnconditionalBranchInstruction(BranchInstruction):

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "b " + self.label
        return result

class ConditionalBranchInstruction(BranchInstruction):

    operator: str

    def __init__(
        self,
        operator: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.operator = operator

    def __str__(self) -> str:

        result = REL_OP[self.operator] + self.label
        return result

class BranchLinkInstruction(BranchInstruction):

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "bl " + self.label
        return result

class LoadInstruction(Instruction):

    rd: str
    label: Optional[str]

    def __init__(
        self,
        label: Optional[str]=None,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.label = label

    def __str__(self) -> str:

        result = "ldr " + self.rd + ","

        if self.label:
            result += "=" + self.label

        elif self.base_offset:

            result += "[" + str(self.base_offset)

            if self.offset:
                result += ",#" + str(self.offset) + "]"
            else:
                result += "]"

        return result

class StoreInstruction(Instruction):

    rd: str
    label: Optional[str]

    def __init__(
        self,
        label: Optional[str]=None,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.label = label

    def __str__(self) -> str:

        result = "str " + self.rd + ","

        if self.label:
            result += "=" + self.label

        elif self.base_offset:

            result += "[" + str(self.base_offset)

            if self.offset:
                result += ",#" + str(self.offset) + "]"
            else:
                result += "]"

        return result

class MoveInstruction(Instruction):

    pass

class MoveImmediateInstruction(MoveInstruction):

    rd: str
    immediate: int

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "mov " + self.rd + ",#" + str(self.immediate)

        return result

class MoveNegateInstruction(MoveInstruction):

    rd: str
    rn: str

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "mvn " + self.rd + "," + self.rn
        return result

class MoveNegateImmediateInstruction(MoveInstruction):

    rd: str
    immediate: int

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "mvn " + self.rd + ",#" + str(self.immediate)

        return result

class MoveRegisterInstruction(MoveInstruction):

    rd: str
    rn: str

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "mov " + self.rd + "," + self.rn

        return result

class CompareInstruction(Instruction):

    rd: str

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        if self.rn:
            result = "cmp " + self.rd + "," + self.rn

        else:
            result = "cmp " + self.rd + ",#" + str(self.immediate)

        return result

class DualOpInstruction(Instruction):

    operator: str
    rd: str
    rn: str

    def __init__(
        self,
        operator: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.operator = operator

    def __str__(self) -> str:

        operator = DUAL_OP[self.operator]

        if self.rm:
            result = operator + self.rd + "," + self.rn + "," + self.rm

        elif self.immediate:
            result = operator + self.rd + "," + self.rn + ",#" + str(self.immediate)

        return result

class NegationInstruction(Instruction):

    rd: str
    rn: str

    def __init__(
        self,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:

        result = "neg " + self.rd + "," + self.rn

        return result
