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
)

from jlite_type import (
    BasicType,
)

REGISTER_DESCRIPTOR_START_STATE = {
    'v1': deque(),
    'v2': deque(),
    'v3': deque(),
    'v4': deque(),
    'v5': deque(),
}

REGISTERS = ['v1', 'v2', 'v3', 'v4', 'v5']

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
    ir3_generator: "IR3Generator"
    address_descriptor: Dict[str, List[str]]
    register_descriptor: Dict[str, List[str]]

    instruction_head: Optional["Instruction"]
    instruction_data_tail: Optional["Instruction"]
    instruction_tail: Optional["Instruction"]

    instruction_count: int
    data_label_count: int

    def __init__(
        self,
        debug: bool=False
    ) -> None:
        self.ir3_generator = IR3Generator()
        self.debug = debug

        self.instruction_count = self.data_label_count = 0

        self.instruction_head = self.instruction_data_tail = \
            self.instruction_tail = None

        self.address_descriptor = {}
        self.register_descriptor = REGISTER_DESCRIPTOR_START_STATE

    def _get_incremented_instruction_count(self) -> int:
        self.instruction_count += 1
        return self.instruction_count

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

    def _is_raw_value(self, value: str) -> bool:

        try:
            is_integer = int(value)
        except:
            is_integer = False

        if type(value) == str and \
                value[0] == '"' and \
                value[-1] == '"':

            is_string = True

        else:
            is_string = False

        if type(value) == str and \
            (value == 'true' or \
            value == 'false'):

            is_boolean = True

        else:
            is_boolean = False

        return is_integer or is_string or is_boolean

    def _check_if_in_register(
        self,
        identifier: str
    ) -> Optional[List[Any]]:

        try:
            x_address_descriptor = self.address_descriptor[identifier]['references']
            is_in_register = [i for i in REGISTERS if i in x_address_descriptor]

        except:

            is_in_register = None

        return is_in_register

    def _check_if_in_arguments(
        self,
        identifier: str,
        md_args: List[str]
    ) -> Optional[str]:

        try:
            arg_index = md_args.index(identifier)

            arg_register = {
                0: 'a1',
                1: 'a2',
                2: 'a3',
                3: 'a4',
            }[arg_index]

            return arg_register

        except:
            return None

    def _get_registers(
        self,
        ir3_node: Assignment3Node,
        md_args: List[str]
    ) -> Any:

        register_data = {}

        if self.debug:
            sys.stdout.write("\nGetting register for assigned value node of type: " + \
                str(type(ir3_node.assigned_value)) + " and value " + \
                str(ir3_node.assigned_value) + "\n")

        is_simple_assignment = self._is_raw_value(ir3_node.assigned_value)

        if is_simple_assignment:

            # Only requires one register for x = CONSTANT

            if self.debug:
                sys.stdout.write("Getting register for plain vanilla node.\n")

            # If x is an argument, use that register

            is_arg = self._check_if_in_arguments(
                ir3_node.identifier,
                md_args
            )

            if is_arg:
                register_data = {'x': is_arg}
                return register_data

            # If x is currently in a register, pick that register
            is_in_register = self._check_if_in_register(ir3_node.identifier)

            if is_in_register:

                if self.debug:
                    sys.stdout.write("Register found in address descriptor: " + \
                        str(is_in_register) + "\n")

                register_data = {'x': is_in_register[0]}
                return register_data

            # If x is not in a register, and there is a register currently empty,
            # pick that register

            if self.debug:
                sys.stdout.write("Getting register - current register descriptor: " +
                    str(self.register_descriptor) + "\n")

            for k, v in self.register_descriptor.items():

                if len(v) == 0:

                    if self.debug:
                        sys.stdout.write("Empty register found: " + \
                            str(k) + "\n")

                    register_data = {'x': k}
                    return register_data

            # If x is not in a register and no register is available:

            # 1. if there is an alternative location, it can be replaced

            # 2. if value in register = y [x = y + z], and y is not z, it can be replaced

            # 3. if value is not used later, it can be replaced

            # 4. Calculate spilling cost and replace register with lowest cost

        elif type(ir3_node.assigned_value) == BinOp3Node:

            if self.debug:
                sys.stdout.write("Getting register for binop node.\n")
                sys.stdout.write("Identifier: " + \
                    str(ir3_node.identifier) + "\n")
                sys.stdout.write("Left operand: " + \
                    str(ir3_node.assigned_value.left_operand) + "\n")
                sys.stdout.write("Right operand: " + \
                    str(ir3_node.assigned_value.right_operand) + "\n")

            left_operand_is_raw_value = self._is_raw_value(
                ir3_node.assigned_value.left_operand
            )

            y_value = None


            if not left_operand_is_raw_value:
                y_value = ir3_node.assigned_value.left_operand

            right_operand_is_raw_value = self._is_raw_value(
                ir3_node.assigned_value.right_operand
            )

            z_value = None
            if not right_operand_is_raw_value:
                z_value = ir3_node.assigned_value.right_operand

            required_registers = {
                'x': ir3_node.identifier,
                'y': y_value,
                'z': z_value
            }

            for k, v in required_registers.items():

                if self.debug:
                    sys.stdout.write("Getting register for binop node - " + k + \
                        "\n")

                if not v:
                    continue

                is_arg = self._check_if_in_arguments(
                    v,
                    md_args
                )

                if is_arg:
                    register_data[k] = is_arg
                    continue

                is_in_register = self._check_if_in_register(v)

                if is_in_register:

                    if self.debug:
                        sys.stdout.write("Register found in address descriptor: " + \
                            str(is_in_register) + "\n")

                    register_data[k] = is_in_register[0]
                    continue

                if self.debug:
                    sys.stdout.write("Register not found in address descriptor.\n")

                # If x is not in a register, and there is a register currently empty,
                # pick that register

                if self.debug:
                    sys.stdout.write("Getting register - current register descriptor: " +
                        str(self.register_descriptor) + "\n")

                for k2, v2 in self.register_descriptor.items():

                    if len(v2) == 0:

                        if self.debug:
                            sys.stdout.write("Empty register found: " + \
                                str(k) + "\n")

                        register_data[k] = k2
                        break
        else:

            # x = y

            if self.debug:
                sys.stdout.write("Getting register for double identifiers.\n")

            required_registers = {
                'x': ir3_node.identifier,
                'y': ir3_node.assigned_value,
            }

            for k, v in required_registers.items():

                if self.debug:
                    sys.stdout.write("Getting register for binop node - " + k + \
                        "\n")

                if not v:
                    continue

                is_in_register = self._check_if_in_register(v)

                if is_in_register:

                    if self.debug:
                        sys.stdout.write("Register found in address descriptor: " + \
                            str(is_in_register) + "\n")

                    register_data[k] = is_in_register[0]
                    continue

                if self.debug:
                    sys.stdout.write("Register not found in address descriptor.\n")

                # If x is not in a register, and there is a register currently empty,
                # pick that register

                if self.debug:
                    sys.stdout.write("Getting register - current register descriptor: " +
                        str(self.register_descriptor) + "\n")

                for k2, v2 in self.register_descriptor.items():

                    if len(v2) == 0:

                        if self.debug:
                            sys.stdout.write("Empty register found: " + \
                                str(k) + "\n")

                        register_data[k] = k2
                        break

        return register_data

    def _update_descriptors(
        self,
        register: str,
        identifier: str
    ) -> None:

        if self.debug:
            sys.stdout.write("\nDescriptors before update.\n")
            sys.stdout.write("Register descriptor: " + str(self.register_descriptor) + \
                "\n")
            sys.stdout.write("Address descriptor: " + str(self.address_descriptor) + \
                "\n")

        # Save current references in register

        current_register_reference = self.register_descriptor[register]

        # Remove register references in address descriptor

        if current_register_reference:
            for r in current_register_reference:
                try:
                    self.address_descriptor[r]['references'].remove(register)
                except:
                    pass

        # Set register to identifier in register descriptor

        self.register_descriptor[register] = deque([identifier])

        # Set identifier to register in address descriptor

        self.address_descriptor[identifier]['references'].append(register)

        if self.debug:
            sys.stdout.write("\nDescriptors updated.\n")
            sys.stdout.write("Register descriptor: " + str(self.register_descriptor) + \
                "\n")
            sys.stdout.write("Address descriptor: " + str(self.address_descriptor) + \
                "\n")

    def _reset_descriptors(self) -> None:

        self.address_descriptor = {}
        self.register_descriptor = REGISTER_DESCRIPTOR_START_STATE

    def _initialise_assembler_directive(self) -> "Instruction":

        instruction_data = Instruction(
            self._get_incremented_instruction_count(),
            instruction=".data\n\n",
        )

        instruction_L1 = Instruction(
            self._get_incremented_instruction_count(),
            instruction="L1:\n.text\n.global main\n\n",
            parent=instruction_data
        )

        instruction_data.set_child(instruction_L1)

        return instruction_data

    def _convert_ir3_to_assembly(self, ir3_tree: "IR3Tree") -> None:

        self.instruction_count = self.data_label_count = 0
        self.instruction_head = self.instruction_data_tail = \
            self.instruction_tail = None

        self._reset_descriptors()

        self.instruction_head = self.instruction_data_tail = \
        self._initialise_assembler_directive()
        self.instruction_tail = self.instruction_head.get_last_child()

        current_node = ir3_tree.head.method_data
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
                current_tail.set_child(instruction)
                instruction.set_parent(current_tail)
                self.instruction_tail = instruction.get_last_child()

                current_node = current_node.child

    def _convert_cmtd3_to_assembly(
        self,
        ir3_node: "CMtd3Node",
        ir3_class_data: "CData3Node"
    ) -> "Instruction":

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
            instruction="stmfd sp!,{v1,v2,v3,v4,v5,fp,lr}\n",
            parent=instruction_start_label,
        )

        instruction_start_label.set_child(instruction_push_callee_saved)

        instruction_set_frame_pointer = Instruction(
            self._get_incremented_instruction_count(),
            instruction="add fp,sp,#24\n",
            parent=instruction_push_callee_saved
        )

        instruction_push_callee_saved.set_child(instruction_set_frame_pointer)

        # Set aside space for variable declarations

        var_decl_offset = self._calculate_offset_for_md_vardecl(
            ir3_node,
            ir3_class_data
        )

        instruction_set_space_for_var_decl = Instruction(
            self._get_incremented_instruction_count(),
            instruction="sub sp,fp,#" + str(var_decl_offset) + "\n",
            parent=instruction_set_frame_pointer
        )

        instruction_set_frame_pointer.set_child(instruction_set_space_for_var_decl)

        # Convert statements to assembly code

        md_args = ir3_node.get_arguments()

        stmt_start_instruction = self._convert_stmt_to_assembly(
            ir3_node.statements,
            md_args
        )
        stmt_end_instruction = stmt_start_instruction.get_last_child()

        instruction_set_space_for_var_decl.set_child(stmt_start_instruction)
        stmt_start_instruction.set_parent(instruction_set_space_for_var_decl)

        # Restore callee-saved registers

        instruction_reset_frame_pointer = Instruction(
            self._get_incremented_instruction_count(),
            instruction="sub sp,fp,#24\n",
            parent=stmt_end_instruction
        )

        stmt_end_instruction.set_child(instruction_reset_frame_pointer)

        instruction_pop_callee_saved = Instruction(
            self._get_incremented_instruction_count(),
            instruction="ldmfd sp!,{v1,v2,v3,v4,v5,fp,pc}\n",
            parent=instruction_reset_frame_pointer
        )

        instruction_reset_frame_pointer.set_child(instruction_pop_callee_saved)

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

                # If variable is a basic type
                if current_var_decl.type in [
                    BasicType.INT,
                    BasicType.STRING,
                    BasicType.BOOL
                ]:

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

                            for a in object_attributes:

                                # For each class attribute, increment the offset
                                # and declare a new variable

                                fp_offset += 4

                                a_identifier = current_var_decl.value + "." + \
                                    a

                                self._declare_new_variable(
                                    a_identifier,
                                    fp_offset
                                )

                            completed = True
                            break

                        current_class_data = current_class_data.child

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
        md_args: List[str]
    ) -> "Instruction":

        if self.debug:
            sys.stdout.write("Converting stmt to assembly - Args: " + \
                str(md_args) + "\n")

        first_instruction = None
        current_instruction = None
        new_instruction = None

        current_stmt = ir3_node
        completed = False

        debug_count = 0

        while not completed:

            if self.debug:
                sys.stdout.write("Converting stmt to assembly - current stmt: " + \
                    str(type(current_stmt)) + "\n")

            if not current_stmt:
                completed = True
                break

            if type(current_stmt) == PrintLn3Node:

                new_instruction = self._convert_println_to_assembly(
                    current_stmt,
                    current_instruction
                )

            elif type(current_stmt) == Assignment3Node:

                registers = self._get_registers(
                    current_stmt,
                    md_args
                )

                if self.debug:
                    sys.stdout.write("Registers obtained: " + str(registers) + \
                        "\n")

                x_is_arg = self._check_if_in_arguments(
                    current_stmt.identifier,
                    md_args
                )

                x_register = registers['x']

                is_simple_assignment = self._is_raw_value(
                    current_stmt.assigned_value
                )

                if is_simple_assignment:

                    # x = CONSTANT
                    new_instruction = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="mov " + x_register + ",#" + \
                            str(current_stmt.assigned_value) + "\n"
                    )

                    self._update_descriptors(
                        register=x_register,
                        identifier=current_stmt.identifier
                    )

                elif type(current_stmt.assigned_value) == BinOp3Node:

                    # x = y + z

                    # Check if y is raw value

                    y_is_arg = self._check_if_in_arguments(
                        current_stmt.assigned_value.left_operand,
                        md_args
                    )

                    y_is_raw = self._is_raw_value(
                        current_stmt.assigned_value.left_operand
                    )

                    y_value = current_stmt.assigned_value.left_operand
                    if not y_is_raw:
                        y_value = registers['y']

                    # Check if z is raw value

                    z_is_arg = self._check_if_in_arguments(
                        current_stmt.assigned_value.right_operand,
                        md_args
                    )

                    z_is_raw = self._is_raw_value(
                        current_stmt.assigned_value.right_operand
                    )

                    z_value = current_stmt.assigned_value.right_operand
                    if not z_is_raw:
                        z_value = registers['z']

                    # Actual assignment

                    if current_stmt.assigned_value.operator == '+':

                        if y_is_raw:
                            # If y is a raw value

                            instruction_binop = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction="add " + x_register + "," + z_value + \
                                    ",#" + str(y_value) + "\n"
                            )

                            if not z_is_arg:

                                # If z is not an argument, load z

                                var_z_offset = self.address_descriptor[current_stmt.assigned_value.right_operand]['offset']

                                new_instruction = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + z_value + ",[fp,#-]" + \
                                        str(var_z_offset) + "\n"
                                )

                                self._update_descriptors(
                                    register=z_value,
                                    identifier=current_stmt.assigned_value.right_operand
                                )

                                instruction_binop.set_parent(new_instruction)
                                new_instruction.set_child(instruction_binop)

                            elif z_is_arg:

                                # If z is an argument

                                new_instruction = instruction_binop

                        elif z_is_raw:

                        # If z is a raw value

                            instruction_binop = Instruction(
                                self._get_incremented_instruction_count(),
                                instruction="add " + x_register + "," + y_value + \
                                    ",#" + str(z_value) + "\n"
                            )

                            if not y_is_arg:

                                # If y is not an argument, load y

                                var_y_offset = self.address_descriptor[current_stmt.assigned_value.left_operand]['offset']

                                new_instruction = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + y_value + ",[fp,#-" + \
                                        str(var_y_offset) + "]\n"
                                )

                                self._update_descriptors(
                                    register=y_value,
                                    identifier=current_stmt.assigned_value.left_operand
                                )

                                instruction_binop.set_parent(new_instruction)
                                new_instruction.set_child(instruction_binop)

                            elif y_is_arg:

                                # If z is a raw value, load y

                                new_instruction = instruction_binop

                        else:

                            # Load y and z

                            if not y_is_arg and not z_is_arg:

                                var_y_offset = self.address_descriptor[current_stmt.assigned_value.left_operand]['offset']

                                new_instruction = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + y_value + ",[fp,#-" + \
                                        str(var_y_offset) + "]\n"
                                )

                                self._update_descriptors(
                                    register=y_value,
                                    identifier=current_stmt.assigned_value.left_operand
                                )

                                var_z_offset = self.address_descriptor[current_stmt.assigned_value.right_operand]['offset']

                                instruction_load_z = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + z_value + ",[fp,#-" + \
                                        str(var_z_offset) + "]\n",
                                    parent=new_instruction
                                )

                                self._update_descriptors(
                                    register=z_value,
                                    identifier=current_stmt.assigned_value.right_operand
                                )

                                new_instruction.set_child(instruction_load_z)

                                instruction_binop = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="add " + x_register + "," + y_value + \
                                        "," + z_value + "\n",
                                    parent=instruction_load_z
                                )

                                instruction_load_z.set_child(instruction_binop)

                            elif y_is_arg and not z_is_arg:

                                var_z_offset = self.address_descriptor[current_stmt.assigned_value.right_operand]['offset']

                                new_instruction = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + z_value + ",[fp,#-" + \
                                        str(var_z_offset) + "]\n",
                                    parent=new_instruction
                                )

                                self._update_descriptors(
                                    register=z_value,
                                    identifier=current_stmt.assigned_value.right_operand
                                )

                                instruction_binop = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="add " + x_register + "," + y_value + \
                                        "," + z_value + "\n",
                                    parent=instruction_load_z
                                )

                                new_instruction.set_child(instruction_binop)

                            elif not y_is_arg and z_is_arg:

                                var_y_offset = self.address_descriptor[current_stmt.assigned_value.left_operand]['offset']

                                new_instruction = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="ldr " + y_value + ",[fp,#-" + \
                                        str(var_y_offset) + "]\n"
                                )

                                self._update_descriptors(
                                    register=y_value,
                                    identifier=current_stmt.assigned_value.left_operand
                                )

                                instruction_binop = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="add " + x_register + "," + y_value + \
                                        "," + z_value + "\n",
                                    parent=instruction_load_z
                                )

                                if not x_is_arg:
                                    self._update_descriptors(
                                        register=x_register,
                                        identifier=current_stmt.identifier
                                    )

                                new_instruction.set_child(instruction_binop)

                            elif y_is_arg and z_is_arg:

                                new_instruction = Instruction(
                                    self._get_incremented_instruction_count(),
                                    instruction="add " + x_register + "," + y_value + \
                                        "," + z_value + "\n",
                                )

                else:

                    # x = y

                    y_register = registers['y']

                    instruction_assign = Instruction(
                        self._get_incremented_instruction_count(),
                        instruction="mov " + x_register + "," + y_register + \
                            "\n",
                    )

                    # Load y if it is not an argument

                    if not y_is_arg:

                        var_y_offset = self.address_descriptor[current_stmt.assigned_value]['offset']

                        new_instruction = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="ldr " + y_register + ",[fp,#-" + \
                                str(var_y_offset) + "]\n"
                        )

                        self._update_descriptors(
                            register=y_register,
                            identifier=current_stmt.assigned_value
                        )

                        # Assign

                        instruction_assign.set_parent(new_instruction)
                        new_instruction.set_child(instruction_assign)

                    else:
                        new_instruction = instruction_assign

                # Update descriptor for x if it is not an argument

                if not x_is_arg:

                    self._update_descriptors(
                        register=x_register,
                        identifier=current_stmt.identifier
                    )

                if current_stmt.identifier not in REGISTERS and not x_is_arg:

                    new_instruction_last = new_instruction.get_last_child()

                    # If RHS of assignment is not a register

                    if current_stmt.identifier in self.address_descriptor:
                        # If variable
                        if self.debug:
                            sys.stdout.write("Converting stmt to assembly - Assignment" + \
                                " - Variable detected on RHS.\n")

                        var_fp_offset = self.address_descriptor[current_stmt.identifier]['offset']

                        store_instruction = Instruction(
                            self._get_incremented_instruction_count(),
                            instruction="str " + x_register + ",[fp,#-" + \
                                str(var_fp_offset) + "]\n",
                            parent=new_instruction_last
                        )

                        new_instruction_last.set_child(store_instruction)

                    else:
                        # If class attribute
                        pass

            elif type(current_stmt) == VarDecl3Node:
                new_instruction = None
                current_stmt = current_stmt.child
                continue

            else:

                new_instruction = Instruction(
                    self._get_incremented_instruction_count(),
                    instruction="Test test " + str(debug_count) + "\n",
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
                debug_count += 1

            new_instruction = None
            current_stmt = current_stmt.child

        return first_instruction

    def _convert_println_to_assembly(
        self,
        println3node: PrintLn3Node,
        current_instruction: Optional["Instruction"],
    ) -> "Instruction":

        print_data_label = "d" + str(self.data_label_count)
        self.data_label_count += 1

        if println3node.type == BasicType.INT:

            if self.debug:
                sys.stdout.write("Converting println to assembly - Integer detected.\n")

            try:
            # Check if it is integer
                print_data = int(println3node.expression)
                instruction_load_print_value_assembly_code = "mov a2,#" + \
                    str(print_data) + "\n"

            except:

                if self.debug:
                    sys.stdout.write("Converting println to assembly - Expression: " + \
                        str(println3node.expression) + "\n")

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
                sys.stdout.write("Converting println to assembly - expression: " + \
                    str(println3node.expression) + "\n")

            # Check if it is a string

            if println3node.expression[0] == '"' and \
                println3node.expression[-1] == '"':
                if self.debug:
                    sys.stdout.write("Converting println to assembly - String detected.\n")

                instruction_load_print_value_assembly_code = "mov a2,#0\n"

                instruction_initialise_print_data_assembly_code = print_data_label + \
                    ": .asciz " + println3node.expression + "\n"

            # Otherwise, lookup symbol table
            else:

                if self.debug:
                    sys.stdout.write("Converting println to assembly - Identifier detected.\n")

                instruction_load_print_value_assembly_code = "mov a2,#100\n"

                instruction_initialise_print_data_assembly_code = print_data_label + \
                    ": .asciz " + '\"Just a variable\"' + "\n"

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

        if current_instruction:
            current_instruction.set_child(instruction_load_print_data)

        instruction_load_print_value = Instruction(
            self._get_incremented_instruction_count(),
            instruction=instruction_load_print_value_assembly_code,
            parent=instruction_load_print_data
        )

        instruction_load_print_data.set_child(instruction_load_print_value)

        instruction_printf = Instruction(
            self._get_incremented_instruction_count(),
            instruction="bl printf\n",
            parent=instruction_load_print_value
        )

        instruction_load_print_value.set_child(instruction_printf)

        return instruction_load_print_data

    def _convert_assignment_to_assembly(
        self,
        assignment3node: Assignment3Node,
        current_instruction: Optional["Instruction"],
    ) -> "Instruction":

        pass

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

        self._write_to_assembly_file(filename)

    def _pretty_print(self) -> None:
        self.instruction_head.pretty_print()

    def _write_to_assembly_file(self, filename: str) -> None:

        f = open(filename + ".s", "w")

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
        filename = os.path.splitext(filepath)[0]
        sys.stdout.write(filename)
        f = open(filepath, 'r')
        c = Compiler(debug=True)
        c.compile(f, filename)

if __name__ == "__main__":

    __main__()
