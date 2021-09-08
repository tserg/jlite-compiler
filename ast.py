import sys

from collections import deque

class Node:

    def __init__(self, value, children=[], is_expression=False):
        self.value = value
        self.children = children
        self.is_expression = is_expression

    def print(self):

        if self.value == None:
            sys.stdout.write("")

        if not self.is_expression and self.value:
            sys.stdout.write(self.value + " ")

        for child in self.children:

            child.print()

    def add_child(self, node):

        self.children.append(node)

class ParseTree:

    def __init__(self, head=None):

        self.head = head

    def total_nodes(self):

        unexplored_nodes = deque()
        unexplored_nodes.append(self.head)

        count = 0

        while len(unexplored_nodes) > 0:
            current_node = unexplored_nodes.popleft()
            count += 1
            unexplored_nodes += current_node.children

        return count

    def print(self):

        sys.stdout.write("Printing parse Tree: " + "\n")
        if self.head:
            self.head.print()
