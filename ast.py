import sys

from collections import deque

from typing import (
    List,
    Optional,
    Any,
)

class ASTNode:
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
    type: str
    child: Any
    sibling: Any

    def __init__(
        self,
        value: str='',
        type: str='',
        child: Optional[Any]=None,
        sibling: Optional[Any]=None
    ) -> None:
        self.value = value
        self.type = type
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
        """
        Helper function to print the node in syntax format recursively.

        :param str delimiter: String to be printed before the next child
        :param str preceding: Whitespace offset to be printed before the current value
        """
        if self.value:

            if self.type == "Int" and self.value[0] == '-':
                sys.stdout.write('(' + self.value + ')')
            else:
                sys.stdout.write(self.value)

        if self.child:
            sys.stdout.write(' ')
            self.child.pretty_print()


        sys.stdout.write(delimiter)
        if self.sibling:

            sys.stdout.write(preceding)
            self.sibling.pretty_print(delimiter, preceding)

class MainClassNode(ASTNode):

    class_name: str
    arguments: Any
    variable_declarations: Any
    statements: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value = 'class'
        self.type = 'mainClass'

    def set_class_name(self, node: Any) -> None:
        self.class_name = node

    def set_arguments(self, node: Any) -> None:
        self.arguments = node

    def set_variable_declarations(self, node: Any) -> None:
        self.variable_declarations = node

    def set_statements(self, node: Any) -> None:
        self.statements = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write("class " + self.class_name.value + "{ \n  Void main")

        sys.stdout.write('(')
        if self.arguments:
            self.arguments.pretty_print()

        sys.stdout.write(')')

        sys.stdout.write(preceding + '{\n')
        if self.variable_declarations:
            self.variable_declarations.pretty_print(delimiter=';\n', preceding='    ')

        sys.stdout.write('\n')
        self.statements.pretty_print(preceding='    ')

        if self.child:
            self.child.pretty_print(preceding='  ')

        sys.stdout.write('\n' + '  ' +'}')


        if self.child:
            self.child.pretty_print()

        sys.stdout.write("\n}\n")

        if self.sibling:
            self.sibling.pretty_print()

class ClassDeclNode(ASTNode):

    class_name: str
    variable_declarations: Any
    method_declarations: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_class_name(self, class_name: str) -> None:
        self.class_name = class_name

    def set_variable_declarations(self, node: Any) -> None:
        self.variable_declarations = node

    def set_method_declarations(self, node: Any) -> None:
        self.method_declarations = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:
        sys.stdout.write("class " + self.class_name + "{ \n")
        self.variable_declarations.pretty_print(delimiter=';\n', preceding='  ')
        self.method_declarations.pretty_print(delimiter=';\n', preceding='  ')


        if self.child:
            self.child.pretty_print(delimiter, preceding='  ')

        sys.stdout.write("\n}\n")

        if self.sibling:
            self.sibling.pretty_print()

class MdDeclNode(ASTNode):

    method_name: str
    return_type: str
    arguments: Any
    variable_declarations: Any
    statements: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_method_name(self, method_name: str) -> None:
        self.method_name = method_name

    def set_return_type(self, return_type: str) -> None:
        self.return_type = return_type

    def set_arguments(self, node: Any) -> None:
        self.arguments = node

    def set_variable_declarations(self, node: Any) -> None:
        self.variable_declarations = node

    def set_statements(self, node: Any) -> None:
        self.statements = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + self.return_type + ' ' + self.method_name)

        sys.stdout.write('(')
        if self.arguments:
            self.arguments.pretty_print(delimiter=',')
        sys.stdout.write(')')

        sys.stdout.write(preceding + '{\n')
        if self.variable_declarations:
            self.variable_declarations.pretty_print(delimiter=';\n', preceding=preceding + '  ')

        sys.stdout.write('\n')
        self.statements.pretty_print(preceding=preceding + '  ')

        if self.child:
            self.child.pretty_print(delimiter, preceding + '  ')

        sys.stdout.write('\n' + preceding+'}')


        if self.child:
            self.child.pretty_print(delimiter, preceding=preceding)

        sys.stdout.write('\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ArithmeticOpNode(ASTNode):

    left_operand: Any
    right_operand: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_left_operand(self, node: Any) -> None:
        self.left_operand = node

    def set_right_operand(self, node: Any) -> None:
        self.right_operand = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + '(')
        self.left_operand.pretty_print()
        sys.stdout.write(self.value)
        self.right_operand.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class BinOpNode(ASTNode):

    left_operand: Any
    right_operand: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_left_operand(self, node: Any) -> None:
        self.left_operand = node

    def set_right_operand(self, node: Any) -> None:
        self.right_operand = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + '(' + '(')
        self.left_operand.pretty_print()
        sys.stdout.write(')')

        sys.stdout.write(self.value)

        sys.stdout.write(preceding + '(')
        self.right_operand.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write(')')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class AssignmentNode(ASTNode):

    identifier: Any
    assigned_value: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any) -> None:
        self.identifier = node

    def set_assigned_value(self, node: Any) -> None:
        self.assigned_value = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding)
        self.identifier.pretty_print()
        sys.stdout.write('=')
        self.assigned_value.pretty_print()
        sys.stdout.write(';\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class InstanceNode(ASTNode):

    atom: Any
    identifier: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_atom(self, node: Any) -> None:
        self.atom = node

    def set_identifier(self, node: Any) -> None:
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        self.atom.pretty_print()
        sys.stdout.write('.')
        self.identifier.pretty_print()

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ClassInstanceNode(ASTNode):

    class_name: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_class_name(self, node: Any) -> None:
        self.class_name = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('new ')
        self.class_name.pretty_print()
        sys.stdout.write('()')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ReturnNode(ASTNode):

    return_value: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.return_value = None

    def set_return_value(self, node: Any) -> None:
        self.return_value = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + self.value)
        if self.return_value:
            sys.stdout.write(' ')
            self.return_value.pretty_print()
        sys.stdout.write(';\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class IfElseNode(ASTNode):

    condition: Any
    if_expression: Any
    else_expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_condition(self, node: Any) -> None:
        self.condition = node

    def set_if_expression(self, node: Any) -> None:
        self.if_expression = node

    def set_else_expression(self, node: Any) -> None:
        self.else_expression = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + 'if (')
        self.condition.pretty_print()
        sys.stdout.write(') {\n')

        self.if_expression.pretty_print(preceding=preceding+'  ')
        sys.stdout.write(preceding + '}' + ' else {\n')
        self.else_expression.pretty_print(preceding=preceding+'  ')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write(preceding + '}' + '\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class WhileNode(ASTNode):

    condition: Any
    while_expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_condition(self, node: Any) -> None:
        self.condition = node

    def set_while_expression(self, node: Any) -> None:
        self.while_expression = node

    def pretty_print(self, delimiter:str='', preceding:str ='') -> None:
        sys.stdout.write(preceding + 'while (')
        self.condition.pretty_print()
        sys.stdout.write(') {\n')
        self.while_expression.pretty_print(delimiter, preceding+'  ')


        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write('\n' + preceding + '}' + '\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ReadLnNode(ASTNode):

    identifier: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any) -> None:
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + 'readln(')
        self.identifier.pretty_print()
        sys.stdout.write(');\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class PrintLnNode(ASTNode):

    expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_expression(self, node: Any) -> None:
        self.expression = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        if self.expression:
            sys.stdout.write(preceding + 'println(')
            self.expression.pretty_print()
            sys.stdout.write(');\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ArgumentNode(ASTNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(self.type + ' ' + self.value)

        if self.sibling:
            sys.stdout.write(', ')
            self.sibling.pretty_print()

class VarDeclNode(ASTNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + self.type + ' ' + self.value + delimiter)

        if self.sibling:
            #sys.stdout.write('\n')
            self.sibling.pretty_print(delimiter, preceding)

class ExpListNode(ASTNode):

    expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.expression = None

    def set_expression(self, node: Any) -> None:
        self.expression = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('(')

        if self.expression:
            self.expression.pretty_print(',', preceding)

        sys.stdout.write(')')

class NegationNode(ASTNode):

    negated_expression: Any

    def __init__(self, negated_expression: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.negated_expression = negated_expression

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('(!)(')

        self.negated_expression.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print()

        if self.sibling:
            self.sibling.pretty_print()

class AbstractSyntaxTree:

    head: Any

    def __init__(self, head: Any) -> None:

        self.head = head

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        if self.head:
            self.head.pretty_print()
