import sys

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
