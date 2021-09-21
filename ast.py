import sys

from collections import deque

from typing import (
    List,
    Optional,
    Any,
)

PRETTY_PRINT_KEYWORDS_WITHOUT_SPACE = {
    'main',
    'true',
    'false',
    'null',
}

PRETTY_PRINT_KEYWORDS_WITH_TRAILING_SPACE = {
    'return',
    'class',
    'new',
    'if',
    'else',
    'while',
    'Void',
    'String',
    'Bool',
    'Int',
}

class Node:
    """
    Node instance for a valid expression

    ...

    Attributes
    ----------
    value: str
    children: List['Node']
    is_expression: bool

    Methods
    -------
    print(symbol_table):
        Prints the current value of the node, and its children.
    add_child(node):
        Adds a node to its children.

    """

    value: str
    children: List['Node']
    is_expression: bool

    def __init__(
        self,
        value: str,
        level: int,
        children: List['Node']=[],
        is_expression: bool=False
    ) -> None:
        self.value = value
        self.level = level
        self.children = children
        self.is_expression = is_expression

    def print(self, symbol_table) -> None:

        if self.value == None:
            sys.stdout.write("")

        if not self.is_expression and self.value:

            if self.value in PRETTY_PRINT_KEYWORDS_WITH_TRAILING_SPACE or \
                (symbol_table.get(self.value) == 'CLASS_NAME'):
                sys.stdout.write(self.value + " ")

            else:
                sys.stdout.write(self.value)

            if self.value in '{};':
                sys.stdout.write("\n")

            if self.value in '{':
                sys.stdout.write("  " * (self.level+1))
            elif self.value in '}':
                sys.stdout.write("  " * (self.level))
            elif self.value in ';':
                sys.stdout.write("  " * (self.level))

        for child in self.children:

            child.print(symbol_table)

    def add_child(self, node: 'Node') -> None:

        self.children.append(node)

class ParseTree:
    """
    Parse tree instance constructed from a parsed file

    ...

    Attributes
    ----------
    head: Node

    Methods
    -------
    pretty_print()
        Prints the parse tree

    """
    head: Node

    def __init__(self, head: Node) -> None:

        self.head = head

    '''
    def total_nodes(self) -> int:

        unexplored_nodes = deque()
        unexplored_nodes.append(self.head)

        count = 0

        while len(unexplored_nodes) > 0:
            current_node = unexplored_nodes.popleft()
            count += 1
            unexplored_nodes += current_node.children

        return count
    '''

    def pretty_print(self, symbol_table) -> None:

        if self.head:
            self.head.print(symbol_table)

class ASTNode:
    """
    Node instance for a valid expression

    ...

    Attributes
    ----------
    value: str
    children: List['Node']
    is_expression: bool

    Methods
    -------
    print(symbol_table):
        Prints the current value of the node, and its children.
    add_child(node):
        Adds a node to its children.

    """

    value: str
    type: str
    child: Any
    sibling: Any

    def __init__(
        self,
        value: str,
        type: str='leaf',
        child: Optional[Any]=None,
        sibling: Optional[Any]=None
    ) -> None:
        self.value = value
        self.type = type
        self.child = child
        self.sibling = sibling


    def add_child(self, node: Any):

        self.child = node

    def add_sibling(self, node: Any):

        self.sibling = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        if self.value:

            if self.type == "INTEGER_LITERAL" and self.value[0] == '-':
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


class ArithmeticOpNode(ASTNode):

    left_operand: Any
    right_operand: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_left_operand(self, node: Any):
        self.left_operand = node

    def set_right_operand(self, node: Any):
        self.right_operand = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_left_operand(self, node: Any):
        self.left_operand = node

    def set_right_operand(self, node: Any):
        self.right_operand = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(preceding + '(')
        self.left_operand.pretty_print()
        sys.stdout.write(')')

        sys.stdout.write(self.value)

        sys.stdout.write(preceding + '(')
        self.right_operand.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class AssignmentNode(ASTNode):

    identifier: Any
    assigned_value: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any):
        self.identifier = node

    def set_assigned_value(self, node: Any):
        self.assigned_value = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_atom(self, node: Any):
        self.atom = node

    def set_identifier(self, node: Any):
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        self.atom.pretty_print()
        sys.stdout.write('.')
        self.identifier.pretty_print()

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ClassInstanceNode(ASTNode):

    class_name: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_class_name(self, node: Any):
        self.class_name = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write('new ')
        self.class_name.pretty_print()
        sys.stdout.write('()')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ReturnNode(ASTNode):

    return_value: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_value = None

    def set_return_value(self, node: Any):
        self.return_value = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(preceding + self.value)
        if self.return_value:
            sys.stdout.write(' ')
            self.return_value.pretty_print()
        sys.stdout.write(';\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class MainClassNode(ASTNode):

    class_name: Any
    fml_list: Any
    mdbody: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_class_name(self, node: Any):
        self.class_name = node

    def set_fml_list(self, node: Any):
        self.fml_list = node

    def set_mdbody(self, node: Any):
        self.mdbody = node

    def pretty_print(self):

        sys.stdout.write("class " + self.class_name.value + "{ \n  Void main")

        sys.stdout.write('(')
        if self.fml_list:
            self.fml_list.pretty_print()

        sys.stdout.write(')')

        if self.mdbody:
            self.mdbody.pretty_print(preceding='  ')


        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write("\n}\n")

        if self.sibling:
            self.sibling.pretty_print()

class MdBodyNode(ASTNode):

    vardecl: Any
    stmt: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_vardecl(self, node: Any):
        self.vardecl = node

    def set_stmt(self, node: Any):
        self.stmt = node

    def pretty_print(self, delimiter:str='', preceding:str=''):

        sys.stdout.write(preceding + '{\n')
        if self.vardecl:
            sys.stdout.write(preceding + '  ')
            self.vardecl.pretty_print(delimiter=';\n', preceding=preceding + '  ')

        sys.stdout.write('\n')
        self.stmt.pretty_print(preceding=preceding + '  ')



        if self.child:
            self.child.pretty_print(delimiter, preceding + '  ')

        sys.stdout.write('\n' + preceding+'}')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding + '  ')

class ClassDeclNode(ASTNode):

    class_name: Any
    var_decl: Any
    mddecl: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_class_name(self, node: Any):
        self.class_name = node

    def set_var_decl(self, node: Any):
        self.var_decl = node

    def set_mddecl(self, node: Any):
        self.mddecl = node

    def pretty_print(self):
        sys.stdout.write("class " + self.class_name.value + "{ \n" + '  ')
        self.var_decl.pretty_print(delimiter=';\n', preceding='  ')
        self.mddecl.pretty_print(delimiter=';\n', preceding='  ')


        if self.child:
            self.child.pretty_print(delimiter, preceding='  ')

        sys.stdout.write("\n}\n")

        if self.sibling:
            self.sibling.pretty_print()

class MdDeclNode(ASTNode):

    identifier: Any
    fml_list: Any
    mdbody: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any):
        self.identifier = node

    def set_fml_list(self, node: Any):
        self.fml_list = node

    def set_mdbody(self, node: Any):
        self.mdbody = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(preceding + self.value + ' ')
        self.identifier.pretty_print()
        sys.stdout.write('(')
        if self.fml_list:
            self.fml_list.pretty_print(delimiter=',')
        sys.stdout.write(')')
        self.mdbody.pretty_print(delimiter=';\n', preceding=preceding)


        if self.child:
            self.child.pretty_print(delimiter, preceding=preceding)

        sys.stdout.write('\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class IfElseNode(ASTNode):

    condition: Any
    if_expression: Any
    else_expression: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_condition(self, node: Any):
        self.condition = node

    def set_if_expression(self, node: Any):
        self.if_expression = node

    def set_else_expression(self, node: Any):
        self.else_expression = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

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

    expression: Any
    statement: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_expression(self, node: Any):
        self.expression = node

    def set_statement(self, node: Any):
        self.statement = node

    def pretty_print(self, delimiter:str='', preceding:str =''):
        sys.stdout.write(preceding + 'while (')
        self.expression.pretty_print()
        sys.stdout.write(') {\n')
        self.statement.pretty_print(delimiter, preceding+'  ')


        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write('\n' + preceding + '}' + '\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ReadLnNode(ASTNode):

    identifier: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any):
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(preceding + 'readln(')
        self.identifier.pretty_print()
        sys.stdout.write(');\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class PrintLnNode(ASTNode):

    expression: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_expression(self, node: Any):
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

class FmlNode(ASTNode):

    identifier: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any):
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write(self.type + ' ')
        self.identifier.pretty_print()

        if self.sibling:
            sys.stdout.write(', ')
            self.sibling.pretty_print()

class ExpListNode(ASTNode):

    expression: Any

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expression = None

    def set_expression(self, node: Any):
        self.expression = node

    def pretty_print(self, delimiter: str='', preceding: str=''):

        sys.stdout.write('(')

        if self.expression:
            self.expression.pretty_print(',', preceding)

        sys.stdout.write(')')

class NegationNode(ASTNode):

    negated_expression: Any

    def __init__(self, negated_expression: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.negated_expression = negated_expression

    def pretty_print(self, delimiter: str='', preceding: str=''):

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

    def pretty_print(self, delimiter: str='', preceding: str=''):

        if self.head:
            self.head.pretty_print()
