import copy
import sys

from collections import deque

from typing import (
    Any,
    Dict,
    List,
    Deque,
    Optional,
)

class SymbolTable:
    """
    IR3 Generator instance to generate IR3 tree from Parser's AST
    ...

    Attributes
    ----------
    symbol_table_stack: Deque[Dict[Any, Any]
    current_scope_depth: int

    Methods
    -------
    add_empty_st()
        Adds an empty dictionary to the symbol table stack
    pop_st()
        Pops the top dictionary from the symbol table stack
    insert(str, Any, str, Any)
        Insert a symbol into the symbol table stack
        Takes in arguments for value, type, temp_id and state
    lookup(str)
        Returns the list of [value, type, temp_id, state] for the symbol if found
    
    """
    # Mappings of value to [type, state, scope, temp_id]
    symbol_table_stack: Deque[Dict[Any, Any]]

    # Track current scope depth
    current_scope_depth: int

    def __init__(self) -> None:
        self.symbol_table_stack = deque()
        self.current_scope_depth = 0

    def add_empty_st(self) -> None:
        """
        Add an empty dictionary to the symbol table stack for current scope
        """
        self.symbol_table_stack.append({})
        self.current_scope_depth += 1

    def pop_st(self) -> None:
        """
        Pops the top dictionary from the symbol table stack to return to previous scope
        """
        self.symbol_table_stack.pop()
        self.current_scope_depth -= 1

    def insert(
        self,
        value: str,
        type: Any,
        temp_id: str=None,
        state: Any=None
    ) -> None:
        """
        Insert a symbol into the symbol table stack

        :param str value: name of the symbol in the AST
        :param Any type: type of the symbol
        :param str temp_id: generated ID for symbol in the IR3Tree
        :param Any state: current state of the symbol

        """

        scope = self.current_scope_depth

        if len(self.symbol_table_stack) == 0:
            new_st = {}
            new_st[value] = [type, state, scope, temp_id]
            self.symbol_table_stack.append(new_st)

        else:
            current_st = self.symbol_table_stack[-1]
            current_st[value] = [type, state, scope, temp_id]

    def lookup(self, value: str) -> Optional[List[Any]]:
        """
        Returns the list of [value, type, temp_id, state] for the symbol if found.
        Otherwise, return None.

        :param str value: name of the symbol in the AST
        :return: the list of [value, type, temp_id, state] or None
        """
        st = copy.deepcopy(self.st)

        while len(st) > 0:

            current_st = st.pop()

            sys.stdout.write("Current lookup symbol table: " + str(current_st) + "\n")

            if value in current_st:
                return current_st[value]

        return None

    def __str__(self) -> str:
        """
        Helper function for debugging

        :return: the symbol table stack in string
        """
        return str(self.st)
