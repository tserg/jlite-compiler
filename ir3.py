import sys

from typing import (
    Deque,
    Dict,
    List,
    Optional,
    Any,
    Union,
    Tuple,
)

from ast import (
    BasicType,
    FunctionType,
)

class IR3Node:
    """
    Node instance for a valid expression

    ...

    Attributes
    ----------
    value: str
    type: str
    child: Any

    Methods
    -------
    add_child(IR3Node):
        Set a node as its child.
    pretty_print():
        Print the current value of the node in syntax format, and its child
        recursively.

    """

    value: str
    type: Any
    #is_identifier: bool
    md_line_no: Optional[int]
    md_basic_block_line_no: Optional[int]
    md_basic_block_no: Optional[int]
    child: Any
    is_raw_value: bool

    #def_set: List[str]
    #use_set: List[str]
    #liveness_data: Optional[Any]

    def __init__(
        self,
        value: str='',
        type: str='',
        #is_identifier: bool=False,
        child: Optional[Any]=None,
        is_raw_value: bool=False
    ) -> None:
        self.value = value
        self.type = type
        #self.is_identifier = is_identifier
        self.child = child
        self.md_line_no = None
        self.md_basic_block_no = None
        self.md_basic_block_line_no = None
        self.is_raw_value = is_raw_value

        #self.def_set = []
        #self.use_set = []
        #self.liveness_data = None

    def add_child(self, node: Any) -> None:
        """
        Set a node as child

        :param Any node: Node to set as child
        """
        self.child = node

    def set_md_line_no(self, line_no: int) -> None:
        self.md_line_no = line_no

    def set_md_basic_block_no(self, block_no: int) -> None:
        self.md_basic_block_no = block_no

    def set_md_basic_block_line_no(self, line_no: int) -> None:
        self.md_basic_block_line_no = line_no

    '''
    def set_liveness_data(self, liveness_data: Any) -> None:
        self.liveness_data = liveness_data

    def add_to_def_set(self, identifier: str) -> None:

        self.def_set.append(identifier)

    def add_to_use_set(self, identifier: str) -> None:

        self.use_set.append(identifier)
    '''
    
    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.value))

        if self.child:
            sys.stdout.write(delimiter)
            self.child.pretty_print(delimiter, preceding)

class Program3Node(IR3Node):

    class_data: Any
    method_data: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.class_data = None
        self.method_data = None

    def set_class_data(self, class_data: Any) -> None:
        self.class_data = class_data

    def set_method_data(self, method_data: Any) -> None:
        self.method_data = method_data

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write("\n======= CData3 =======\n\n")

        if self.class_data:
            self.class_data.pretty_print()

        sys.stdout.write("=======CMtd3 =======\n\n")

        if self.method_data:
            self.method_data.pretty_print()

        sys.stdout.write("\n=====fx== End of IR3 Program =======\n")

class CData3Node(IR3Node):

    class_name: str
    var_decl: Any

    def __init__(self, class_name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.class_name = class_name
        self.var_decl = None

    def set_var_decl(self, var_decl: Any) -> None:
        self.var_decl = var_decl

    def get_var_decl_identifiers(self) -> List[str]:

        result = []

        completed = False
        current_var_decl = self.var_decl

        while not completed:

            if not current_var_decl:
                completed = True
                break

            result.append(current_var_decl.value)

            current_var_decl = current_var_decl.child

        return result

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write("class " + self.class_name + "{\n" )

        if self.var_decl:
            self.var_decl.pretty_print(preceding='  ')

        sys.stdout.write("}\n\n")

        if self.child:
            self.child.pretty_print()

class CMtd3Node(IR3Node):

    return_type: Any
    method_id: str
    arguments: Any
    variable_declarations: Any
    statements: Any

    def __init__(
        self,
        method_id: str,
        return_type: Any,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.variable_declarations = None
        self.method_id = method_id
        self.return_type = return_type

    def set_return_type(self, return_type: str) -> None:
        self.return_type = return_type

    def set_arguments(self, node: Any) -> None:
        self.arguments = node

    def set_variable_declarations(self, node: Any) -> None:
        self.variable_declarations = node

    def set_statements(self, node: Any) -> None:
        self.statements = node

    def get_arguments(self) -> List[str]:

        result = []

        completed = False
        current_arg = self.arguments

        while not completed:

            if not current_arg:
                completed = True
                break

            result.append((current_arg.value, current_arg.type))

            current_arg = current_arg.child

        return result

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.return_type) + " " + self.method_id + "(")

        self.arguments.pretty_print()

        sys.stdout.write(") {\n")

        if self.variable_declarations:
            self.variable_declarations.pretty_print(preceding='  ')

        if self.statements:
            self.statements.pretty_print(preceding='  ')

        sys.stdout.write("}\n\n")

        if self.child:
            self.child.pretty_print()

class VarDecl3Node(IR3Node):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        if type(self.type) == BasicType:
            sys.stdout.write(preceding + str(self.type) + " " + \
                str(self.value) + ";\n")

        elif type(self.type) == tuple:

            sys.stdout.write(preceding + str(self.type[1]) + " " + \
            str(self.value) + ";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class Arg3Node(IR3Node):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        if type(self.type) == BasicType:

            sys.stdout.write(str(self.type) + " " + str(self.value))

        elif type(self.type) == tuple:
            sys.stdout.write(str(self.type[1]) + " " + str(self.value))

        else:
            sys.stdout.write(str(self.type) + " " + str(self.value))

        if self.child:
            sys.stdout.write(", ")
            self.child.pretty_print(delimiter, preceding)

class Label3Node(IR3Node):

    label_id: int

    def __init__(self, label_id: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.label_id = label_id

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding[:-1] + "Label " + str(self.label_id) + ":\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class IfGoTo3Node(IR3Node):

    rel_exp: Any
    goto: int

    def __init__(self, rel_exp: Any, goto: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rel_exp = rel_exp
        self.goto = goto

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "if (")

        if type(self.rel_exp) == str:
            sys.stdout.write(self.rel_exp)
        else:
            self.rel_exp.pretty_print()

        sys.stdout.write(") goto " + str(self.goto) + ";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class GoTo3Node(IR3Node):

    goto: int

    def __init__(self, goto: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.goto = goto

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "goto " + str(self.goto) + ";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class ReadLn3Node(IR3Node):

    id3: Any

    def __init__(self, id3: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id3 = id3

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "readln(")

        if self.id3:
            sys.stdout.write(str(self.id3))

        sys.stdout.write(");\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class PrintLn3Node(IR3Node):

    expression: str

    def __init__(self, expression: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.expression = expression

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "println(")

        sys.stdout.write(str(self.expression))

        sys.stdout.write(");\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class ClassInstance3Node(IR3Node):

    target_class: str

    def __init__(self, target_class: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.target_class = target_class

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "new " + str(self.target_class) + "()")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class ClassAttribute3Node(IR3Node):

    object_name: str
    target_attribute: str
    class_name: str

    def __init__(
        self,
        object_name: str,
        target_attribute: str,
        class_name: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.object_name = object_name
        self.target_attribute = target_attribute
        self.class_name = class_name

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + str(self.object_name) + \
            "." + str(self.target_attribute))

        if self.child:
            self.child.pretty_print(delimiter, preceding)

    def __str__(self):

        return self.object_name + "." + self.target_attribute

class Assignment3Node(IR3Node):

    identifier: Any
    assigned_value: Any
    assigned_value_is_raw_value: bool

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.identifier = None
        self.assigned_value = None
        self.assigned_value_is_raw_value = False

    def set_identifier(self, identifier: Any) -> None:
        self.identifier = identifier

    def set_assigned_value(
        self,
        assigned_value: Any,
        assigned_value_is_raw_value: bool=False
    ) -> None:
        self.assigned_value = assigned_value
        self.assigned_value_is_raw_value = assigned_value_is_raw_value

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding)
        if isinstance(self.identifier, IR3Node):
            self.identifier.pretty_print()
        else:
            sys.stdout.write(self.identifier)
        sys.stdout.write(" = ")

        if self.assigned_value:
            try:
                self.assigned_value.pretty_print(delimiter='')
            except:
                sys.stdout.write(str(self.assigned_value))

        sys.stdout.write(";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class MethodCall3Node(IR3Node):

    method_id: str
    arguments: Any
    return_type: Any

    def __init__(
        self,
        method_id: str,
        return_type: Any,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.method_id = method_id
        self.arguments = None
        self.return_type = return_type

    def set_arguments(self, arguments: Any) -> None:
        self.arguments = arguments

    def set_return_type(self, return_type: Any) -> None:
        self.return_type = return_type

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.method_id) + "(")

        if self.arguments:
            self.arguments.pretty_print(delimiter=",")

        sys.stdout.write(")")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class Return3Node(IR3Node):

    return_value: Any

    def __init__(self, return_value: Any=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.return_value = return_value

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "Return")

        if self.return_value:
            sys.stdout.write(" " + str(self.return_value))


        sys.stdout.write(";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class RelOp3Node(IR3Node):

    left_operand: Any
    right_operand: Any
    operator: str

    left_operand_is_raw_value: bool
    right_operand_is_raw_value: bool

    def __init__(
        self,
        left_operand: str,
        right_operand: str,
        operator: str,
        left_operand_is_raw_value: bool,
        right_operand_is_raw_value: bool,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.left_operand = left_operand
        self.right_operand = right_operand
        self.operator = operator
        self.left_operand_is_raw_value = left_operand_is_raw_value
        self.right_operand_is_raw_value = right_operand_is_raw_value


    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.left_operand) + " " + str(self.operator) + \
            " " + str(self.right_operand))

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class BinOp3Node(IR3Node):

    left_operand: Any
    right_operand: Any
    operator: str

    left_operand_is_raw_value: bool
    right_operand_is_raw_value: bool

    def __init__(
        self,
        left_operand: Any,
        right_operand: Any,
        operator: str,
        left_operand_is_raw_value: bool=False,
        right_operand_is_raw_value: bool=False,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.left_operand = left_operand
        self.right_operand = right_operand
        self.operator = operator
        self.left_operand_is_raw_value = left_operand_is_raw_value
        self.right_operand_is_raw_value = right_operand_is_raw_value

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        if type(self.left_operand) != IR3Node and \
            type(self.right_operand) != IR3Node:

            sys.stdout.write(str(self.left_operand) + \
                " " + str(self.operator) + " " + str(self.right_operand))

        elif type(self.left_operand) != IR3Node:
            sys.stdout.write("\n")

            sys.stdout.write(str(self.left_operand) + " " + \
                str(self.operator) + " ")
            self.right_operand.pretty_print()

        elif type(self.right_operand) != IR3Node:
            sys.stdout.write("\n")
            self.left_operand.pretty_print()
            sys.stdout.write(" " + str(self.operator) + " " + \
                str(self.right_operand))

        else:

            self.left_operand.pretty_print()
            sys.stdout.write(" " + str(self.operator) + " ")
            self.right_operand.pretty_print()

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class UnaryOp3Node(IR3Node):

    operand: Any
    operator: str

    def __init__(
        self,
        operand: Any,
        operator: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.operand = operand
        self.operator = operator

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.operator) + str(self.operand))

        if self.child:
            self.child.pretty_print(delimiter, preceding)

class IR3Tree:

    head: Any

    def __init__(self, head: Any) -> None:

        self.head = head

    def pretty_print(self) -> None:

        if self.head:
            self.head.pretty_print()
