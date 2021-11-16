import sys

from typing import (
    Tuple,
)

from ir3 import (
    CMtd3Node,
    GoTo3Node,
    Label3Node
)

from instruction import (
    Instruction,
    MoveRegisterInstruction,
    LabelInstruction,
    LoadInstruction,
    StoreInstruction,
    UnconditionalBranchInstruction,
)

class PeepholeOptimizer:

    debug: bool

    def __init__(
        self,
        debug: bool=False
    ) -> None:

        self.debug = debug

    '''
    def _peephole_optimize_ir3_pass(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        completed = False
        current_stmt = cmtd3_node.statements
        previous_stmt = cmtd3_node.statements

        if self.debug:
            sys.stdout.write("Peephole optimisation - IR3.\n")

        while not completed:

            if not current_stmt:
                completed = True
                break

            if self.debug:
                sys.stdout.write("Peephole optimisation - IR3: " + \
                    str(type(current_stmt)) + "\n")

            if type(previous_stmt) == GoTo3Node and \
                type(current_stmt) != Label3Node:

                # If the previous statement is an unconditional branch
                # and the current statement is not a label, then it is
                # unreachable

                if self.debug:
                    sys.stdout.write("Peephole optimisation - Unreachable post branch.\n")

                if current_stmt.child:

                    previous_stmt.add_child(current_stmt.child)

                else:
                    previous_stmt.child=None

            else:
                previous_stmt = current_stmt

            current_stmt = current_stmt.child
    '''

    def _eliminate_redundant_ldr_str(
        self,
        current_instruction: "Instruction",
        previous_instruction: "Instruction",
        previous_instruction_parent: "Instruction",
    ) -> Tuple["Instruction", "Instruction", "Instruction"]:

        if (type(current_instruction) == LoadInstruction and \
            type(previous_instruction) == StoreInstruction and \
            current_instruction.__str__()[3:] == previous_instruction.__str__()[3:]) or \
            (type(current_instruction) == LoadInstruction == 'ldr' and \
            type(previous_instruction) == LoadInstruction == 'ldr' and \
            type(previous_instruction_parent) == StoreInstruction == 'str' and \
            current_instruction.__str__()[3:] == previous_instruction_parent.__str__()[3:]):

            # Check for immediate load stores

            if self.debug:
                sys.stdout.write("Peephole optimisation - Redundant immediate ldr str detected.\n")

            # Link previous instruction to the child of current instruction

            next_instruction = current_instruction.child

            previous_instruction.set_child(next_instruction)
            next_instruction.set_parent(previous_instruction)
            current_instruction = next_instruction
            previous_instruction_parent = previous_instruction

        elif current_instruction.assembly_code == 'stmfd sp!,{a1,a2,a3,a4}\n' and \
            previous_instruction.assembly_code == 'ldmfd sp!,{a1,a2,a3,a4}\n':

            if self.debug:
                sys.stdout.write("Peephole optimisation - Redundant ldr str of args detected.\n")

            previous_instruction_parent.set_child(current_instruction.child)
            current_instruction.child.set_parent(previous_instruction_parent)

            current_instruction = current_instruction.child

            return (
                current_instruction,
                previous_instruction_parent,
                previous_instruction_parent.parent
            )

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

        if type(instruction) == MoveRegisterInstruction and \
            instruction.rd == instruction.rn:

            current_instruction_parent = instruction.parent
            current_instruction_child = instruction.child

            current_instruction_parent.set_child(current_instruction_child)
            current_instruction_child.set_parent(current_instruction_parent)

            return current_instruction_child

        return instruction

    def _eliminate_unreachable_post_branch(
        self,
        current_instruction: "Instruction",
        previous_instruction: "Instruction"
    ) -> "Instruction":

        if type(previous_instruction) == UnconditionalBranchInstruction and \
            type(current_instruction) != LabelInstruction:

            current_instruction_child = current_instruction.child

            previous_instruction.set_child(current_instruction_child)
            current_instruction_child.set_parent(previous_instruction)

            if self.debug:
                sys.stdout.write("Peephole optimisation - Unreachable instruction detected.\n")
                sys.stdout.write("Previous instruction: " + previous_instruction.__str__() + "\n")
                sys.stdout.write("Current instruction: " + current_instruction.__str__() + "\n")

            return current_instruction_child

        return current_instruction

    def _eliminate_jump_to_next_instruction(
        self,
        current_instruction: "Instruction",
        previous_instruction: "Instruction",
        previous_instruction_parent: "Instruction"
    ) -> Tuple["Instruction", "Instruction"]:

        if type(previous_instruction) == UnconditionalBranchInstruction:

            if type(current_instruction) == LabelInstruction:

                if self.debug:
                    sys.stdout.write("Peephole optimisation: checking for jump: \n")
                    sys.stdout.write("Previous instruction: " + \
                        previous_instruction.__str__())
                    sys.stdout.write("Current instruction: " + \
                        current_instruction.__str__() + "\n")


                if previous_instruction.label == current_instruction.label:

                    previous_instruction_parent.set_child(current_instruction)
                    current_instruction.set_parent(previous_instruction_parent)

                    previous_instruction = previous_instruction_parent
                    previous_instruction_parent = previous_instruction_parent.parent

                    if self.debug:
                        sys.stdout.write("Peephole optimisation - Jump to next instruction detected.\n")

        return (
            previous_instruction,
            previous_instruction_parent
        )

    def peephole_optimize_assembly_pass(
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

            current_instruction = self._eliminate_unreachable_post_branch(
                current_instruction,
                previous_instruction
            )

            previous_instruction, \
            previous_instruction_parent = self._eliminate_jump_to_next_instruction(
                current_instruction,
                previous_instruction,
                previous_instruction_parent
            )

            current_instruction, \
            previous_instruction, \
            previous_instruction_parent = self._eliminate_redundant_ldr_str(
                current_instruction,
                previous_instruction,
                previous_instruction_parent
            )
