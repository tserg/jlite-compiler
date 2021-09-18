import sys

from collections import deque

from typing import (
    List,
    Optional,
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

class AbstractSyntaxTree:
    pass
