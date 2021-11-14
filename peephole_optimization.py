import sys

from typing import (
    Tuple,
)

from instruction import (
    Instruction,
)

class PeepholeOptimizer:

    debug: bool

    def __init__(
        self,
        debug: bool=False
    ) -> None:

        self.debug = debug

    def _eliminate_redundant_ldr_str(
        self,
        current_instruction: "Instruction",
        previous_instruction: "Instruction",
        previous_instruction_parent: "Instruction",
    ) -> Tuple["Instruction", "Instruction", "Instruction"]:

        if (current_instruction.assembly_code[:3] == 'ldr' and \
            previous_instruction.assembly_code[:3] == 'str' and \
            current_instruction.assembly_code[3:] == previous_instruction.assembly_code[3:]) or \
            (current_instruction.assembly_code[:3] == 'ldr' and \
            previous_instruction.assembly_code[:3] == 'ldr' and \
            previous_instruction_parent.assembly_code[:3] == 'str' and \
            current_instruction.assembly_code[3:] == previous_instruction_parent.assembly_code[3:]):

            # Check for immediate load stores

            if self.debug:
                sys.stdout.write("Peephole optimisation - Redundant immediate ldr str detected.\n")

            # Link previous instruction to the child of current instruction

            next_instruction = current_instruction.child

            previous_instruction.set_child(next_instruction)
            next_instruction.set_parent(previous_instruction)
            current_instruction = next_instruction
            previous_instruction_parent = previous_instruction

        else:
            previous_instruction_parent = previous_instruction

        previous_instruction = current_instruction
        current_instruction = current_instruction.child

        return (
            current_instruction,
            previous_instruction,
            previous_instruction_parent
        )

    def _eliminate_redundant_mov(
        self,
        instruction: "Instruction"
    ) -> "Instruction":

        if instruction.assembly_code[:3] == "mov" and \
            instruction.assembly_code[4:6] == instruction.assembly_code[7:9]:

            current_instruction_parent = instruction.parent
            current_instruction_child = instruction.child

            current_instruction_parent.set_child(current_instruction_child)
            current_instruction_child.set_parent(current_instruction_parent)

            return current_instruction_child

        return instruction

    def _peephole_optimize_pass(
        self,
        instruction_head: "Instruction"
    ) -> None:

        completed = False
        current_instruction = instruction_head
        previous_instruction = instruction_head
        previous_instruction_parent = instruction_head

        while not completed:

            if not current_instruction:
                completed = True
                break

            current_instruction = self._eliminate_redundant_mov(
                current_instruction
            )

            current_instruction, \
            previous_instruction, \
            previous_instruction_parent = self._eliminate_redundant_ldr_str(
                current_instruction,
                previous_instruction,
                previous_instruction_parent
            )
