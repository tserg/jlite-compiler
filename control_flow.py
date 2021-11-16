import sys

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from ir3 import (
    CMtd3Node,
    IfGoTo3Node,
    GoTo3Node,
    Label3Node,
    Assignment3Node,
    IR3Node,
    VarDecl3Node,
    RelOp3Node,
    BinOp3Node,
    PrintLn3Node,
)

from jlite_type import (
    BasicType
)

class ControlFlowGenerator:

    debug: bool
    optimize: bool

    instruction_count: int

    basic_block_count: int
    label_to_block: Dict[int, int]
    bb_edges: Dict[Optional[int], List[Union[int, str, Tuple[Any, Any]]]]

    var_decl: Set[str]

    def __init__(
        self,
        debug: bool=False,
        optimize: bool=False
    ):

        self.debug = debug
        self.optimize = optimize

        self.var_decl = set()

        self.instruction_count = 0

        self.bb_edges = {}
        self.label_to_block = {}

    def _reset(self) -> None:

        self.var_decl = set()

        self.instruction_count = 0
        self.bb_edges = {}
        self.label_to_block = {}

    def _label_md_line_no(
        self,
        stmt: Any
    ) -> None:

        self.instruction_count += 1
        stmt.set_md_line_no(
            self.instruction_count
        )

    def _initialise_var_decl(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        var_decl_completed = False
        current_var_decl = cmtd3_node.variable_declarations

        while not var_decl_completed:

            if not current_var_decl:
                var_decl_completed = True
                break

            self.var_decl.add(current_var_decl.value)

            current_var_decl = current_var_decl.child

    def _add_var_decl(
        self,
        stmt: Any
    ) -> None:

        if type(stmt) == VarDecl3Node:
            self.var_decl.add(stmt.value)

    def _label_ir3_nodes(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        self.instruction_count = 0

        completed = False
        current_stmt = cmtd3_node.statements

        while not completed:

            if not current_stmt:
                completed = True
                break

            self._label_md_line_no(current_stmt)

            if self.debug:
                sys.stdout.write("Control flow - Labelling IR3: " + \
                    str(self.instruction_count) + "\n")

            self._add_var_decl(current_stmt)

            current_stmt = current_stmt.child

        if self.debug:
            sys.stdout.write("Control flow - Var decl: " + \
                str(self.var_decl) + "\n")

    def _label_basic_blocks(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        self.basic_block_count = 1
        self.bb_edges = {1: []}

        current_block_line_no = 1

        completed = False
        current_stmt = cmtd3_node.statements
        previous_stmt = None

        while not completed:

            if not current_stmt:
                completed = True
                break

            if type(current_stmt) == Label3Node and \
                type(previous_stmt) not in [IfGoTo3Node, GoTo3Node]:
                self.basic_block_count += 1
                current_block_line_no = 1
                self.bb_edges[self.basic_block_count] = []

            current_stmt.set_md_basic_block_no(
                self.basic_block_count
            )

            current_stmt.set_md_basic_block_line_no(
                current_block_line_no
            )

            current_block_line_no += 1

            if type(current_stmt) == Label3Node:
                self.label_to_block[current_stmt.label_id] = self.basic_block_count

            if self.debug:
                sys.stdout.write("Control flow - Labelling basic blocks - Line no " + \
                    str(current_stmt.md_line_no) + " is assigned to basic block " + \
                    str(current_stmt.md_basic_block_no) + " with basic block line no " + \
                    str(current_stmt.md_basic_block_line_no) + "\n")


            if type(current_stmt) in [
                IfGoTo3Node,
                GoTo3Node,
            ]:

                self.basic_block_count += 1
                current_block_line_no = 1
                self.bb_edges[self.basic_block_count] = []

            previous_stmt = current_stmt
            current_stmt = current_stmt.child

        if self.debug:
            sys.stdout.write("Control flow - Initialise bb_edges: " + \
                str(self.bb_edges) + "\n")

    def _derive_edges(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        completed = False
        current_stmt = cmtd3_node.statements

        while not completed:

            if not current_stmt:
                completed = True
                break

            try:
                next_block_no = current_stmt.child.md_basic_block_no

            except:
                next_block_no = current_stmt.md_basic_block_no

            if current_stmt.md_basic_block_no != next_block_no or \
                not current_stmt.child:

                # Current statement is last statement of basic block

                if type(current_stmt) == IfGoTo3Node:

                    # Link to both conditional flows
                    self.bb_edges[current_stmt.md_basic_block_no].append(
                        self.label_to_block[current_stmt.goto]
                    )

                    if current_stmt.child:
                        self.bb_edges[current_stmt.md_basic_block_no].append(
                            current_stmt.child.md_basic_block_no
                        )


                elif type(current_stmt) == GoTo3Node:

                    # Link to branch flow
                    self.bb_edges[current_stmt.md_basic_block_no].append(
                        self.label_to_block[current_stmt.goto]
                    )

                else:

                    # Link to next statement
                    if current_stmt.child:
                        self.bb_edges[current_stmt.md_basic_block_no].append(
                            current_stmt.child.md_basic_block_no
                        )



            current_stmt = current_stmt.child

        if self.debug:
            sys.stdout.write("Control flow - Deriving edges: " + \
                str(self.bb_edges) + "\n")

    def _annotate_def_use(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        pass

    def _optimize_algebraic_identities(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        # x + 0 = 0 + x = x
        # x * 1 = 1 * x = x
        # x - 0 = x
        # x/1 = x - not implemented since division is not handled

        completed = False
        current_stmt = cmtd3_node.statements

        while not completed:

            if not current_stmt:
                completed = True
                break

            if type(current_stmt) == Assignment3Node:

                assigned_value = current_stmt.assigned_value

                if type(assigned_value) == BinOp3Node and \
                    assigned_value.type == BasicType.INT:

                    if assigned_value.operator in ["+", "*", "-"]:

                        if assigned_value.left_operand_is_raw_value:

                            try:
                                left_operand_value = assigned_value.left_operand.value

                            except:
                                left_operand_value = assigned_value.left_operand


                            if (assigned_value.operator == "+" and \
                                left_operand_value == "0") or \
                                (assigned_value.operator == "*" and \
                                left_operand_value == "1"):

                                current_stmt.assigned_value = assigned_value.right_operand

                        elif assigned_value.right_operand_is_raw_value:

                            try:
                                right_operand_value = assigned_value.right_operand.value

                            except:
                                right_operand_value = assigned_value.right_operand

                            if ((assigned_value.operator == "+" or \
                                assigned_value.operator == "-") and \
                                right_operand_value == "0") or \
                                (assigned_value.operator == "*" and \
                                right_operand_value == "1"):

                                current_stmt.assigned_value = assigned_value.left_operand

            current_stmt = current_stmt.child

    def _annotate_int_constants_and_propagate(
        self,
        cmtd3_node: "CMtd3Node"
    ):

        # Naive implementation of constant propagation within a basic block
        # Replaces load instruction with move instruction

        completed = False
        current_stmt = cmtd3_node.statements
        previous_stmt = cmtd3_node.statements

        current_block_values: Dict[str, Set[str]] = {x: set() for x in self.var_decl}

        while not completed:

            if not current_stmt:
                completed = True
                break

            if current_stmt.md_basic_block_no != previous_stmt.md_basic_block_no:
                # Reset block values if moving to next block
                current_block_values = {x: set() for x in self.var_decl}

            try:
                if type(current_stmt) == Assignment3Node:

                    if self.debug:
                        sys.stdout.write(str(current_block_values) + "\n")

                    # Annotate constant
                    if current_stmt.assigned_value_is_raw_value:

                        if self.debug:
                            sys.stdout.write(str(current_block_values[current_stmt.identifier]) + "\n")

                        current_block_values[current_stmt.identifier].add(
                            current_stmt.assigned_value
                        )

                        if self.debug:

                            sys.stdout.write("Constant value added for: " + \
                                current_stmt.identifier + " with value: " + \
                                str(current_stmt.assigned_value) + "\n")
                            sys.stdout.write(str(current_block_values) + "\n")

                    else:

                        current_block_values[current_stmt.identifier] = set('T')

            except:
                # Ignore class attributes
                pass

            # Replace with constant

            if current_stmt.type == BasicType.INT:
                if type(current_stmt) == PrintLn3Node:

                    if self.debug:
                        sys.stdout.write("Checking constant for println3node with expression: " + \
                            str(current_stmt.expression) + "\n")

                    try:
                        constant_values = current_block_values[current_stmt.expression]

                        if self.debug:
                            sys.stdout.write("Constant value(s) found for println3node: " + \
                                str(constant_values) + "\n")

                        if len(constant_values) == 1:

                            constant_value = constant_values.pop()

                            if constant_value != 'T':

                                if self.debug:
                                    sys.stdout.write("Propagating constant for println3node: " + \
                                        str(constant_value) + "\n")

                                current_stmt.expression = constant_value
                                current_stmt.is_raw_value = True

                    except:
                        pass

            # Continue loop
            previous_stmt = current_stmt
            current_stmt = current_stmt.child

        if self.debug:
            sys.stdout.write("Annotating constants: " + str(current_block_values) + "\n")
            cmtd3_node.pretty_print()


    def generate_basic_blocks(
        self,
        cmtd3_node: "CMtd3Node"
    ) -> None:

        if self.debug:
            sys.stdout.write("Generating basic blocks for control flow.\n")

        self._reset()

        self._initialise_var_decl(cmtd3_node)
        self._label_ir3_nodes(cmtd3_node)
        self._label_basic_blocks(cmtd3_node)
        self._derive_edges(cmtd3_node)

        if self.optimize:

            self._annotate_int_constants_and_propagate(cmtd3_node)
            self._optimize_algebraic_identities(cmtd3_node)

            self._reset()

            self._initialise_var_decl(cmtd3_node)
            self._label_ir3_nodes(cmtd3_node)
            self._label_basic_blocks(cmtd3_node)
            self._derive_edges(cmtd3_node)
