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

    # Mappings of value to [type, state, scope, temp_id]
    st: Deque[Dict[Any, Any]]

    # Track current scope depth
    current_scope_depth: int

    def __init__(self):
        self.st = deque()
        self.current_scope_depth = 0

    def add_empty_st(self):
        self.st.append({})
        self.current_scope_depth += 1

    def pop_st(self):
        self.st.pop()
        self.current_scope_depth -= 1

    def insert(self, value: str, type: Any, temp_id: str=None, state: Any=None) -> None:

        scope = self.current_scope_depth

        if len(self.st) == 0:
            new_st = {}
            new_st[value] = [type, state, scope, temp_id]
            self.st.append(new_st)

        else:
            current_st = self.st[-1]
            current_st[value] = [type, state, scope, temp_id]

    def lookup(self, value: str) -> Optional[List[Any]]:

        st = copy.deepcopy(self.st)

        while len(st) > 0:

            current_st = st.pop()

            sys.stdout.write("Current lookup symbol table: " + str(current_st) + "\n")

            if value in current_st:
                return current_st[value]

        return None

    def __str__(self):
        return str(self.st)
