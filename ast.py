import sys

from collections import deque

from typing import (
    List,
    Optional,
)

class Node:

    value: str
    children: List['Node']
    is_expression: bool

    def __init__(
        self,
        value: str,
        children: List['Node']=[],
        is_expression: bool=False
    ) -> None:
        self.value = value

        self.children = children
        self.is_expression = is_expression

    def print(self) -> None:

        if self.value == None:
            sys.stdout.write("")

        if not self.is_expression and self.value:
            sys.stdout.write(self.value + " ")

        for child in self.children:

            child.print()

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

    def pretty_print(self) -> None:

        sys.stdout.write("Printing parse Tree: " + "\n")
        if self.head:
            self.head.print()
