import os
import sys

from collections import (
    deque,
)

from gen import (
    IR3Generator
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
    TextIO,
    Tuple,
    Union,
)

from instruction import (
    Instruction,
)

from ir3 import (
    IR3Node,
    CMtd3Node,
    PrintLn3Node,
    Assignment3Node,
    VarDecl3Node,
    BinOp3Node,
    CData3Node,
    RelOp3Node,
    Return3Node,
    ClassAttribute3Node,
    ClassInstance3Node,
    MethodCall3Node,
    ReadLn3Node,
    Label3Node,
    IfGoTo3Node,
    GoTo3Node,
    UnaryOp3Node,
)

from jlite_type import (
    BasicType,
)

REGISTERS = ['v1', 'v2', 'v3', 'v4', 'v5']

ARG_REGISTERS = {
    0: 'a1',
    1: 'a2',
    2: 'a3',
    3: 'a4',
}

ARG_REGISTER_TO_STACK_OFFSET = {
    'a1': 0,
    'a2': 4,
    'a3': 8,
    'a4': 12
}

ARITHMETIC_OP = {
    '+': 'add ',
    '-': 'sub ',
    '*': 'mul ',
}

BINARY_OP = {
    '||': 'orr ',
    '&&': 'and ',
}

BOOL_CONVERSION = {
    'true': 'mvn ',
    'false': 'mov ',
}

REL_OP = {
    '>': 'bgt ',
    '>=': 'bge ',
    '<': 'blt ',
    '<=': 'ble ',
    '==': 'beq ',
    '!=': 'bne '
}

class Compiler:
    """
    Compiler instance to generate ARM assembly code from input file
    ...

    Attributes
    ----------
    ir3_generator: IR3Generator
    address_descriptor: Dict[str, List[str]]
    register_descriptor: Dict[str, List[str]]

    Methods
    -------
    _parse_content(f)
        Run the parser through the given file

    """
    optimize: bool

    ir3_generator: "IR3Generator"
    address_descriptor: Dict[str, List[str]]
    register_descriptor: Dict[str, List[str]]

    instruction_head: Optional["Instruction"]
    instruction_data_tail: Optional["Instruction"]
    instruction_tail: Optional["Instruction"]

    instruction_count: int
    data_label_count: int
    branch_count: int

    def __init__(
        self,
        debug: bool=False,
        optimize: bool=False
    ) -> None:

        self.optimize = optimize

        self.ir3_generator = IR3Generator()
        self.debug = debug

        self.instruction_count = self.data_label_count = self.branch_count = 0

        self.instruction_head = self.instruction_data_tail = \
            self.instruction_tail = None

        self.address_descriptor = {}
        self.register_descriptor = {
            'v1': deque(),
            'v2': deque(),
            'v3': deque(),
            'v4': deque(),
            'v5': deque(),
        }

    def _get_incremented_instruction_count(self) -> int:
        self.instruction_count += 1
        return self.instruction_count

    def _update_instruction_line_no(self) -> None:

        current_instruction = self.instruction_head

        old_instruction_count = self.instruction_count

        self.instruction_count = 0

        completed = False

        while not completed:

            if not current_instruction:
                completed = True
                break

            self.instruction_count += 1
            current_instruction.set_instruction_line_no(self.instruction_count)

            current_instruction = current_instruction.child

        if self.debug:
            sys.stdout.write("Updating instruction line numbers.\n")
            sys.stdout.write("Initial count: " + str(old_instruction_count) + "\n")
            sys.stdout.write("Updated count: " + str(self.instruction_count) + "\n")

    def _link_instructions(
        self,
        instructions: List["Instructions"]
    ) -> None:

        for i in range(0, len(instructions)-1):



            current_instruction = instructions[i]
            next_instruction = instructions[i+1]

            if self.debug:
                sys.stdout.write("Linking instructions: " + str(current_instruction.line_no) + \
                " - " + str(next_instruction.line_no) + "\n")

            current_instruction.set_child(next_instruction)
            next_instruction.set_parent(current_instruction)

    def _declare_new_variable(
        self,
        variable_name: str,
        offset: int
    ) -> None:

        if self.debug:
            sys.stdout.write("Adding new variable to address descriptor: " + \
                variable_name + "\n")

        self.address_descriptor[variable_name] = {
            'offset': offset,
            'references': deque()
        }

        if self.debug:
            sys.stdout.write("Current address descriptor: " + \
                str(self.address_descriptor) + "\n")

    def _get_variable_offset(self, identifier: str) -> Optional[int]:

        try:
            offset = self.address_descriptor[identifier]['offset']

        except:

            offset = None

        return offset

    def _get_space_required_for_object(self, class_name: str) -> Optional[int]:

        if self.debug:
            sys.stdout.write("Calculating space required for object of class: " + \
                class_name + "\n")

        completed = False
        current_class_data = self.ir3_generator.ir3_tree.head.class_data

        while not completed:

            if not current_class_data:
                completed = True
                break

            if self.debug:
                sys.stdout.write("Calculating space required for object - Checking class: " + \
                    current_class_data.class_name + "\n")

            if class_name == current_class_data.class_name:

                # Get identifiers of class attributes

                object_attributes = current_class_data.get_var_decl_identifiers()

                return len(object_attributes) * 4

            current_class_data = current_class_data.child

        return None

    def _calculate_class_attribute_offset(
        self,
        ir3_node: Optional[Union[ClassAttribute3Node, IR3Node]]=None,
        class_name: Optional[str]=None,
        attribute_name: Optional[str]=None
    ) -> Optional[int]:

        if type(ir3_node) == ClassAttribute3Node:

            attribute_name = ir3_node.target_attribute
            class_name = ir3_node.class_name

        try:

            completed = False
            current_class_data = self.ir3_generator.ir3_tree.head.class_data

            while not completed:

                if not current_class_data:
                    completed = True
                    break

                if class_name == current_class_data.class_name:

                    # Get identifiers of class attributes

                    object_attributes = current_class_data.get_var_decl_identifiers()

                    if self.debug:

                        sys.stdout.write("Getting class attribute offset - all vars: " + \
                            str(object_attributes) + "\n")

                    offset = 0

                    for a in object_attributes:

                        if a == attribute_name:
                            return offset

                        offset += 4

                current_class_data = current_class_data.child

        except:
            return None

    def _get_md_liveness_data(
        self,
        ir3_node: CMtd3Node,
        md_args: List[str]
    ) -> Dict[str, List[int]]:

        if self.debug:
            sys.stdout.write("Getting liveness data for method: " + \
                str(ir3_node.method_id) + "\n")

        liveness_data = {}
        instruction_count = 0

        completed = False
        current_stmt = ir3_node.statements

        while not completed:

            if not current_stmt:
                completed = True
                break

            instruction_count += 1
            current_stmt.set_md_line_no(instruction_count)

            # Check for statements
            if type(current_stmt) == Assignment3Node:

                identifier = current_stmt.identifier

                identifier_is_arg = self._check_if_in_arguments(
                    identifier,
                    md_args
                )

                if not identifier_is_arg:
                    if identifier in liveness_data:
                        liveness_data[identifier].append(instruction_count)

                    else:
                        liveness_data[identifier] = [instruction_count]

                assigned_value = current_stmt.assigned_value
                assigned_value_is_raw_value = current_stmt.assigned_value_is_raw_value

                if isinstance(assigned_value, IR3Node) == True:

                    if type(assigned_value) in [BinOp3Node, RelOp3Node]:

                        left_operand = assigned_value.left_operand
                        right_operand = assigned_value.right_operand

                        left_operand_is_non_arg_id = self._check_if_in_arguments(
                            left_operand,
                            md_args
                        ) or assigned_value.left_operand_is_raw_value

                        if left_operand_is_non_arg_id:

                            if left_operand in liveness_data:
                                liveness_data[left_operand].append(instruction_count)

                            else:
                                liveness_data[left_operand] = [instruction_count]

                        right_operand_is_non_arg_id = self._check_if_in_arguments(
                            right_operand,
                            md_args
                        ) or assigned_value.right_operand_is_raw_value

                        if right_operand_is_non_arg_id:

                            if right_operand in liveness_data:
                                liveness_data[right_operand].append(instruction_count)

                            else:
                                liveness_data[right_operand] = [instruction_count]

                    else:
                        # Base IR3Node
                        assigned_value_is_raw_value = assigned_value.is_raw_value
                        assigned_value = assigned_value.value

                        assigned_value_is_non_arg_id = self._check_if_in_arguments(
                            assigned_value,
                            md_args
                        ) or assigned_value_is_raw_value

                        if assigned_value_is_non_arg_id:

                            if assigned_value in liveness_data:
                                liveness_data[assigned_value].append(instruction_count)

                            else:
                                liveness_data[assigned_value] = [instruction_count]

                else:

                    assigned_value_is_non_arg_id = self._check_if_in_arguments(
                        assigned_value,
                        md_args
                    ) or assigned_value_is_raw_value

                    if assigned_value_is_non_arg_id:

                        if assigned_value in liveness_data:
                            liveness_data[assigned_value].append(instruction_count)

                        else:
                            liveness_data[assigned_value] = [instruction_count]

            elif type(current_stmt) == PrintLn3Node:

                expression = current_stmt.expression

                expression_is_non_arg_id = self._check_if_in_arguments(
                    expression,
                    md_args
                ) or current_stmt.is_raw_value

                if expression_is_non_arg_id:

                    if expression in liveness_data:
                        liveness_data[expression].append(instruction_count)

                    else:
                        liveness_data[expression] = [instruction_count]

            current_stmt = current_stmt.child

        return liveness_data

    def _check_if_in_register(
        self,
        identifier: str,
        excluded_registers: List[str]=[]
    ) -> Optional[List[Any]]:

        try:
            x_address_descriptor = self.address_descriptor[identifier]['references']
            is_in_register = [i for i in REGISTERS if i in x_address_descriptor and \
                i not in excluded_registers]

            if len(is_in_register) == 0:
                return None

        except:

            is_in_register = None

        return is_in_register

    def _check_if_in_arguments(
        self,
        identifier: str,
        md_args: List[str]
    ) -> Optional[str]:

        if self.debug:
                sys.stdout.write("Checking if identifier [" + str(identifier) + \
                    "] is in arguments: " + str(md_args) + "\n")

        arg_index = [i for i in range(len(md_args)) if md_args[i][0] == identifier]

        if len(arg_index) > 0:
            arg_register = ARG_REGISTERS[arg_index[0]]

            return arg_register

        else:
            return None

    def _check_for_empty_register(
        self,
        excluded_registers: List[str]
    ) -> Optional[str]:

        for k, v in self.register_descriptor.items():

            if k not in excluded_registers:

                if len(v) == 0:

                    if self.debug:
                        sys.stdout.write("Empty register found: " + \
                            str(k) + "\n")

                    return k

        if self.debug:
            sys.stdout.write("No empty registers available.\n")

        return None

    def _check_for_register_with_replaceable_value(
        self,
        excluded_registers: List[str]
    ) -> Optional[str]:

        if self.debug:
            sys.stdout.write("Getting register - Check #1 Alternative locations.\n")

        for k, v in self.register_descriptor.items():

            if k not in excluded_registers:

                for r in v:

                    # Check each reference and see if there is an alternative location

                    try:
                        if len(self.address_descriptor[r]['references']) > 1:

                            if self.debug:
                                sys.stdout.write("Getting register - Check #1 Alternative locations passed.\n")

                            return k

                    except:
                        pass


        return None

    def _check_for_no_subsequent_use(
        self,
        identifier: str,
        current_line_no: int,
        liveness_data: Dict[str, List[int]],
        excluded_registers: List[str]
    ) -> Optional[str]:

        if self.debug:
            sys.stdout.write("Checking register for subsequent use - liveness data received - " + \
                str(liveness_data) + "\n")
            sys.stdout.write("Checking register for subsequent use - Address descriptor - " + \
                str(self.address_descriptor) + "\n")
            sys.stdout.write("Checking register for subsequent use - Register descriptor - " + \
                str(self.register_descriptor) + "\n")

        for k, v in self.register_descriptor.items():

            if k not in excluded_registers:

                for r in v:

                    try:
                        # Try/except to handle key errors for class attributes
                        current_register_value_last_use = max([max(liveness_data[r]) for r in v])

                        if current_line_no > current_register_value_last_use:

                            if self.debug:
                                sys.stdout.write("Value in register not used subsequently. Register found: " + \
                                    str(k) + "\n")

                            return k

                    except:
                        pass

        return None

    def _check_for_equivalent_register(
        self,
        identifier: str,
        other_ref: str,
        other_ref_reg: Optional[str],
        excluded_registers: List[str]
    ) -> Optional[str]:

        if self.debug:
            sys.stdout.write("Checking for equivalent register.\n")

        for k, v in self.register_descriptor.items():

            if k not in excluded_registers and k != other_ref_reg:
                # If current register is not already assigned to
                # y or z

                for r in v:
                    # For each reference pointed to by current register,
                    # check if it has

                    try:
                        # Try/except to handle key errors for class attributes
                        if (v in self.address_descriptor[r]['references'] and \
                            other_ref not in self.address_descriptor[k]['references']):

                            if self.debug:
                                sys.stdout.write("Getting register - Equivalent register found.\n")

                            return k4

                    except:
                        pass

                    # If inner for loop is not exited, assign register

        return None

    def _get_spilled_register(
        self,
        identifier: str,
        current_line_no: int,
        liveness_data: Dict[str, List[int]],
        excluded_registers: List[str]
    ) -> str:

        if self.debug:
            sys.stdout.write("Checking for spilled register.\n")

        min_spill_cost = float("inf")
        min_spill_cost_reg = None

        for k, v in self.register_descriptor.items():

            if k not in excluded_registers:

                total_spill_cost = 0

                for r in v:

                    # For each identifier referenced in the current register,
                    # calculate the number of times it appears in a later instruction

                    current_identifier_liveness = liveness_data[r]
                    subsequent_reference_count = len(
                        [i for i in current_identifier_liveness if i > current_line_no]
                    )
                    total_spill_cost += subsequent_reference_count

                if self.debug:
                    sys.stdout.write("Spill cost of register " + k + ": " + \
                        str(total_spill_cost) + "\n")

                if total_spill_cost < min_spill_cost:
                    min_spill_cost = total_spill_cost
                    min_spill_cost_reg = k

        if self.debug:
            sys.stdout.write("Checking for spilled register - Register obtained: " + \
                min_spill_cost_reg + "\n")

        return min_spill_cost_reg

    def _get_required_registers(
        self,
        ir3_node: Any
    ) -> Dict[str, str]:

        if type(ir3_node) == Assignment3Node:

            is_simple_assignment = ir3_node.assigned_value_is_raw_value

            if type(ir3_node.identifier) == ClassAttribute3Node:

                # Requires two registers
                # 1. x = new Object
                # 2. Base address of object

                # Need to guarantee register for base address of object is different
                # from register for value to assign

                required_registers = {
                    'y': ir3_node.identifier,
                    'z': 'placeholder'
                }

                return required_registers

            elif type(ir3_node.assigned_value) == ClassInstance3Node:

                required_registers = {
                    'x': ir3_node.identifier,
                }

                return required_registers

            elif is_simple_assignment:

                # Only requires one register for x = CONSTANT or x = new Object

                if self.debug:
                    sys.stdout.write("Getting register for plain vanilla node.\n")

                required_registers = {
                    'x': ir3_node.identifier
                }

                return required_registers

            elif type(ir3_node.assigned_value) == BinOp3Node:

                if self.debug:
                    sys.stdout.write("Getting register for binop node.\n")
                    sys.stdout.write("Identifier: " + \
                        str(ir3_node.identifier) + "\n")
                    sys.stdout.write("Left operand: " + \
                        str(ir3_node.assigned_value.left_operand) + "\n")
                    sys.stdout.write("Right operand: " + \
                        str(ir3_node.assigned_value.right_operand) + "\n")

                left_operand_is_raw_value = ir3_node.assigned_value.left_operand_is_raw_value

                y_value = None

                if not left_operand_is_raw_value or \
                    ir3_node.assigned_value.operator == '*':
                    y_value = ir3_node.assigned_value.left_operand

                right_operand_is_raw_value = ir3_node.assigned_value.right_operand_is_raw_value

                z_value = None
                if not right_operand_is_raw_value or \
                    ir3_node.assigned_value.operator == '*':
                    z_value = ir3_node.assigned_value.right_operand

                required_registers = {
                    'x': ir3_node.identifier,
                    'y': y_value,
                    'z': z_value
                }

                return required_registers

            elif type(ir3_node.assigned_value) == RelOp3Node:

                if self.debug:
                    sys.stdout.write("Getting register for relop node.\n")
                    sys.stdout.write("Identifier: " + \
                        str(ir3_node.identifier) + "\n")
                    sys.stdout.write("Left operand: " + \
                        str(ir3_node.assigned_value.left_operand) + "\n")
                    sys.stdout.write("Right operand: " + \
                        str(ir3_node.assigned_value.right_operand) + "\n")

                y_value = ir3_node.assigned_value.left_operand
                z_value = ir3_node.assigned_value.right_operand

                required_registers = {
                    'x': ir3_node.identifier,
                    'y': y_value,
                    'z': z_value
                }

                return required_registers

            else:

                if self.debug:
                    sys.stdout.write("Getting register for assigned value type: " + \
                        str(type(ir3_node.assigned_value)) + "\n")
                    sys.stdout.write("Assigned value: " + str(ir3_node.assigned_value) + "\n")

                # x = y

                if self.debug:
                    sys.stdout.write("Getting register for double identifiers.\n")

                required_registers = {
                    'x': ir3_node.identifier,
                    'y': ir3_node.assigned_value,
                }

        elif type(ir3_node) == Return3Node:

            required_registers = {
                'x': ir3_node.return_value
            }

        elif type(ir3_node) == ClassAttribute3Node:

            required_registers = {
                'x': ir3_node.object_name
            }

        elif type(ir3_node) == ReadLn3Node:

            required_registers = {
                'x': ir3_node.id3
            }

        elif type(ir3_node) == IfGoTo3Node:

            if type(ir3_node.rel_exp) == str:

                # Identifier (no raw values for IR3)
                required_registers = {
                    'y': ir3_node.rel_exp,
                    'z': 'placeholder'
                }

            elif type(ir3_node.rel_exp) == RelOp3Node:

                required_registers = {
                    'y': ir3_node.rel_exp.left_operand,
                    'z': ir3_node.rel_exp.right_operand
                }

            elif type(ir3_node.rel_exp) == IR3Node:

                required_registers = {
                    'y': ir3_node.rel_exp.value,
                    'z': 'placeholder'
                }

        else:
            if self.debug:
                sys.stdout.write("Getting required registers - uncaught situation: " + \
                    str(ir3_node.rel_exp) + "\n")

        return required_registers

    def _get_registers(
        self,
        ir3_node: Any,
        md_args: List[str],
        liveness_data: Dict[str, List[int]]
    ) -> Any:

        # Register data to be returned is a dictionary of a tuple of (str, bool)
        # where the string is the register and the bool is for whether there is
        # spilling

        register_data = {}

        required_registers = self._get_required_registers(ir3_node)

        # Store registers that have been selected to prevent re-selection
        excluded_registers = []

        for k, v in required_registers.items():

            register_found = False

            if self.debug:
                sys.stdout.write("Getting register for binop node - " + k + \
                    "\n")

            if not v:
                continue

            '''
            is_arg = self._check_if_in_arguments(
                v,
                md_args
            )

            if is_arg:
                register_data[k] = (is_arg, False)
                continue
            '''

            is_in_register = self._check_if_in_register(v, excluded_registers)

            if is_in_register:

                if self.debug:
                    sys.stdout.write("Register found in address descriptor: " + \
                        str(is_in_register) + "\n")

                register_data[k] = (is_in_register[0], False)
                excluded_registers.append(is_in_register[0])
                continue

            if self.debug:
                sys.stdout.write("Register not found in address descriptor.\n")

            # If x is not in a register, and there is a register currently empty,
            # pick that register

            if self.debug:
                sys.stdout.write("Getting register - current register descriptor: " +
                    str(self.register_descriptor) + "\n")

            empty_register = self._check_for_empty_register(
                excluded_registers
            )

            if empty_register:
                register_data[k] = (empty_register, False)
                excluded_registers.append(empty_register)
                continue

            # If x is not in a register and no register is available:

            # 1. if there is an alternative location, it can be replaced

            empty_register = self._check_for_register_with_replaceable_value(
                excluded_registers
            )
            if empty_register:
                register_data[k] = (empty_register, False)
                excluded_registers.append(empty_register)
                continue

            if self.debug:
                sys.stdout.write("Getting register - Check #1 Alternative locations failed.\n")

            # 2. if value in register = y [x = y + z], and y is not z, it can be replaced

            if self.debug:
                sys.stdout.write("Getting register - Check #2 [x = y + z], and y is not z, it can be replaced.\n")

            if k == 'y' or k == 'z':

                other_ref = None
                other_ref_reg = None

                if k == 'y':

                    try:
                        other_ref = required_registers['z']
                        other_ref_reg = register_data['z'][0]
                    except:
                        pass

                elif k == 'z':


                    try:
                        other_ref = required_registers['y']
                        other_ref_reg = register_data['y'][0]
                    except:
                        pass

                empty_register = self._check_for_equivalent_register(
                    v,
                    other_ref,
                    other_ref_reg,
                    excluded_registers
                )
                if empty_register:
                    register_data[k] = (empty_register, False)
                    excluded_registers.append(empty_register)
                    continue

            if self.debug:
                    sys.stdout.write("Getting register - Check #2 failed.\n")

            # 3. if value is not used later, it can be replaced

            if self.debug:
                sys.stdout.write("Getting register - Check #3 Replace no subsequent use.\n")

            replaced_register = self._check_for_no_subsequent_use(
                k,
                ir3_node.md_line_no,
                liveness_data,
                excluded_registers
            )
            if replaced_register:
                register_data[k] = (replaced_register, False)
                excluded_registers.append(replaced_register)
                continue

            # 4. Calculate spilling cost and replace register with lowest cost

            if self.debug:
                sys.stdout.write("Getting register - Check #4 Getting spilled register.\n")

            spilled_register = self._get_spilled_register(
                v,
                ir3_node.md_line_no,
                liveness_data,
                excluded_registers
            )
            if spilled_register:
                register_data[k] = (spilled_register, True)
                excluded_registers.append(spilled_register)
                continue

        return register_data

    def _update_label(
        self,
        identifier: Any,
        label: str
    ) -> None:

        if self.debug:
            sys.stdout.write("\nDescriptors before label update.\n")
            sys.stdout.write("Address descriptor: " + str(self.address_descriptor) + \
                "\n")

        # Update sole reference to label

        # There should be one reference only for a string identifier
        self.address_descriptor[identifier]['references'] = deque([label])

    def _update_descriptors(
        self,
        register: str,
        identifier: Any
    ) -> None:

        if self.debug:
            sys.stdout.write("\nDescriptors before update.\n")
            sys.stdout.write("Register descriptor: " + str(self.register_descriptor) + \
                "\n")
            sys.stdout.write("Address descriptor: " + str(self.address_descriptor) + \
                "\n")

        # Save current references in register

        try:
            current_register_reference = self.register_descriptor[register]
        except:
            current_register_reference = None

        # Remove register references in address descriptor

        if current_register_reference:
            for r in current_register_reference:
                try:
                    self.address_descriptor[r]['references'].remove(register)
                except:
                    pass

        # Check if identifier is a ClassAttribute3Node

        if type(identifier) == ClassAttribute3Node:

            # Set register to empty list since it is a temporary store
            # before storing to memory

            self.register_descriptor[register] = deque([])

        else:
            # Set register to identifier in register descriptor

            self.register_descriptor[register] = deque([identifier])

            # Set identifier to register in address descriptor

            try:
                self.address_descriptor[identifier]['references'].append(register)
            except:
                pass

        if self.debug:
            sys.stdout.write("\nDescriptors updated.\n")
            sys.stdout.write("Register descriptor: " + str(self.register_descriptor) + \
                "\n")
            sys.stdout.write("Address descriptor: " + str(self.address_descriptor) + \
                "\n")

    def _reset_descriptors(self) -> None:

        if self.debug:
            sys.stdout.write("Resetting descriptors.\n")
            sys.stdout.write("Register descriptor: " + str(self.register_descriptor) + \
                "\n")
            sys.stdout.write("Address descriptor: " + str(self.address_descriptor) + \
                "\n")


        self.address_descriptor = {}
        self.register_descriptor = {
            'v1': deque(),
            'v2': deque(),
            'v3': deque(),
            'v4': deque(),
            'v5': deque(),
        }

    def _initialise_assembler_directive(self) -> "Instruction":

        instruction_data = Instruction(
            self._get_incremented_instruction_count(),
            instruction=".data\n\n",
        )

        instruction_L1 = Instruction(
            self._get_incremented_instruction_count(),
            instruction="L1:\n.text\n.global main\n\n"
        )

        self._link_instructions([
            instruction_data,
            instruction_L1
        ])

        return instruction_data

    def _convert_ir3_to_assembly(self, ir3_tree: "IR3Tree") -> None:

        self.instruction_count = self.data_label_count = 0
        self.instruction_head = self.instruction_data_tail = \
            self.instruction_tail = None

        self._reset_descriptors()

        self.instruction_head = self.instruction_data_tail = \
        self._initialise_assembler_directive()
        self.instruction_tail = self.instruction_head.get_last_child()

        main_instruction = self._convert_cmtd3_to_assembly(
            ir3_tree.head.method_data,
            ir3_tree.head.class_data
        )

        current_node = ir3_tree.head.method_data.child
        completed = False

        while not completed:
            # Iterate through methods

            if not current_node:
                # If no other methods, terminate loop
                completed=True

            if current_node:

                self._reset_descriptors()

                instruction = self._convert_cmtd3_to_assembly(
                    current_node,
                    ir3_tree.head.class_data
                )

                current_tail = self.instruction_tail

                self._link_instructions([
                    current_tail,
                    instruction
                ])

                self.instruction_tail = instruction.get_last_child()

                current_node = current_node.child

        current_tail = self.instruction_tail

        self._link_instructions([
            current_tail,
            main_instruction
        ])

        self.instruction_tail = main_instruction.get_last_child()

    def _convert_cmtd3_to_assembly(
        self,
        ir3_node: "CMtd3Node",
        ir3_class_data: "CData3Node"
    ) -> "Instruction":

        self._reset_descriptors()

        # Get method arguments to cascade down to each statement
        md_args = ir3_node.get_arguments()

        # Set up callee-saved registers

        method_name = ir3_node.method_id
        if method_name[0] == "%":
            method_name = method_name[1:]

        instruction_start_label = Instruction(
            self._get_incremented_instruction_count(),
            "\n" + method_name + ":" + "\n"
        )

        instruction_push_callee_saved = Instruction(
            self._get_incremented_instruction_count(),
            instruction="stmfd sp!,{v1,v2,v3,v4,v5,fp,lr}\n"
        )

        instruction_set_frame_pointer = Instruction(
            self._get_incremented_instruction_count(),
            instruction="add fp,sp,#24\n",
        )

        # Set aside space for variable declarations

        var_decl_offset = self._calculate_offset_for_md_vardecl(
            ir3_node,
            ir3_class_data
        )

        instruction_set_space_for_var_decl = Instruction(
            self._get_incremented_instruction_count(),
            instruction="sub sp,fp,#" + str(var_decl_offset) + "\n"
        )

        # Convert statements to assembly code

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Arguments - " + \
                str(md_args) + "\n")

        # Compute liveness information
        liveness_data = self._get_md_liveness_data(
            ir3_node,
            md_args
        )

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Liveness data - " + \
                str(liveness_data) + "\n")

        # Pre-generate exit label for method
        # Needed for early termination e.g. multiple return statements

        exit_label = "." + method_name + "Exit"

        # Convert statements to assembly

        stmt_start_instruction = self._convert_stmt_to_assembly(
            ir3_node.statements,
            md_args,
            liveness_data,
            exit_label
        )
        stmt_end_instruction = stmt_start_instruction.get_last_child()

        # Placeholder label to exit method

        instruction_exit_label = Instruction(
            self._get_incremented_instruction_count(),
            instruction="\n" + exit_label + ":\n"
        )

        # Restore callee-saved registers

        instruction_reset_frame_pointer = Instruction(
            self._get_incremented_instruction_count(),
            instruction="sub sp,fp,#24\n"
        )

        instruction_pop_callee_saved = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldmfd sp!,{v1,v2,v3,v4,v5,fp,pc}\n",
        )

        self._link_instructions([
            instruction_start_label,
            instruction_push_callee_saved,
            instruction_set_frame_pointer,
            instruction_set_space_for_var_decl,
            stmt_start_instruction
        ])

        self._link_instructions([
            stmt_end_instruction,
            instruction_exit_label,
            instruction_reset_frame_pointer,
            instruction_pop_callee_saved
        ])

        return instruction_start_label

    def _calculate_offset_for_md_vardecl(
        self,
        ir3_node: "CMtd3Node",
        ir3_class_data: "CData3Node"
    ) -> int:

        fp_offset = 24

        current_var_decl = ir3_node.variable_declarations
        var_decl_completed = False

        while not var_decl_completed:

            if not current_var_decl:
                var_decl_completed = True
                break

            if type(current_var_decl) == VarDecl3Node:

                # Calculate offset
                fp_offset += 4

                # Add variable and offset to symbol table
                if self.debug:
                    sys.stdout.write("Calculating space for var decl: " + \
                        str(current_var_decl.value) + "\n")
                    sys.stdout.write("Offset: " + str(fp_offset) + "\n")

                self._declare_new_variable(
                    current_var_decl.value,
                    fp_offset
                )

                if self.debug:
                    sys.stdout.write("Add var decl to address descriptor: " + \
                        str(self.address_descriptor) + "\n")

                '''
                elif type(current_var_decl.type) == tuple:

                    # If it is a class object

                    if self.debug:
                        sys.stdout.write("Calculating space for object decl: " + \
                            str(current_var_decl.value) + " of class " + \
                            str(current_var_decl.type[1])+ "\n")

                    # Look for object class in class data

                    object_class = current_var_decl.type[1]

                    completed = False
                    current_class_data = ir3_class_data

                    while not completed:

                        if not current_class_data:
                            completed = True
                            break

                        if object_class == current_class_data.class_name:

                            # Get identifiers of class attributes

                            object_attributes = current_class_data.get_var_decl_identifiers()

                            relative_offset = 0

                            for a in object_attributes:

                                # For each class attribute, increment the offset
                                # and declare a new variable

                                fp_offset += 4

                                a_identifier = current_var_decl.value + "." + \
                                    a

                                self._declare_new_variable(
                                    a_identifier,
                                    fp_offset,
                                    relative_offset
                                )

                                relative_offset += 4

                            completed = True
                            break

                        current_class_data = current_class_data.child
                '''
            current_var_decl = current_var_decl.child

        current_stmt = ir3_node.statements
        stmt_completed = False

        while not stmt_completed:

            if not current_stmt:
                stmt_completed = True
                break

            if type(current_stmt) == VarDecl3Node:

                # Calculate offset
                fp_offset += 4

                # Add variable and offset to symbol table
                if self.debug:
                    sys.stdout.write("Calculating space for var decl: " + \
                        str(current_stmt.value) + "\n")
                    sys.stdout.write("Offset: " + str(fp_offset) + "\n")

                self._declare_new_variable(current_stmt.value, fp_offset)

                if self.debug:
                    sys.stdout.write("Add var decl to address descriptor: " + \
                        str(self.address_descriptor) + "\n")

            current_stmt = current_stmt.child

        return fp_offset

    def _convert_stmt_to_assembly(
        self,
        ir3_node: Any,
        md_args: List[str],
        liveness_data: Dict[str, List[int]],
        exit_label: str
    ) -> "Instruction":

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Args: " + \
                str(md_args) + "\n")

        first_instruction = None
        current_instruction = None
        new_instruction = None

        current_stmt = ir3_node
        completed = False

        while not completed:

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - current stmt: " + \
                    str(type(current_stmt)) + "\n")

            if not current_stmt:
                completed = True
                break

            if type(current_stmt) == ReadLn3Node:

                new_instruction = self._convert_readln_to_assembly(
                    current_stmt,
                    current_instruction,
                    md_args,
                    liveness_data
                )

            elif type(current_stmt) == PrintLn3Node:

                new_instruction = self._convert_println_to_assembly(
                    current_stmt,
                    current_instruction
                )

            elif type(current_stmt) == Assignment3Node:

                new_instruction = self._convert_assignment_to_assembly(
                    current_stmt,
                    md_args,
                    liveness_data
                )

            elif type(current_stmt) == VarDecl3Node:
                # Ignore VarDecl3 node since no instructions are required
                if self.debug:
                    sys.stdout.write("Converting stmt to assembly - "
                        "Skipping VarDecl3Node.\n")

            elif type(current_stmt) == Return3Node:

                new_instruction = self._convert_return_to_assembly(
                    current_stmt,
                    md_args,
                    liveness_data,
                    exit_label
                )

            elif type(current_stmt) == Label3Node:

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="\n." + str(current_stmt.label_id) + ":\n"
                )

            elif type(current_stmt) == IfGoTo3Node:

                new_instruction = self._convert_if_goto_statement_to_assembly(
                    current_stmt,
                    md_args,
                    liveness_data
                )

            elif type(current_stmt) == GoTo3Node:

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="b ." + str(current_stmt.goto) + "\n"
                )

            else:

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="Uncaught statement detected\n",
                    parent=current_instruction
                )

            if new_instruction:

                if self.debug:
                    sys.stdout.write("Converting stmt to assembly - Generated instruction: " + \
                        new_instruction.assembly_code + "\n")

                if current_instruction:
                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - Adding instruction\n")
                    current_instruction.set_child(new_instruction)

                else:
                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - First instruction\n")
                    first_instruction = new_instruction

                current_instruction = new_instruction.get_last_child()

            new_instruction = None
            current_stmt = current_stmt.child

        return first_instruction

    def _convert_readln_to_assembly(
        self,
        readln3node: ReadLn3Node,
        current_instruction: Optional["Instruction"],
        md_args: List[str],
        liveness_data: Dict[str, List[int]]
    ) -> "Instruction":

        read_data_string_label = "d" + str(self.data_label_count) + \
            "_" + str(readln3node.id3) + "_format"

        read_data_label = "d" + str(self.data_label_count) + \
            "_" + str(readln3node.id3)
        self.data_label_count += 1

        if self.debug:
            sys.stdout.write("Converting readln to assembly - Expression.\n")

        # Initialise storage variable for integer in data

        instruction_initialise_readln_data_storage_format = Instruction(
            self._get_incremented_instruction_count(),
            instruction=read_data_string_label + ": .asciz \"%d\"\n"
        )

        instruction_initialise_readln_data_storage_identifier = Instruction(
            self._get_incremented_instruction_count(),
            instruction=read_data_label + ": .word 0\n"
        )

        self._link_instructions([
            instruction_initialise_readln_data_storage_format,
            instruction_initialise_readln_data_storage_identifier,
        ])

        self.instruction_data_tail.insert_child(instruction_initialise_readln_data_storage_format)
        self.instruction_data_tail = instruction_initialise_readln_data_storage_identifier

        # Actual instructions to read input

        instruction_load_readln_format = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldr a1,=" + read_data_string_label + "\n"
        )

        instruction_load_readln_storage_identifier = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldr a2,=" + read_data_label + "\n"
        )

        instruction_scanf = Instruction(
            self._get_incremented_instruction_count(),
            instruction="bl scanf\n"
        )

        # Store data captured to identifier

        store_register = self._get_registers(
            readln3node,
            md_args,
            liveness_data
        )['x'][0]


        instruction_load_read_value_address = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldr " + store_register + ",=" + read_data_label + "\n"
        )

        instruction_load_read_value = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldr " + store_register + ",[" + store_register + "]\n"
        )

        identifier_offset = self._get_variable_offset(
            readln3node.id3
        )

        instruction_store_read_value_to_identifier = Instruction(
            self._get_incremented_instruction_count(),
            instruction="str " + store_register + ",[fp,#-" + \
                str(identifier_offset) + "]\n"
        )

        self._update_descriptors(
            register=store_register,
            identifier=readln3node.id3
        )

        # Pop argument registers onto the stack to save argument values
        # in case there are nested function calls

        instruction_save_arg_registers = Instruction(
            self._get_incremented_instruction_count(),
            instruction="stmfd sp!,{a1,a2,a3,a4}\n"
        )

        # Restore argument registers from stack to restore argument values
        # after nested function call

        instruction_pop_arg_registers = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldmfd sp!,{a1,a2,a3,a4}\n"
        )

        self._link_instructions([
            instruction_save_arg_registers,
            instruction_load_readln_format,
            instruction_load_readln_storage_identifier,
            instruction_scanf,
            instruction_load_read_value_address,
            instruction_load_read_value,
            instruction_store_read_value_to_identifier,
            instruction_pop_arg_registers
        ])

        return instruction_save_arg_registers

    def _convert_println_to_assembly(
        self,
        println3node: PrintLn3Node,
        current_instruction: Optional["Instruction"],
    ) -> "Instruction":

        print_data_label = "d" + str(self.data_label_count)
        self.data_label_count += 1

        if self.debug:
            sys.stdout.write("Converting println to assembly - Expression: " + \
                str(println3node.expression) + "\n")

        if println3node.type == BasicType.INT:

            if self.debug:
                sys.stdout.write("Converting println to assembly - Integer detected.\n")

            if println3node.is_raw_value:
                # Check if it is raw integer
                    print_data = int(println3node.expression)
                    instruction_load_print_value_assembly_code = "mov a2,#" + \
                        str(print_data) + "\n"

            else:

                # Check if identifier is in register
                identifier_in_register = self._check_if_in_register(
                    println3node.expression
                )

                if identifier_in_register:
                    # Move value from existing register to a1
                    instruction_load_print_value_assembly_code = "mov a2," + \
                        identifier_in_register[0] + "\n"

                else:
                    # Load value from stack
                    identifier_offset = self._get_variable_offset(
                        println3node.expression
                    )

                    instruction_load_print_value_assembly_code = "ldr a2,[fp,#-" + \
                        str(identifier_offset) + "]\n"

            instruction_initialise_print_data_assembly_code = print_data_label + \
                ": .asciz \"%i\"\n"

        elif println3node.type == BasicType.STRING:

            if self.debug:
                sys.stdout.write("Converting println to assembly - String detected.\n")

            # Check if it is a raw string

            if println3node.is_raw_value:

                instruction_load_print_value_assembly_code = "mov a2,#0\n"

                instruction_initialise_print_data_assembly_code = print_data_label + \
                    ": .asciz " + println3node.expression[:-1] + '"' + "\n"

            # Otherwise, lookup symbol table
            else:

                if self.debug:
                    sys.stdout.write("Converting println to assembly - Identifier detected.\n")


                print_data_label = self.address_descriptor[println3node.expression]['references'][0]

                # Print data label should be the only reference for address descriptor
                # of a string unless it is returned from a method call.

                # Check for the first letter.
                # If it starts with 'd', load from data
                # If it starts with 'v', move from register

                if print_data_label[0] == 'd':

                    instruction_load_print_value_assembly_code = "ldr a1,=" + print_data_label + "\n"

                elif print_data_label[0] == 'v':

                    instruction_load_print_value_assembly_code = "mov a1," + print_data_label + "\n"

        elif println3node.type == BasicType.BOOL:

            if self.debug:
                sys.stdout.write("Converting println to assembly - Boolean detected.\n")

            # Check if it is a raw boolean

            if println3node.is_raw_value:

                instruction_load_print_value_assembly_code = "mov a2,#0\n"

                instruction_initialise_print_data_assembly_code = print_data_label + \
                    ": .asciz " + '"' + println3node.expression + '"' + "\n"

            # Otherwise, lookup symbol table
            else:

                if self.debug:
                    sys.stdout.write("Converting println to assembly - Identifier detected.\n")

                print_true_label = print_data_label
                instruction_initialise_print_true_assembly_code = print_true_label + \
                    ': .asciz "true"\n'

                print_false_label = "d" + str(self.data_label_count) + "_false"

                instruction_initialise_print_false_assembly_code = print_false_label + \
                    ': .asciz "false"\n'

                # Load boolean identifier

                # Check if identifier is in register
                identifier_in_register = self._check_if_in_register(
                    println3node.expression
                )

                if identifier_in_register:
                    # Move value from existing register to a1
                    instruction_load_print_value_assembly_code = "mov a1," + \
                        identifier_in_register[0] + "\n"

                else:
                    # Load value from stack
                    identifier_offset = self._get_variable_offset(
                        println3node.expression
                    )

                    instruction_load_print_value_assembly_code = "ldr a1,[fp,#-" + \
                        str(identifier_offset) + "]\n"

        instruction_load_print_data=None
        if println3node.type == BasicType.BOOL and \
            not println3node.is_raw_value:

            instruction_initialise_print_true = Instruction(
                self._get_incremented_instruction_count(),
                instruction=instruction_initialise_print_true_assembly_code,
            )

            instruction_initialise_print_false = Instruction(
                self._get_incremented_instruction_count(),
                instruction=instruction_initialise_print_false_assembly_code,
            )


            self._link_instructions([
                instruction_initialise_print_true,
                instruction_initialise_print_false
            ])

            self.instruction_data_tail.insert_child(instruction_initialise_print_true)
            self.instruction_data_tail = instruction_initialise_print_false

            # Get value of boolean identifier

            # If true, get true label. If false, get false label

            instruction_load_boolean = Instruction(
                self._get_incremented_instruction_count(),
                instruction=instruction_load_print_value_assembly_code
            )

            # Compare with 0

            instruction_compare_boolean_with_false = Instruction(
                self._get_incremented_instruction_count(),
                instruction="cmp a1,#0\n"
            )

            # If true, value is 0/False branch

            instruction_go_to_false_branch = Instruction(
                self._get_incremented_instruction_count(),
                instruction="beq ." + println3node.value + "_" + \
                    print_false_label + 'False\n'
            )

            # Load argument for true

            instruction_load_true = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldr a1,=" + print_true_label + "\n"
            )

            # Branch to exit

            instruction_branch_exit = Instruction(
                self._get_incremented_instruction_count(),
                instruction="b ." + println3node.value + "_" + print_true_label + \
                    "_exit\n"
            )

            # False branch

            instruction_false_branch = Instruction(
                self._get_incremented_instruction_count(),
                instruction="." + println3node.value + "_" + \
                    print_false_label + 'False:\n'
            )

            # Load argument for false

            instruction_load_false = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldr a1,=" + print_false_label + "\n"
            )

            # Exit branch

            instruction_exit_label = Instruction(
                self._get_incremented_instruction_count(),
                instruction="._" + print_true_label + \
                    "_exit:\n"
            )

            self._link_instructions([
                current_instruction,
                instruction_load_boolean,
                instruction_compare_boolean_with_false,
                instruction_go_to_false_branch,
                instruction_load_true,
                instruction_branch_exit,
                instruction_false_branch,
                instruction_load_false,
                instruction_exit_label
            ])

            instruction_load_print_value = instruction_exit_label

        elif not (println3node.type == BasicType.STRING and not println3node.is_raw_value):

            instruction_initialise_print_data = Instruction(
                self._get_incremented_instruction_count(),
                instruction=instruction_initialise_print_data_assembly_code,
            )

            self.instruction_data_tail.insert_child(instruction_initialise_print_data)
            self.instruction_data_tail = instruction_initialise_print_data

            instruction_load_print_data = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldr a1,=" + print_data_label + "\n",
                parent=current_instruction
            )

        if current_instruction and instruction_load_print_data:
            current_instruction.set_child(instruction_load_print_data)

        if not (println3node.type == BasicType.BOOL and \
            not println3node.is_raw_value):

            instruction_load_print_value = Instruction(
                self._get_incremented_instruction_count(),
                instruction=instruction_load_print_value_assembly_code
            )

        if instruction_load_print_data:
            # No need for additional loading for string identifier
            self._link_instructions([
                instruction_load_print_data,
                instruction_load_print_value
            ])

        instruction_printf = Instruction(
            self._get_incremented_instruction_count(),
            instruction="bl printf\n"
        )

        self._link_instructions([
            instruction_load_print_value,
            instruction_printf
        ])

        # Pop argument registers onto the stack to save argument values
        # in case there are nested function calls

        instruction_save_arg_registers = Instruction(
            self._get_incremented_instruction_count(),
            instruction="stmfd sp!,{a1,a2,a3,a4}\n"
        )

        # Restore argument registers from stack to restore argument values
        # after nested function call

        instruction_pop_arg_registers = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldmfd sp!,{a1,a2,a3,a4}\n"
        )

        if println3node.type == BasicType.BOOL and \
            not println3node.is_raw_value:

            self._link_instructions([
                instruction_save_arg_registers,
                instruction_load_boolean
            ])

        elif instruction_load_print_data:

            self._link_instructions([
                instruction_save_arg_registers,
                instruction_load_print_data
            ])

        else:

            self._link_instructions([
                instruction_save_arg_registers,
                instruction_load_print_value
            ])

        self._link_instructions([
            instruction_printf,
            instruction_pop_arg_registers
        ])

        return instruction_save_arg_registers

    def _convert_assignment_to_assembly(
        self,
        assignment3node: Assignment3Node,
        md_args: List[str],
        liveness_data: Dict[str, List[int]]
    ) -> "Instruction":

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Assignment\n")

        registers = self._get_registers(
            assignment3node,
            md_args,
            liveness_data
        )

        required_registers = self._get_required_registers(
            assignment3node
        )

        if self.debug:
            sys.stdout.write("Registers obtained: " + str(registers) + \
                "\n")

        x_is_arg = self._check_if_in_arguments(
            assignment3node.identifier,
            md_args
        )

        if type(assignment3node.identifier) == ClassAttribute3Node:

            # Manually override with y register for class attribute
            # Need to guarantee register for base address of object is different
            # from register for value to assign
            x_register = registers['y'][0]

        else:
            x_register = registers['x'][0]

        is_simple_assignment = assignment3node.assigned_value_is_raw_value

        if is_simple_assignment:

            if type(assignment3node.assigned_value) == IR3Node:
                assigned_value = assignment3node.assigned_value.value

            else:
                assigned_value = assignment3node.assigned_value

            if assignment3node.type in [BasicType.INT, BasicType.BOOL]:

                if assignment3node.type == BasicType.INT:

                    # x = CONSTANT
                    new_instruction = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="mov " + x_register + ",#" + \
                            str(assigned_value) + "\n"
                    )

                elif assignment3node.type == BasicType.BOOL:

                    mv_operator = BOOL_CONVERSION[assigned_value]

                    new_instruction = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction=mv_operator + " " + x_register + ",#0\n"
                    )

            elif assignment3node.type == BasicType.STRING:

                string_data_label = "d" + str(self.data_label_count)
                self.data_label_count += 1

                if self.debug:
                    sys.stdout.write("Converting assignment to assembly - Raw string: " + \
                        str(assigned_value) + "\n")

                instruction_initialise_string_data_assembly_code = string_data_label + \
                    ": .asciz " + assigned_value[:-1] + '"' + "\n"

                instruction_add_string_to_data = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction=instruction_initialise_string_data_assembly_code
                )

                self.instruction_data_tail.insert_child(instruction_add_string_to_data)
                self.instruction_data_tail = instruction_add_string_to_data

                self._update_label(
                    identifier=assignment3node.identifier,
                    label=string_data_label
                )

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + x_register + ",=" + string_data_label + "\n"
                )

            else:

                if self.debug:
                    sys.stdout.write("Converting stmt to assembly - Assignment - node type: " + \
                        str(assignment3node.type) + "\n")

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="Error in simple assignment.\n"
                )

        elif type(assignment3node.assigned_value) == ClassInstance3Node:

            #  x = new Object

            # Get the space required for object
            space_required = self._get_space_required_for_object(
                assignment3node.assigned_value.target_class
            )

            # Set argument register to the space required
            instruction_create_space = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov a1,#" + str(space_required) + "\n"
            )

            # Create space in memory
            instruction_malloc = Instruction(
                self._get_incremented_instruction_count(),
                instruction="bl malloc\n"
            )

            # Get offset of object

            object_offset = self.address_descriptor[
                assignment3node.identifier
            ]['offset']

            # Store address returned in stack

            instruction_store_base_address = Instruction(
                self._get_incremented_instruction_count(),
                instruction="str a1,[fp,#-" + str(object_offset) + "]\n"
            )

            self._link_instructions([
                instruction_create_space,
                instruction_malloc,
                instruction_store_base_address
            ])

            new_instruction = instruction_create_space

        elif type(assignment3node.assigned_value) == UnaryOp3Node:

            # x = -y
            # x = !y

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                    "x = unaryop y\n")

            # Get register for y
            # No need to check if y is raw value because IR3 code uses identifiers
            # only for UnaryOp3Node

            y_reg = registers['y'][0]

            if (assignment3node.type == BasicType.INT and \
                    assignment3node.assigned_value.operator == '-'):

                var_y_offset = self.address_descriptor[
                    assignment3node.assigned_value.operand
                ]['offset']

                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + y_reg + ",[fp,#-" + str(var_y_offset) + \
                        "]\n"
                )

                instruction_not_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="neg " + x_register + "," + y_reg + "\n"
                )

                self._link_instructions([
                    instruction_load_y_value,
                    instruction_not_y_value
                ])

                self._update_descriptors(
                    register=y_reg,
                    identifier=assignment3node.assigned_value.operand
                )

                new_instruction = instruction_load_y_value

            elif (assignment3node.type == BasicType.BOOL and \
                    assignment3node.assigned_value.operator) == '!':

                var_y_is_arg = self._check_if_in_arguments(
                    assignment3node.assigned_value.operand,
                    md_args
                )

                if self.debug:

                    sys.stdout.write("Unary op - check if y is in arg: " + \
                        str(var_y_is_arg) + "\n")

                if var_y_is_arg:

                    instruction_load_y_value = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="mov " + y_reg + "," + var_y_is_arg + "\n"
                    )

                else:
                    var_y_offset = self.address_descriptor[
                        assignment3node.assigned_value.operand
                    ]['offset']

                    instruction_load_y_value = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="ldr " + y_reg + ",[fp,#-" + str(var_y_offset) + \
                            "]\n"
                    )

                instruction_negate_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="mvn " + x_register + "," + y_reg + "\n"
                )

                self._link_instructions([
                    instruction_load_y_value,
                    instruction_negate_y_value
                ])

                self._update_descriptors(
                    register=y_reg,
                    identifier=assignment3node.assigned_value.operand
                )

                new_instruction = instruction_load_y_value

        elif type(assignment3node.assigned_value) == BinOp3Node:

            # x = y + z
            if self.debug:
                sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                    "x = y + z\n")

            # Check if y is raw value

            y_is_arg = self._check_if_in_arguments(
                assignment3node.assigned_value.left_operand,
                md_args
            )

            y_is_raw = assignment3node.assigned_value.left_operand_is_raw_value

            y_value = assignment3node.assigned_value.left_operand
            if not y_is_raw:
                y_value = registers['y'][0]

            # Check if z is raw value

            z_is_arg = self._check_if_in_arguments(
                assignment3node.assigned_value.right_operand,
                md_args
            )

            z_is_raw = assignment3node.assigned_value.right_operand_is_raw_value

            z_value = assignment3node.assigned_value.right_operand
            if not z_is_raw:
                z_value = registers['z'][0]

            # Actual assignment

            if (assignment3node.type == BasicType.INT and \
                    assignment3node.assigned_value.operator != '/') or \
                assignment3node.type == BasicType.BOOL:

                move_instruction = "mov "
                if assignment3node.type == BasicType.INT:


                    operator_instruction = ARITHMETIC_OP[assignment3node.assigned_value.operator]

                elif assignment3node.type == BasicType.BOOL:

                    operator_instruction = BINARY_OP[assignment3node.assigned_value.operator]
                    # Convert raw values if any
                    if y_is_raw:
                        move_instruction = "mvn "
                        y_value = 0

                    if z_is_raw:
                        move_instruction = "mvn "
                        z_value = 0

                if self.debug:
                    sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                        "x = y + z - Plus operator" + "\n")

                if y_is_raw:
                    # If y is a raw value
                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                            "x = y + z - Loading z" + "\n")

                    instruction_load_mul_raw_y = None
                    if assignment3node.assigned_value.operator == '*':
                        instruction_load_mul_raw_y = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=move_instruction + registers['y'][0] + ",#" + str(y_value) + "\n"
                        )

                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + z_value + "," + registers['y'][0] + "\n"
                        )

                        self._link_instructions([
                            instruction_load_mul_raw_y,
                            instruction_binop
                        ])

                    else:

                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + z_value + ",#" + str(y_value) + "\n"
                        )

                    if not z_is_arg:

                        # If z is not an argument, load z

                        var_z_offset = self.address_descriptor[assignment3node.assigned_value.right_operand]['offset']

                        new_instruction = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + z_value + ",[fp,#-" + \
                                str(var_z_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=z_value,
                            identifier=assignment3node.assigned_value.right_operand
                        )

                        if instruction_load_mul_raw_y:

                            self._link_instructions([
                                new_instruction,
                                instruction_load_mul_raw_y
                            ])


                        else:

                            self._link_instructions([
                                new_instruction,
                                instruction_binop
                            ])

                    elif z_is_arg:

                        # If z is an argument, load z from the argument register
                        # to the assigned register

                        instruction_move_from_argument_register = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=move_instruction + z_value + "," + z_is_arg + "\n"
                        )

                        self._update_descriptors(
                            register=z_value,
                            identifier=assignment3node.assigned_value.right_operand
                        )


                        if instruction_load_mul_raw_y:

                            self._link_instructions([
                                instruction_move_from_argument_register,
                                instruction_load_mul_raw_y
                            ])

                        else:

                            self._link_instructions([
                                instruction_move_from_argument_register,
                                instruction_binop
                            ])

                        new_instruction = instruction_move_from_argument_register

                elif z_is_raw:

                    # If z is a raw value
                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                            "x = y + z - Loading z" + "\n")

                    instruction_load_mul_raw_z = None
                    if assignment3node.assigned_value.operator == '*':
                        instruction_load_mul_raw_z = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="mov " + registers['z'][0] + ",#" + str(z_value) + "\n"
                        )

                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + y_value + "," + registers['z'][0] + "\n"
                        )

                        self._link_instructions([
                            instruction_load_mul_raw_z,
                            instruction_binop
                        ])

                    else:

                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + y_value + ",#" + str(z_value) + "\n"
                        )

                    if not y_is_arg:

                        # If y is not an argument, load y

                        var_y_offset = self.address_descriptor[assignment3node.assigned_value.left_operand]['offset']

                        new_instruction = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + y_value + ",[fp,#-" + \
                                str(var_y_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=y_value,
                            identifier=assignment3node.assigned_value.left_operand
                        )

                        if instruction_load_mul_raw_z:

                            self._link_instructions([
                                new_instruction,
                                instruction_load_mul_raw_z
                            ])

                        else:

                            self._link_instructions([
                                new_instruction,
                                instruction_binop
                            ])

                    elif y_is_arg:

                        # If z is a raw value, load y

                        instruction_move_from_argument_register = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="mov " + y_value + "," + y_is_arg + "\n"
                        )

                        self._update_descriptors(
                            register=y_value,
                            identifier=assignment3node.assigned_value.left_operand
                        )

                        if instruction_load_mul_raw_z:

                            self._link_instructions([
                                instruction_move_from_argument_register,
                                instruction_load_mul_raw_z
                            ])

                        else:

                            self._link_instructions([
                                instruction_move_from_argument_register,
                                instruction_binop
                            ])

                        new_instruction = instruction_move_from_argument_register

                else:

                    # Load y and z
                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                            "x = y + z - Loading y and z" + "\n")

                    if not y_is_arg and not z_is_arg:

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                                "x = y + z - Loading y and z - Both not args" + "\n")

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                                "x = y + z - Loading y and z - Both not args - register y: " + \
                                y_value + "\n")

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                                "x = y + z - Loading y and z - Both not args - register z: " + \
                                z_value + "\n")

                        var_y_offset = self.address_descriptor[assignment3node.assigned_value.left_operand]['offset']

                        new_instruction = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + y_value + ",[fp,#-" + \
                                str(var_y_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=y_value,
                            identifier=assignment3node.assigned_value.left_operand
                        )

                        var_z_offset = self.address_descriptor[assignment3node.assigned_value.right_operand]['offset']

                        instruction_load_z = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + z_value + ",[fp,#-" + \
                                str(var_z_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=z_value,
                            identifier=assignment3node.assigned_value.right_operand
                        )


                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + y_value + "," + z_value + "\n"
                        )

                        self._link_instructions([
                            new_instruction,
                            instruction_load_z,
                            instruction_binop
                        ])

                    elif y_is_arg and not z_is_arg:

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                                "x = y + z - Loading y and z - Only y is arg" + "\n")

                        instruction_move_from_argument_register = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="mov " + y_value + "," + y_is_arg + "\n",
                        )

                        self._update_descriptors(
                            register=y_value,
                            identifier=assignment3node.assigned_value.left_operand
                        )

                        var_z_offset = self.address_descriptor[assignment3node.assigned_value.right_operand]['offset']

                        instruction_load_z = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + z_value + ",[fp,#-" + \
                                str(var_z_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=z_value,
                            identifier=assignment3node.assigned_value.right_operand
                        )

                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + y_value + "," + z_value + "\n"
                        )

                        self._link_instructions([
                            instruction_move_from_argument_register,
                            instruction_load_z,
                            instruction_binop
                        ])

                        new_instruction = instruction_move_from_argument_register

                    elif not y_is_arg and z_is_arg:

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                                "x = y + z - Loading y and z - Only z is arg" + "\n")

                        instruction_move_from_argument_register = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="mov " + z_value + "," + z_is_arg + "\n",
                        )

                        self._update_descriptors(
                            register=z_value,
                            identifier=assignment3node.assigned_value.right_operand
                        )

                        var_y_offset = self.address_descriptor[assignment3node.assigned_value.left_operand]['offset']

                        instruction_load_y = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + y_value + ",[fp,#-" + \
                                str(var_y_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=y_value,
                            identifier=assignment3node.assigned_value.left_operand
                        )

                        instruction_move_from_argument_register.set_child(instruction_load_y)


                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + y_value + "," + z_value + "\n"
                        )

                        self._link_instructions([
                            instruction_move_from_argument_register,
                            instruction_load_y,
                            instruction_binop
                        ])

                        new_instruction = instruction_move_from_argument_register

                    elif y_is_arg and z_is_arg:

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                                "x = y + z - Loading y and z - Both args" + "\n")

                        instruction_move_y_from_argument_register = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="mov " + y_value + "," + y_is_arg + "\n",
                        )

                        self._update_descriptors(
                            register=y_value,
                            identifier=assignment3node.assigned_value.left_operand
                        )

                        instruction_move_z_from_argument_register = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="mov " + z_value + "," + z_is_arg + "\n"
                        )

                        self._update_descriptors(
                            register=z_value,
                            identifier=assignment3node.assigned_value.right_operand
                        )

                        instruction_binop = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction=operator_instruction + x_register + \
                                "," + y_value + "," + z_value + "\n"
                        )

                        self._link_instructions([
                            instruction_move_y_from_argument_register,
                            instruction_move_z_from_argument_register,
                            instruction_binop
                        ])

                        new_instruction = instruction_move_y_from_argument_register

            else:

                # Placeholder: Handle string concatenation and integer division

                if self.debug:
                    sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                        "String concatenation and integer division are not handled" + "\n")

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="String concatenation and integer division are not handled\n"
                )

            # Check for spilling and store to stack beforehand by adding
            # instruction at the top

            if self.debug:
                sys.stdout.write("Registers obtained: " + str(registers) + ".\n")

            for k, v in registers.items():

                if v[1]:

                    if self.debug:
                        sys.stdout.write("Spilt register - Generating str instruction.\n")

                    spilled_identifiers = self.register_descriptor[v[0]]

                    stored_offsets = []

                    for s in spilled_identifiers:
                        var_offset = self.address_descriptor[s]['offset']

                        if var_offset not in stored_offsets:

                            spill_instruction = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction="str " + v[0] + ",[fp,#-" + \
                                    str(var_offset) + "]\n"
                            )

                            self._link_instructions([
                                spill_instruction,
                                new_instruction
                            ])

                            new_instruction = spill_instruction

                            stored_offset.append(var_offset)

                    if self.debug:
                        sys.stdout.write("Spilt register - str instruction added.\n")

                    self._update_descriptors(
                        register=v[0],
                        identifier=required_registers[k]
                    )

        elif type(assignment3node.assigned_value) == RelOp3Node:

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - RelOp.\n")

            new_instruction = Instruction(
                self._get_incremented_instruction_count(),
                instruction="Test test RelOp\n"
            )

            # Load first operand

            var_y_is_arg = self._check_if_in_arguments(
                assignment3node.assigned_value.left_operand,
                md_args
            )

            if var_y_is_arg:
                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="mov " + registers['y'][0] + "," + \
                        var_y_is_arg + "\n"
                )

            else:

                var_y_offset = self.address_descriptor[
                    assignment3node.assigned_value.left_operand
                ]['offset']

                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + registers['y'][0] + ",[fp,#-" + \
                        str(var_y_offset) + "]\n",
                )

            # Load second operand

            var_z_is_arg = self._check_if_in_arguments(
                assignment3node.assigned_value.right_operand,
                md_args
            )

            if var_z_is_arg:
                instruction_load_z_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="mov " + registers['z'][0] + "," + \
                        var_z_is_arg + "\n"
                )

            else:

                var_z_offset = self.address_descriptor[
                    assignment3node.assigned_value.right_operand
                ]['offset']

                instruction_load_z_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + registers['z'][0] + ",[fp,#-" + \
                        str(var_z_offset) + "]\n"
                )

            # Compare

            instruction_compare = Instruction(
                self._get_incremented_instruction_count(),
                instruction="cmp " + registers['y'][0] + "," + \
                    registers['z'][0] + "\n"
            )

            # If true, go to branch to set to True

            rel_instruction = REL_OP[assignment3node.assigned_value.operator]
            branch_index = self.branch_count
            self.branch_count += 1

            true_branch_label = "." + str(assignment3node.identifier) + \
                "_true_" + str(branch_index)
            exit_branch_label = "." + str(assignment3node.identifier) + \
                "_exit_" + str(branch_index)

            instruction_conditional_branch = Instruction(
                self._get_incremented_instruction_count(),
                instruction=rel_instruction + true_branch_label + "\n"
            )

            # Otherwise, set to False and branch to exit

            instruction_set_value_to_false = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov " + registers['x'][0] + ",#0\n"
            )

            instruction_branch_exit = Instruction(
                self._get_incremented_instruction_count(),
                instruction="b " + exit_branch_label + "\n"
            )

            # True branch

            instruction_true_branch_label = Instruction(
                self._get_incremented_instruction_count(),
                instruction=true_branch_label + ":\n"
            )

            instruction_set_value_to_true = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mvn " + registers['x'][0] + ",#0\n"
            )

            # Exit branch label

            instruction_exit_label = Instruction(
                self._get_incremented_instruction_count(),
                instruction=exit_branch_label + ":\n"
            )

            # Link instructions

            self._link_instructions([
                instruction_load_y_value,
                instruction_load_z_value,
                instruction_compare,
                instruction_conditional_branch,
                instruction_set_value_to_false,
                instruction_branch_exit,
                instruction_true_branch_label,
                instruction_set_value_to_true,
                instruction_exit_label
            ])

            new_instruction = instruction_load_y_value

        elif type(assignment3node.assigned_value) == MethodCall3Node:

            method_call_node = assignment3node.assigned_value

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - MethodCall3.\n")

            # Move the base address of the class to a1

            this_arg_identifier = method_call_node.arguments.value

            if this_arg_identifier == 'this':
                # If first argument is a reference to 'this', retain the first argument register

                instruction_load_arguments = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="mov a1,a1\n"
                )

            else:
                base_address_offset = self.address_descriptor[this_arg_identifier]['offset']

                instruction_load_arguments = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr a1,[fp,#-" + str(base_address_offset) +"]\n"
                )

            next_arg = method_call_node.arguments.child
            arg_count = 1
            completed = False
            latest_instruction_load_argument = instruction_load_arguments

            while not completed:

                if not next_arg:
                    completed = True
                    break

                if next_arg:

                    # For each argument, check if it is a raw value or an identifier

                    next_arg_reg = ARG_REGISTERS[arg_count]

                    if next_arg.is_raw_value:
                        # If raw value, move to register directly

                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - MethodCall3 - raw value arg detected.\n")

                        if next_arg.type == BasicType.INT:
                            instruction_load_next_argument = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction="mov " + next_arg_reg + ",#" + \
                                    str(next_arg.value) + "\n"
                            )

                        if next_arg.type == BasicType.STRING:

                            string_data_label = "d" + str(self.data_label_count)
                            self.data_label_count += 1

                            if self.debug:
                                sys.stdout.write("Converting stmt to assembly - MethodCall3 - String.\n")

                            instruction_initialise_string_data_assembly_code = string_data_label + \
                                ": .asciz " + next_arg.value[:-1] + '"' + "\n"

                            instruction_add_string_to_data = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction=instruction_initialise_string_data_assembly_code
                            )

                            self.instruction_data_tail.insert_child(instruction_add_string_to_data)
                            self.instruction_data_tail = instruction_add_string_to_data

                            # No need to update labels because it is a string constant
                            # that will not be reused

                            instruction_load_next_argument = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction="ldr " + next_arg_reg + ",=" + string_data_label + "\n"
                            )

                        if next_arg.type == BasicType.BOOL:

                            mv_instruction = BOOL_CONVERSION[next_arg.value]

                            instruction_load_next_argument = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction=mv_instruction + " " + next_arg_reg + \
                                    ",#0\n"
                            )

                    else:

                        if type(next_arg) == ClassAttribute3Node:
                            if self.debug:
                                sys.stdout.write("Converting stmt to assembly - MethodCall3 - Class attribute arg detected.\n")
                            pass

                        else:
                            if self.debug:
                                sys.stdout.write("Converting stmt to assembly - MethodCall3 - Identifier arg detected: " +
                                    next_arg.value + "\n")

                            next_arg_in_reg = self._check_if_in_arguments(
                                next_arg.value,
                                md_args
                            )

                            if next_arg_in_reg:

                                # Since arguments have been pushed onto the stack,
                                # retrieve arguments from the stack instead
                                # with offset from stack pointer

                                arg_reg_stack_offset = ARG_REGISTER_TO_STACK_OFFSET[next_arg_in_reg]

                                instruction_load_next_argument = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + next_arg_reg + ",[sp,#" + \
                                        str(arg_reg_stack_offset) + "]\n"
                                )

                            else:

                                # Otherwise, retrieve arguments from stack
                                # with offset from frame pointer

                                var_offset = self.address_descriptor[next_arg.value]['offset']

                                instruction_load_next_argument = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + next_arg_reg + ",[fp,#-" + \
                                        str(var_offset) + "]\n"
                                )
                        # move to an argument register

                    arg_count += 1
                    next_arg = next_arg.child

                    self._link_instructions([
                        latest_instruction_load_argument,
                        instruction_load_next_argument
                    ])

                    latest_instruction_load_argument = instruction_load_next_argument

            instruction_load_arguments_last_child = instruction_load_arguments.get_last_child()

            instruction_branch_to_function= Instruction(
                self._get_incremented_instruction_count(),
                instruction="bl " + method_call_node.method_id[1:] + "\n"
            )

            instruction_move_return_value_to_x_register = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov " + x_register + ",a1\n"
            )

            self._link_instructions([
                instruction_load_arguments_last_child,
                instruction_branch_to_function,
                instruction_move_return_value_to_x_register
            ])

            # Pop argument registers onto the stack to save argument values
            # in case there are nested function calls

            instruction_save_arg_registers = Instruction(
                self._get_incremented_instruction_count(),
                instruction="stmfd sp!,{a1,a2,a3,a4}\n"
            )

            # Restore argument registers from stack to restore argument values
            # after nested function call

            instruction_pop_arg_registers = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldmfd sp!,{a1,a2,a3,a4}\n"
            )

            self._link_instructions([
                instruction_save_arg_registers,
                instruction_load_arguments
            ])

            self._link_instructions([
                instruction_move_return_value_to_x_register,
                instruction_pop_arg_registers
            ])

            new_instruction = instruction_save_arg_registers

        else:

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                    "x = y" + "\n")

            # x = y

            y_register = registers['y'][0]

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                    "x = y - y register: " + str(y_register) + "\n")
                sys.stdout.write("x register: " + str(x_register) + "\n")

            instruction_assign = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov " + x_register + "," + y_register + \
                    "\n",
            )

            # Load y if it is not an argument
            y_is_arg = self._check_if_in_arguments(
                assignment3node.assigned_value,
                md_args
            )

            if type(assignment3node.assigned_value) == ClassAttribute3Node:

                if assignment3node.assigned_value.object_name == "this":

                    # Load base address into a register
                    base_address_register = registers['y'][0]

                    instruction_load_base_address = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="mov " + base_address_register + ",a1\n",
                    )

                    self._update_descriptors(
                        register=base_address_register,
                        identifier="this"
                    )

                    # Calculate offset of class attribute in object

                    class_attribute_offset = self._calculate_class_attribute_offset(
                        class_name=assignment3node.assigned_value.class_name,
                        attribute_name=assignment3node.assigned_value.target_attribute
                    )

                else:

                    # Get base address of object
                    object_address_offset = self.address_descriptor[
                        assignment3node.assigned_value.object_name
                    ]['offset']

                    # Load base address into a register
                    base_address_register = registers['y'][0]

                    instruction_load_base_address = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="ldr " + base_address_register + ",[fp,#-" + \
                            str(object_address_offset) + "]\n",
                    )

                    self._update_descriptors(
                        register=base_address_register,
                        identifier=assignment3node.assigned_value.object_name
                    )

                    # Calculate offset of class attribute in object

                    class_attribute_offset = self._calculate_class_attribute_offset(
                        ir3_node=assignment3node.assigned_value
                    )

                # Generate instruction

                instruction_load_class_attribute = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + base_address_register + ",[" + base_address_register + \
                        ",#" + str(class_attribute_offset) + "]\n"
                )

                self._update_descriptors(
                    register=base_address_register,
                    identifier=assignment3node.assigned_value.__str__()
                )

                self._link_instructions([
                    instruction_load_base_address,
                    instruction_load_class_attribute,
                    instruction_assign
                ])

                new_instruction = instruction_load_base_address

            elif not y_is_arg and not assignment3node.assigned_value_is_raw_value:

                if self.debug:
                    sys.stdout.write("Testing: " + str(assignment3node.assigned_value_is_raw_value) + "\n")

                var_y_offset = self.address_descriptor[assignment3node.assigned_value]['offset']

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + y_register + ",[fp,#-" + \
                        str(var_y_offset) + "]\n"
                )

                self._update_descriptors(
                    register=y_register,
                    identifier=assignment3node.assigned_value
                )

                # Assign

                self._link_instructions([
                    new_instruction,
                    instruction_assign
                ])

            else:
                new_instruction = instruction_assign

        # Update descriptor for x if it is not an argument and not a class attribute

        if not x_is_arg:

            self._update_descriptors(
                register=x_register,
                identifier=assignment3node.identifier
            )

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                "Instruction: " + str(new_instruction) + "\n")

        if assignment3node.identifier not in REGISTERS and \
            not x_is_arg and \
            not type(assignment3node.assigned_value) == ClassInstance3Node:

            # If LHS of assignment is not a register, not an argument, and
            # it is not declaring a new object, then store the value of identifier
            # to stack

            sys.stdout.write("Converting stmt to assembly - updating register x of type: " + \
                str(type(assignment3node.identifier)) + "\n")

            new_instruction_last = new_instruction.get_last_child()

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - Assignment - " + \
                    "Last instruction: " + str(new_instruction_last) + "\n")
                sys.stdout.write("Converting stmt to assembly - Storing value of x: " + \
                    str(assignment3node.identifier) + " with type " + \
                    str(type(assignment3node.identifier))+ "\n")

            if type(assignment3node.identifier) == ClassAttribute3Node:
                # If class attribute

                if self.debug:
                    sys.stdout.write("Converting stmt to assembly - x is class attribute.\n")
                    sys.stdout.write("Converting stmt to assembly - object name: " + \
                        str(assignment3node.identifier.object_name) + "\n")

                if assignment3node.identifier.object_name == "this":

                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - x is this class attribute.\n")

                    # Load base address into a register from the first argument
                    base_address_register = registers['z'][0]

                    instruction_load_base_address = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="mov " + base_address_register + ",a1\n"
                    )

                    # Calculate offset of class attribute in object

                    if self.debug:
                        sys.stdout.write('Converting stmt to assembly - "this" class type: ' + \
                            str(assignment3node.identifier.class_name) + "\n")

                    class_attribute_offset = self._calculate_class_attribute_offset(
                        class_name=assignment3node.identifier.class_name,
                        attribute_name=assignment3node.identifier.target_attribute
                    )

                    if self.debug:
                        sys.stdout.write('Converting stmt to assembly - "this" class type attribute offset: ' + \
                            str(class_attribute_offset) + "\n")

                    # Generate instruction

                    instruction_store_to_class_attribute = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="str " + x_register + ",[" + base_address_register + \
                            ",#" + str(class_attribute_offset) + "]\n"
                    )

                    self._link_instructions([
                        new_instruction_last,
                        instruction_load_base_address,
                        instruction_store_to_class_attribute
                    ])

                    store_instruction = instruction_load_base_address

                else:
                    # Get base address of object
                    object_address_offset = self.address_descriptor[
                        assignment3node.identifier.object_name
                    ]['offset']

                    # Load base address into a register
                    base_address_register = registers['z'][0]

                    instruction_load_base_address = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="ldr " + base_address_register + ",[fp,#-" + \
                            str(object_address_offset) + "]\n"
                    )

                    # Calculate offset of class attribute in object

                    class_attribute_offset = self._calculate_class_attribute_offset(
                        ir3_node=assignment3node.identifier
                    )

                    # Generate instruction

                    instruction_store_to_class_attribute = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="str " + x_register + ",[" + base_address_register + \
                            ",#" + str(class_attribute_offset) + "]\n"
                    )

                    self._link_instructions([
                        new_instruction_last,
                        instruction_load_base_address,
                        instruction_store_to_class_attribute
                    ])

                    store_instruction = instruction_load_base_address

            else:

                x_identifier = assignment3node.identifier
                if x_identifier in self.address_descriptor:
                    # If variable
                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - Assignment" + \
                            " - Variable detected on LHS.\n")



                    var_fp_offset = self.address_descriptor[x_identifier]['offset']

                    if self.debug:
                        sys.stdout.write("Converting stmt to assembly - Storing value of x: " + \
                            str(assignment3node.identifier) + " with type " + \
                            str(type(assignment3node.identifier)) + " in register " + \
                            x_register + " with offset " + str(var_fp_offset) + "\n")

                    store_instruction = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="str " + x_register + ",[fp,#-" + \
                            str(var_fp_offset) + "]\n"
                    )

                    self._link_instructions([
                        new_instruction_last,
                        store_instruction
                    ])

        return new_instruction

    def _convert_return_to_assembly(
        self,
        ir3_node: Return3Node,
        md_args: List[str],
        liveness_data: Dict[str, List[int]],
        md_exit_label: str
    ) -> "Instruction":

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Return.\n")

        # Create method exit branch instruction

        instruction_branch_md_exit = Instruction(
            self._get_incremented_instruction_count(),
            instruction="b " + md_exit_label + "\n"
        )

        # Check if return value identifier is already in a register

        return_identifier = ir3_node.return_value

        return_identifier_reg = self._check_if_in_arguments(
            ir3_node.return_value,
            md_args
        )

        if return_identifier_reg:
            if self.debug:
                sys.stdout.write("Converting return statement to assembly - Already an argument.\n")

            instruction_move_to_argument_reg = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov a1," + return_identifier_reg + "\n"
            )

            self._link_instructions([
                instruction_move_to_argument_reg,
                instruction_branch_md_exit
            ])

            return instruction_move_to_argument_reg

        try:
            return_identifier_reg = self._check_if_in_register(return_identifier)[0]

            if self.debug:
                sys.stdout.write("Converting return statement to assembly - Already in register.\n")

            instruction_move_to_argument_reg = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov a1," + return_identifier_reg + "\n"
            )

            self._link_instructions([
                instruction_move_to_argument_reg,
                instruction_branch_md_exit
            ])

            return instruction_move_to_argument_reg

        except:

            return_identifier_reg = self._get_registers(
                ir3_node,
                md_args,
                liveness_data
            )['x'][0]

        # Check if identifier is in address descriptor
        try:
            return_identifier_offset = self.address_descriptor[return_identifier]['offset']

        except:
            return_identifier_offset = None

        if return_identifier_offset:

            new_instruction = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldr " + return_identifier_reg + ",[fp,#-" + \
                    str(return_identifier_offset) + "]" + "\n"
            )

            self._update_descriptors(
                register=return_identifier_reg,
                identifier=return_identifier
            )

            # Otherwise, load from stack

            instruction_move_to_argument_reg = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mov a1," + return_identifier_reg + "\n"
            )

            self._link_instructions([
                new_instruction,
                instruction_move_to_argument_reg,
                instruction_branch_md_exit
            ])

        else:

            # Otherwise, check if it is in class attribute

            # Get current class

            current_class = md_args[0][1]

            if self.debug:
                sys.stdout.write("Converting return statement to assembly - Checking for class attribute: " + \
                    str(ir3_node.return_value) + " in current class: " + str(current_class) + "\n")

            # Get offset

            class_attribute_offset = self._calculate_class_attribute_offset(
                class_name=current_class,
                attribute_name=ir3_node.return_value
            )

            if self.debug:
                sys.stdout.write("Converting return statement to assembly - Getting offset for class attribute " + \
                    str(ir3_node.return_value) + " in current class: " + str(current_class) + \
                    ": " + str(class_attribute_offset) + "\n")

            # Load base address + offset in register a1 into a1

            new_instruction = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldr a1,[a1,#" + str(class_attribute_offset) + "]\n"
            )

            self._link_instructions([
                new_instruction,
                instruction_branch_md_exit
            ])

        return new_instruction

    def _convert_if_goto_statement_to_assembly(
        self,
        ir3_node: IfGoTo3Node,
        md_args: List[str],
        liveness_data: Dict[str, List[int]]
    ) -> "Instruction":

        # Get registers

        registers = self._get_registers(
            ir3_node,
            md_args,
            liveness_data
        )

        y_reg = registers['y'][0]
        z_reg = registers['z'][0]

        if type(ir3_node.rel_exp) == str:

            if self.debug:
                sys.stdout.write("Converting if-goto to assembly - Identifier as condition.\n")

            rel_instruction = "beq "

            # Load identifier

            var_y_offset = self.address_descriptor[ir3_node.rel_exp]['offset']

            instruction_load_y_value = Instruction(
                self._get_incremented_instruction_count(),
                instruction="ldr " + y_reg + ",[fp,#-" + str(var_y_offset) + \
                    "]\n"
            )

            instruction_load_true_value = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mvn " + z_reg + ",#0\n"
            )

            # Compare

            instruction_compare = Instruction(
                self._get_incremented_instruction_count(),
                instruction="cmp " + y_reg + "," + z_reg + "\n"
            )

            self._link_instructions([
                instruction_load_y_value,
                instruction_load_true_value,
                instruction_compare
            ])

        elif type(ir3_node.rel_exp) == IR3Node:

            if self.debug:
                sys.stdout.write("Converting if-goto to assembly - Nested identifier as condition.\n")
                sys.stdout.write("Md args: " + str(md_args) + "\n")
                sys.stdout.write("Attribute identifier: " +str(ir3_node.rel_exp.value) + "\n")

            rel_instruction = "beq "

            # Load identifier

            var_y_offset = self._calculate_class_attribute_offset(
                attribute_name=ir3_node.rel_exp.value,
                class_name=md_args[0][1]
            )

            if self.debug:
                sys.stdout.write("Converting if-goto to assembly - Attribute offset: " +\
                    str(var_y_offset) + "\n")

            if type(var_y_offset) == int:

                if self.debug:
                    sys.stdout.write("Offset found in attribute")

                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + y_reg + ",[a1,#" + str(var_y_offset) + \
                        "]\n"
                )

            else:

                var_y_offset = self.address_descriptor[
                    ir3_node.rel_exp.value
                ]['offset']

                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + y_reg + ",[fp,#-" + str(var_y_offset) + \
                        "]\n"
                )

            if self.debug:
                sys.stdout.write("Converting if-goto to assembly - Offset: " + \
                    str(var_y_offset) + "\n")

            instruction_load_true_value = Instruction(
                self._get_incremented_instruction_count(),
                instruction="mvn " + z_reg + ",#0\n"
            )

            # Compare

            instruction_compare = Instruction(
                self._get_incremented_instruction_count(),
                instruction="cmp " + y_reg + "," + z_reg + "\n"
            )

            self._link_instructions([
                instruction_load_y_value,
                instruction_load_true_value,
                instruction_compare
            ])

        elif type(ir3_node.rel_exp) == RelOp3Node:

            if self.debug:
                sys.stdout.write("Converting if-goto to assembly - RelOp as condition.\n")

            # Load identifier

            var_y_is_arg = self._check_if_in_arguments(
                ir3_node.rel_exp.left_operand,
                md_args
            )

            if var_y_is_arg:
                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="mov " + y_reg + "," + var_y_is_arg + "\n"
                )

            else:

                var_y_offset = self.address_descriptor[
                    ir3_node.rel_exp.left_operand
                ]['offset']

                instruction_load_y_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + y_reg + ",[fp,#-" + str(var_y_offset) + \
                        "]\n"
                )

            var_z_is_arg = self._check_if_in_arguments(
                ir3_node.rel_exp.right_operand,
                md_args
            )

            if var_z_is_arg:
                instruction_load_z_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="mov " + z_reg + "," + var_z_is_arg + "\n"
                )

            else:

                var_z_offset = self.address_descriptor[
                    ir3_node.rel_exp.right_operand
                ]['offset']


                instruction_load_z_value = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="ldr " + z_reg + ",[fp,#-" + str(var_z_offset) + \
                        "]\n"
                )

            # Compare

            instruction_compare = Instruction(
                self._get_incremented_instruction_count(),
                instruction="cmp " + y_reg + "," + z_reg + \
                    "\n"
            )

            # If true, go to branch to set to True

            rel_instruction = REL_OP[ir3_node.rel_exp.operator]
            branch_index = self.branch_count
            self.branch_count += 1

            true_branch_label = "." + str(ir3_node.rel_exp.left_operand) + "_" + \
                str(ir3_node.rel_exp.right_operand) + "_true_" + str(branch_index)
            exit_branch_label = "." + str(ir3_node.rel_exp.left_operand) + "_" + \
                str(ir3_node.rel_exp.right_operand) + "_exit_" + str(branch_index)

            self._link_instructions([
                instruction_load_y_value,
                instruction_load_z_value,
                instruction_compare
            ])

        # Branch

        true_label = "." + str(ir3_node.goto)

        instruction_branch_to_true = Instruction(
            self._get_incremented_instruction_count(),
            instruction=rel_instruction + true_label + "\n"
        )

        self._link_instructions([
            instruction_compare,
            instruction_branch_to_true
        ])

        if type(ir3_node.rel_exp) == RelOp3Node:
            self._update_descriptors(
                register=y_reg,
                identifier=ir3_node.rel_exp.left_operand
            )
            self._update_descriptors(
                register=z_reg,
                identifier=ir3_node.rel_exp.right_operand
            )

        else:
            self._update_descriptors(
                register=y_reg,
                identifier=ir3_node.rel_exp
            )
            self._update_descriptors(
                register=z_reg,
                identifier='placeholder'
            )

        return instruction_load_y_value

    def _compile(
        self,
        f: TextIO,
        filename: str
    ) -> None:
        """
        Lexes, parses, type checks the input file, then generates
        the IR3 tree.

        :param TextIO f: the input file
        """
        self.ir3_generator.generate_ir3(f)
        self._convert_ir3_to_assembly(self.ir3_generator.ir3_tree)
        self._update_instruction_line_no()
        self._write_to_assembly_file()

    def _pretty_print(self) -> None:
        self.instruction_head.pretty_print()

    def _write_to_assembly_file(self) -> None:

        f = open("program.s", "w")

        completed = False
        current_instruction = self.instruction_head

        while not completed:

            if not current_instruction:
                completed = True
                break

            f.write(current_instruction.assembly_code)
            current_instruction = current_instruction.child

    def compile(
        self,
        f: TextIO,
        filename: str
    ) -> None:
        self._compile(f, filename)
        self._pretty_print()


def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. "
            "Please check the file name or extension.\n")

    else:

        optimize = False

        try:
            if sys.argv[2] == '-o':
                optimize = True
        except:
            pass

        filename = os.path.splitext(filepath)[0]
        sys.stdout.write(filename)
        f = open(filepath, 'r')
        c = Compiler(debug=True, optimize=optimize)
        c.compile(f, filename)

if __name__ == "__main__":

    __main__()
