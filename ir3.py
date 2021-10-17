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
    FunctionType
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
    sibling: Any

    Methods
    -------
    pretty_print():
        Print the current value of the node in syntax format, and its child and sibling recursively.
    add_child(node):
        Set a node as its child. Child is traversed before sibling.
    add_sibling(node):
        Set a node as its sibling. Sibling is traversed after child (and sub-childs).

    """

    value: str
    type: Any
    #is_identifier: bool
    child: Any
    sibling: Any

    def __init__(
        self,
        value: str='',
        type: str='',
        #is_identifier: bool=False,
        child: Optional[Any]=None,
        sibling: Optional[Any]=None
    ) -> None:
        self.value = value
        self.type = type
        #self.is_identifier = is_identifier
        self.child = child
        self.sibling = sibling

    def add_child(self, node: Any) -> None:
        """
        Set a node as child

        :param Any node: Node to set as child
        """
        self.child = node

    def add_sibling(self, node: Any) -> None:
        """
        Set a node as sibling

        :param Any node: Node to set as sibling
        """
        self.sibling = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.value))

        if self.child:
            sys.stdout.write(delimiter)
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

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

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write("class " + self.class_name + "{\n" )

        if self.var_decl:
            self.var_decl.pretty_print(preceding='  ')

        sys.stdout.write("}\n\n")

        if self.child:
            self.child.pretty_print()

        if self.sibling:
            self.sibling.pretty_print()

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

        if self.sibling:
            self.sibling.pretty_print()

class VarDecl3Node(IR3Node):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        if type(self.type) == BasicType:
            sys.stdout.write(preceding + str(self.type) + " " + str(self.value) + ";\n")

        elif type(self.type) == tuple:
            #sys.stdout.write(str(self.type))
            sys.stdout.write(preceding + str(self.type[1]) + " " + str(self.value) + ";\n")

        if self.child:

            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

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

        if self.sibling:

            self.sibling.pretty_print(delimiter, preceding)

class Label3Node(IR3Node):

    label_id: int

    def __init__(self, label_id: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.label_id = label_id

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding[:-1] + "Label " + str(self.label_id) + ":\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

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

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class GoTo3Node(IR3Node):

    goto: int

    def __init__(self, goto: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.goto = goto

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "goto " + str(self.goto) + ";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

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

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

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

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ClassInstance3Node(IR3Node):

    target_class: str

    def __init__(self, target_class: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.target_class = target_class

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "new " + str(self.target_class) + "()")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ClassAttribute3Node(IR3Node):

    target_class: str
    target_attribute: str

    def __init__(
        self,
        target_class: str,
        target_attribute: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.target_class = target_class
        self.target_attribute = target_attribute

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + str(self.target_class) + \
            "." + str(self.target_attribute))

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class Assignment3Node(IR3Node):

    identifier: Any
    assigned_value: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.identifier = None
        self.assigned_value = None

    def set_identifier(self, identifier: Any) -> None:
        self.identifier = identifier

    def set_assigned_value(self, assigned_value: Any) -> None:
        self.assigned_value = assigned_value

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

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class MethodCall3Node(IR3Node):

    method_id: str
    arguments: Any

    def __init__(
        self,
        method_id: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.method_id = method_id
        self.arguments = None

    def set_arguments(self, arguments: Any) -> None:
        self.arguments = arguments

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(str(self.method_id) + "(")

        if self.arguments:
            self.arguments.pretty_print(delimiter=",")

        sys.stdout.write(")")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class Return3Node(IR3Node):

    return_value: Any

    def __init__(self, return_value: Any=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.return_value = return_value

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + "Return " + str(self.return_value))

        sys.stdout.write(";\n")

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class RelOp3Node(IR3Node):

    left_operand: Any
    right_operand: Any
    operator: str

    def __init__(
        self,
        left_operand: str,
        right_operand: str,
        operator: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.left_operand = left_operand
        self.right_operand = right_operand
        self.operator = operator

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(str(self.left_operand) + " " + str(self.operator) + " " + str(self.right_operand))

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class BinOp3Node(IR3Node):

    left_operand: Any
    right_operand: Any
    operator: str

    def __init__(
        self,
        left_operand: Any,
        right_operand: Any,
        operator: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.left_operand = left_operand
        self.right_operand = right_operand
        self.operator = operator

    def pretty_print(self, delimiter: str='', preceding: str=''):

        if type(self.left_operand) != IR3Node and type(self.right_operand) != IR3Node:
            sys.stdout.write(str(self.left_operand) + \
                " " + str(self.operator) + " " + str(self.right_operand))

        elif type(self.left_operand) != IR3Node:
            sys.stdout.write("\n")

            sys.stdout.write(str(self.left_operand) + " " + str(self.operator) + " ")
            self.right_operand.pretty_print()

        elif type(self.right_operand) != IR3Node:
            sys.stdout.write("\n")
            self.left_operand.pretty_print()
            sys.stdout.write(" " + str(self.operator) + " " + str(self.right_operand))

        else:

            self.left_operand.pretty_print()
            sys.stdout.write(" " + str(self.operator) + " ")
            self.right_operand.pretty_print()

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

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

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(str(self.operator) + str(self.operand))

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class IR3Tree:

    head: Any

    def __init__(self, head: Any) -> None:

        self.head = head

    def pretty_print(self) -> None:

        if self.head:
            self.head.pretty_print()