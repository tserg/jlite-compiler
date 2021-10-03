import os
import sys
import copy

from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple
)

from parse import (
    Parser,
)

from ir3 import *

class IR3Generator:
    """
    IR3 Generator instance to generate IR3 tree from Parser's AST
    ...

    Attributes
    ----------
    lex : Lexer

    Methods
    -------
    _parse_content(f)
        Run the parser through the given file

    """
    parser: Parser
    debug: bool
    ir3_tree: IR3Tree

    def __init__(self, debug: bool=False) -> None:
        self.parser = Parser()
        self.debug = debug

    def _parse_content(self, f) -> None:
        self.parser.parse(f)
        self.parser.type_check()

    def _generate_ir3(self):

        return self._program_expression(self.parser.ast.head)

    def generate_ir3(self, f) -> None:
        self._parse_content(f)
        self.ir3_tree = IR3Tree(self._generate_ir3())

    def _program_expression(self, ast):

        '''
        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._program_expression.__name__
                    + "\n"
                )

            t1, lexer = self._mainclass_expression(lexer)
            t2, lexer = self._kleene_closure_loop(
                self._classdeclaration_expression,
                lexer
            )

            if self.debug:
                if t2:
                    sys.stdout.write("Class decl node created" + t2.value + "\n")

            t1.add_sibling(t2)

            return t1

        except ParseError as e:
            raise e
        '''

        _main_class_node = MainClassIR3Node()
        _main_class_node.set_class_name(ast.class_name)

        return _main_class_node

    def pretty_print(self) -> None:
        """
        Prints the AST of the parsed file
        """
        self.ir3_tree.pretty_print()

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        gen = IR3Generator(debug=True)
        gen.generate_ir3(f)

        gen.pretty_print()

if __name__ == "__main__":

    __main__()
