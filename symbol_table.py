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

    def __init__(self):
        self.st = deque()

    def insert(self, value: str, type: Any, temp_id: str, scope: str=None) -> None:

        if len(self.st) == 0:
            new_st = {}
            new_st[value] = [type, None, scope, temp_id]
            self.st.append(new_st)

        else:
            current_st = self.st[-1]
            current_st[value] = [type, None, scope, temp_id]

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
