import sys

from collections import deque

from typing import (
    List,
    Optional,
)

PRETTY_PRINT_KEYWORDS = {
    'if',
    'else',
    'while',
    'main',
    'true',
    'false',
    'return',
    'Void',
    'String',
    'Bool',
    'Int',
    'null',
    'new',
    'class',
}

class Node:

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

            if self.value in PRETTY_PRINT_KEYWORDS:
                sys.stdout.write(self.value + " ")
            elif self.value in symbol_table.keys():
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

    head: Node

    def __init__(self, head: Optional[Node] = None) -> None:

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

        sys.stdout.write("Printing parse Tree: " + "\n")
        if self.head:
            self.head.print(symbol_table)
