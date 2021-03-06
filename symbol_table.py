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

from jlite_type import (
    FunctionType,
)

class SymbolTableStack:
    """
    Symbol table stack for managing symbol tables
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
    # Mappings of value to a dictionary for type, state, scope, temp_id
    symbol_table_stack: Deque[Dict[Any, Dict[str, Any]]]

    # Track current scope depth
    current_scope_depth: int

    debug: bool

    def __init__(self, debug: bool=False) -> None:
        self.symbol_table_stack = deque()
        self.current_scope_depth = 0
        self.debug = debug

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
        temp_list: Any
        scope = self.current_scope_depth

        if len(self.symbol_table_stack) == 0:
            new_st = {}
            new_st[value] = {
                'type': type,
                'state': state,
                'scope': scope,
                'temp_id': temp_id
            }
            self.symbol_table_stack.append(new_st)

        else:
            current_st = self.symbol_table_stack[-1]

            if value not in current_st:
                current_st[value] = {
                    'type': type,
                    'state': state,
                    'scope': scope,
                    'temp_id': temp_id
                }
            elif isinstance(type, FunctionType):
                if isinstance(current_st[value], dict):
                    # Initialise list if there is only one possible method call
                    existing = current_st[value]
                    temp_list = [existing]
                    temp_list.append({
                        'type': type,
                        'state': state,
                        'scope': scope,
                        'temp_id': temp_id
                    })

                    current_st[value] = temp_list

                else:
                    # Add to list if there is more than one possible method call
                    # I.e

                    temp_list = current_st[value]
                    temp_list.append({
                        'type': type,
                        'state': state,
                        'scope': scope,
                        'temp_id': temp_id
                    })

                    current_st[value] = temp_list

    def lookup(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Returns the list of [value, type, temp_id, state] for the symbol if found.
        Otherwise, return None.

        :param str value: name of the symbol in the AST
        :return: the list of [value, type, temp_id, state] or None
        """
        st = copy.deepcopy(self.symbol_table_stack)

        while len(st) > 0:

            current_st = st.pop()

            if self.debug:
                sys.stdout.write("Current lookup symbol table: " + \
                    str(current_st) + "\n")

            if value in current_st:
                return current_st[value]

        return None

    def __str__(self) -> str:
        """
        Helper function for debugging

        :return: the symbol table stack in string
        """
        return str(self.symbol_table_stack)
