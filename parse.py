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

from lex import (
    Lexer,
    Token,
)

from ast import (
    Node,
    ParseTree,
)

class ParseError(Exception):
    """
    Exception class for errors encountered while parsing.

    ...

    Attributes
    ----------
    expression: str
    message: str

    """

    expression: str
    message: str

    def __init__(self, expression: str, token: str, index:int, line: int) -> None:
        self.expression = expression
        self.message = "Invalid expression at: "
        self.token = token
        self.line = str(line)
        self.index = str(index)

    def __str__(self) -> str:

        return f'{self.message} {self.expression}. Unable to parse token {self.token} at index {self.index} of line {self.line}.'

class InvalidExpressionError(Exception):
    """
    Exception class for errors encountered while consuming a token during parsing.

    ...

    Attributes
    ----------
    message: str

    """

    message: str

    def __init__(self) -> None:
        self.message = "Unable to derive expression."

    def __str__(self) -> str:
        return self.message

class Parser:
    """
    Parser instance to read token from Lexer and produce abstract syntax tree

    ...

    Attributes
    ----------
    lex : Lexer

    Methods
    -------
    _lex_content(f)
        Run the lexer through the given file
    _eat(expected_token, lexer)
        Checks if the next token in the lexer matches the expected_token. If yes,
        consume the next token. Otherwise, throw an exception.
    _concatenate_parsed(token_list)
        Concatenate tokens in a given list into a string.
    _kleene_closure_loop(expression, lexer)
        Perform Kleene closure on a given expression.
    _positive_closure_loop(expression, lexer)
        Perform positive closure on a given expression.

    """

    lex: Lexer
    parse_tree: ParseTree
    symbol_table: dict
    debug: bool

    def __init__(self, debug: bool=False) -> None:
        self.lex = Lexer()
        self.symbol_table = {}
        self.debug = debug

    def _lex_content(self, f) -> None:
        self.lex.lex_content(f)

    def _eat(self, expected_token: str, lexer: Lexer, level: int) -> Any:
        """
        Checks if the token matches the supposed token.
        If yes, call advance(). Otherwise, return error.

        :param str suppposed_token: string of token to check for
        :param Lexer: the lexer at the current state
        :return: string of token that is found
        :raises InvalidExpressionError: next token does not match the expected token
        """
        if lexer.is_empty():
            return None

        check_next_token = lexer.peek()

        if self.debug:
            print("Checking next token to eat: " + check_next_token.value + "\n")

        if check_next_token == 'EOF':
            lexer.get_next_token_from_queue()
            return None

        if check_next_token.token_name == expected_token:
            if self.debug:
                print("Token eaten" + "\n")

            found_token = lexer.get_next_token_from_queue().value

            # Create node for found token
            new_node = Node(found_token, level)

            return new_node

        raise InvalidExpressionError

    def _kleene_closure_loop(
        self,
        expression: Callable,
        lexer: Lexer,
        level: int
    ) -> Any:
        """
        Helper function to execute Kleene's closure on a given expression

        :param Callable expression: the expression with Kleene's closure
        :param Lexer lexer: the lexer at the current state
        :return: tuple of the expression(s) found and the lexer in the state
            after the Kleene closure
        """

        try:

            if self.debug:
                sys.stdout.write((
                    "Kleene closure loop triggered for expression: ")
                    + expression.__name__
                    + "\n"
                )

            root_node, lexer = expression(lexer, level)

            if root_node:

                repeat_ended = False

                while not repeat_ended:
                    current_lexer = copy.deepcopy(lexer)

                    if self.debug:
                        sys.stdout.write(
                            ("Kleene closure repeat loop entered for expression: ")
                            + expression.__name__
                            + "\n"
                        )

                    try:
                        temp_node, current_lexer = expression(current_lexer, level)
                        root_node.add_child(temp_node)
                        lexer = current_lexer

                    except:
                        repeat_ended = True

                        if self.debug:
                            sys.stdout.write(
                                ("Kleene closure repeat loop terminated for expression: ")
                                + expression.__name__
                                + "\n"
                            )
        except:
            root_node = None

        return (root_node, lexer)

    def _positive_closure_loop(
        self,
        expression: Callable,
        lexer: Lexer,
        level: int
    ) -> Any:

        root_node, lexer = expression(lexer, level)

        repeat_ended = False

        while not repeat_ended:
            current_lexer = copy.deepcopy(lexer)
            if self.debug:
                sys.stdout.write(
                    ("Positive closure loop triggered for expression: ")
                    + expression.__name__
                    + "\n"
                )
            try:
                temp_node, current_lexer = expression(current_lexer, level)
                root_node.add_child(temp_node)
                lexer = current_lexer

            except:
                repeat_ended = True

                if self.debug:
                    sys.stdout.write(
                        ("Positive closure loop terminated for expression: ")
                        + expression.__name__
                        + "\n"
                    )

        return (root_node, lexer)

    def _program_expression(self, lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._program_expression.__name__
                    + "\n"
                )

            t1, lexer = self._mainclass_expression(lexer, 0)
            t2, lexer = self._kleene_closure_loop(
                self._classdeclaration_expression,
                lexer,
                0
            )

            root_node = Node(
                self._program_expression.__name__,
                0,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return root_node

        except ParseError as e:
            raise e

    def _mainclass_expression(self, lexer: Lexer, level: int):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._mainclass_expression.__name__
                    + "\n"
                )

            t1 = self._eat("class", lexer, level)
            t2 = self._eat("CLASS_NAME", lexer, level)
            t3 = self._eat("{", lexer, level)
            t4 = self._eat("Void", lexer, level+1)
            t5 = self._eat("main", lexer, level+1)
            t6 = self._eat("(", lexer, level+1)

            t7, lexer = self._fmllist_expression(lexer, level+1)
            t8 = self._eat(")", lexer, level+1)
            t9, lexer = self._mdbody_expression(lexer, level+1)
            t10 = self._eat("}", lexer, level)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            root_node = Node(
                self._mainclass_expression.__name__,
                level,
                [node for node in [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._mainclass_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _classdeclaration_expression(self, lexer: Lexer, level: int):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._classdeclaration_expression.__name__
                    + "\n"
                )

            t1 = self._eat("class", lexer, level)
            t2 = self._eat("CLASS_NAME", lexer, level)
            t3 = self._eat("{", lexer, level)
            t4, lexer = self._kleene_closure_loop(self._vardecl_expression, lexer, level+1)
            t5, lexer = self._kleene_closure_loop(self._mddecl_expression, lexer, level+1)
            t6 = self._eat("}", lexer, level)

            root_node = Node(
                self._mddecl_expression.__name__,
                level,
                [node for node in [t1, t2, t3, t4, t5, t6] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._classdeclaration_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _vardecl_expression(self, lexer: Lexer, level: int):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._vardecl_expression.__name__
                    + "\n"
                )

            t1, lexer = self._type_expression(lexer, level)
            t2 = self._eat("IDENTIFIER", lexer, level)
            t3 = self._eat(";", lexer, level)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            root_node = Node(
                self._vardecl_expression.__name__,
                level,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._vardecl_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _mddecl_expression(self, lexer: Lexer, level: int):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._mddecl_expression.__name__
                    + "\n"
                )

            t1, lexer = self._type_expression(lexer, level)
            t2 = self._eat("IDENTIFIER", lexer, level)
            t3 = self._eat("(", lexer, level)

            t4, lexer = self._fmllist_expression(lexer, level)
            t5 = self._eat(")", lexer, level)

            t6, lexer = self._mdbody_expression(lexer, level)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            root_node = Node(
                self._mddecl_expression.__name__,
                level,
                [node for node in [t1, t2, t3, t4, t5, t6] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._mddecl_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _fmllist_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._fmllist_expression.__name__
                    + "\n"
                )
            current_lexer = copy.deepcopy(lexer)
            t1, current_lexer = self._type_expression(current_lexer, level)
            t2 = self._eat("IDENTIFIER", current_lexer, level)

            t3, current_lexer = self._kleene_closure_loop(self._fmlrest_expression, current_lexer, level)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            root_node = Node(
                self._fmllist_expression.__name__,
                level,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:
            return (None, lexer)


    def _fmlrest_expression(self, lexer: Lexer, level: int):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._fmlrest_expression.__name__
                    + "\n"
                )

            t1 = self._eat(",", lexer, level)
            t2, lexer = self._type_expression(lexer, level)
            t3 = self._eat("IDENTIFIER", lexer, level)

            if t3.value not in self.symbol_table.keys():
                self.symbol_table[t3.value] = "IDENTIFIER"

            root_node = Node(
                self._fmlrest_expression.__name__,
                level,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._fmlrest_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _type_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._type_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "Int":
                t1 = self._eat("Int", lexer, level)

            elif next_token.token_name == "Bool":
                t1 = self._eat("Bool", lexer, level)

            elif next_token.token_name == "String":
                t1 = self._eat("String", lexer, level)

            elif next_token.token_name == "Void":
                t1 = self._eat("Void", lexer, level)

            elif next_token.token_name == "CLASS_NAME":
                t1 = self._eat("CLASS_NAME", lexer, level)

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "CLASS_NAME"

            else:
                raise ParseError(self._type_expression.__name__)

            root_node = Node(
                self._type_expression.__name__,
                level,
                [node for node in [t1] if isinstance(node, Node)],
                True
            )

            return (root_node, lexer)

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._type_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _mdbody_expression(self, lexer: Lexer, level: int):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._mdbody_expression.__name__
                    + "\n"
                )

            t1 = self._eat("{", lexer, level)
            t2, lexer = self._kleene_closure_loop(
                self._vardecl_expression,
                lexer,
                level+1
            )

            t3, lexer = self._positive_closure_loop(
                self._stmt_expression,
                lexer,
                level+1
            )

            t4 = self._eat("}", lexer, level)

            root_node = Node(
                self._mdbody_expression.__name__,
                level,
                [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._fmlrest_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _stmt_expression(self, lexer: Lexer, level: int):
        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmt_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "if":

                t1 = self._eat("if", lexer, level)


                t2 = self._eat("(", lexer, level)
                t3, lexer = self._exp_expression(lexer, level)
                t4 = self._eat(")", lexer, level)
                t5 = self._eat("{", lexer, level)

                t6, lexer = self._positive_closure_loop(
                    self._stmt_expression,
                    lexer,
                    level+1
                )

                t7 = self._eat("}", lexer, level)
                t8 = self._eat("else", lexer, level)
                t9 = self._eat("{", lexer, level)

                t10, lexer = self._positive_closure_loop(
                    self._stmt_expression,
                    lexer,
                    level+1
                )

                t11 = self._eat("}", lexer, level)

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "while":

                t1 = self._eat("while", lexer, level)
                t2 = self._eat("(", lexer, level)
                t3, lexer = self._exp_expression(lexer, level)
                t4 = self._eat(")", lexer, level)
                t5 = self._eat("{", lexer, level)

                t6, lexer = self._kleene_closure_loop(
                    self._stmt_expression,
                    lexer,
                    level+1
                )

                t7 = self._eat("}", lexer, level)

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4, t5, t6, t7] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "readln":

                t1 = self._eat("readln", lexer, level)
                t2 = self._eat("(", lexer, level)
                t3 = self._eat("IDENTIFIER", lexer, level)
                t4 = self._eat(")", lexer, level)
                t5 = self._eat(";", lexer, level)

                if t3.value not in self.symbol_table.keys():
                    self.symbol_table[t3.value] = "IDENTIFIER"

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "println":

                t1 = self._eat("println", lexer, level)
                t2 = self._eat("(", lexer, level)
                t3, lexer = self._exp_expression(lexer, level)
                t4 = self._eat(")", lexer, level)
                t5 = self._eat(";", lexer, level)

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "IDENTIFIER":

                t1 = self._eat("IDENTIFIER", lexer, level)
                t2 = self._eat("=", lexer, level)
                t3, lexer = self._exp_expression(lexer, level)
                t4 = self._eat(";", lexer, level)

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "IDENTIFIER"

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "return":
                t1 = self._eat("return", lexer, level)
                t2, lexer = self._stmtbeta_expression(lexer, level)

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

            else:

                t1, lexer = self._atom_expression(lexer, level)
                t2, lexer = self._stmtalpha_expression(lexer, level)

                root_node = Node(
                    self._stmt_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )


            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._type_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _stmtbeta_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmtbeta_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == ";":
                t1 = self._eat(";", lexer, level)
                root_node = Node(
                    self._stmtbeta_expression.__name__,
                    level,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                return root_node, lexer

            else:
                t1, lexer = self._exp_expression(lexer, level)
                t2 = self._eat(";", lexer, level)

                root_node = Node(
                    self._stmtbeta_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._stmtalpha_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _stmtalpha_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmtalpha_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == ".":
                t1 = self._eat(".", lexer, level)
                t2 = self._eat("IDENTIFIER", lexer, level)
                t3 = self._eat("=", lexer, level)
                t4, lexer = self._exp_expression(lexer, level)
                t5 = self._eat(";", lexer, level)

                root_node = Node(
                    self._stmtalpha_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            else:

                t1 = self._eat("(", lexer, level)
                t2, lexer = self._explist_expression(lexer, level)
                t3 = self._eat(")", lexer, level)
                t4 = self._eat(";", lexer, level)

                root_node = Node(
                    self._stmtalpha_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._stmtalpha_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _exp_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._exp_expression.__name__
                    + "\n"
                )

            try:
                current_lexer = copy.deepcopy(lexer)

                t1, current_lexer = self._bexp_expression(current_lexer, level)

                if self.debug:
                    sys.stdout.write("BExp expression found, returning to Exp expression" + "\n")

                root_node = Node(
                    self._exp_expression.__name__,
                    level,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )

                return (root_node, current_lexer)

            except:

                if self.debug:
                    sys.stdout.write("BExp expression exception encountered, returned to Exp expression" + "\n")

                try:
                    current_lexer = copy.deepcopy(lexer)
                    t1, current_lexer = self._aexp_expression(current_lexer, level)

                    if self.debug:
                        sys.stdout.write("AExp expression found, returning to Exp expression" + "\n")

                    root_node = Node(
                        self._exp_expression.__name__,
                        level,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )
                    return (root_node, current_lexer)
                except:

                    if self.debug:
                        sys.stdout.write("AExp expression exception encountered, returned to Exp expression" + "\n")

                    try:
                        current_lexer = copy.deepcopy(lexer)
                        if self.debug:
                            sys.stdout.write("Exp expression going to SExp expression" + "\n")
                            sys.stdout.write("Next token: " + lexer.peek().value + "\n")

                        t1, current_lexer = self._sexp_expression(current_lexer, level)

                        if self.debug:
                            sys.stdout.write("SExp expression found, returned to Exp expression" + "\n")

                        root_node = Node(
                            self._exp_expression.__name__,
                            level,
                            [node for node in [t1] if isinstance(node, Node)],
                            True
                        )
                        return (root_node, current_lexer)
                    except ParseError as e:

                        raise ParseError(self._exp_expression.__name__)

        except ParseError as e:
            if self.debug:
                sys.stdout.write("Atom expression exception encountered, backtracking" + "\n")
            raise e

        except:
            if self.debug:
                sys.stdout.write("Atom expression exception encountered, backtracking" + "\n")

            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._exp_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _bexp_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bexp_expression.__name__
                    + "\n"
                )

            t1, lexer = self._conj_expression(lexer, level)
            t2, lexer, loop_count = self._bexpalpha_expression(lexer, level)

            left_p = []

            if t2:
                left_p = [Node("(", level) for i in range(loop_count)]

            root_node = Node(
                self._bexp_expression.__name__,
                level,
                [node for node in left_p + [t1, t2] if isinstance(node, Node)],
                True
            )
            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

    def _bexpalpha_expression(self, lexer: Lexer, level: int, loop_count=0):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bexpalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)

            t1 = self._eat("||", current_lexer, level)
            t2, current_lexer = self._conj_expression(current_lexer, level)
            t3, current_lexer, loop_count = self._bexpalpha_expression(current_lexer, level, loop_count+1)

            right_p = Node(")", level)

            root_node = Node(
                self._bexpalpha_expression.__name__,
                level,
                [node for node in [t1, t2, right_p, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer,
                loop_count
            )

        except:
            return (None, lexer, loop_count)

    def _conj_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._conj_expression.__name__
                    + "\n"
                )
            t1, lexer = self._rexp_expression(lexer, level)
            t2, lexer, loop_count = self._conjalpha_expression(lexer, level)

            left_p = []

            if t2:
                left_p = [Node("(", level) for i in range(loop_count)]

            root_node = Node(
                self._conj_expression.__name__,
                level,
                [node for node in left_p + [t1, t2] if isinstance(node, Node)],
                True
            )
            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

    def _conjalpha_expression(self, lexer: Lexer, level: int, loop_count=0):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._conjalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)
            t1 = self._eat("&&", current_lexer, level)
            t2, current_lexer = self._rexp_expression(current_lexer, level)
            t3, current_lexer, loop_count = self._conjalpha_expression(current_lexer, level, loop_count+1)

            right_p = Node(")", level)

            root_node = Node(
                self._conjalpha_expression.__name__,
                level,
                [node for node in [t1, t2, right_p, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer,
                loop_count
            )

        except:
            return (None, lexer, loop_count)

    def _rexp_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._rexp_expression.__name__
                    + "\n"
                )

            try:
                current_lexer = copy.deepcopy(lexer)
                t1, current_lexer = self._aexp_expression(current_lexer, level)

                if self.debug:
                    sys.stdout.write(
                        ("aexp expression resolved, "
                        "returning to rexp expression first time")
                        + "\n"
                    )


                t2, current_lexer = self._bop_expression(current_lexer, level)

                if self.debug:
                    sys.stdout.write(
                        ("bop expression resolved, "
                        "returning to rexp expression")
                        + "\n"
                    )

                t3, current_lexer = self._aexp_expression(current_lexer, level)

                if self.debug:
                    sys.stdout.write(
                        ("aexp expression resolved, "
                        "returning to rexp expression second time")
                        + "\n"
                    )

                root_node = Node(
                    self._rexp_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    current_lexer
                )

            except:
                if self.debug:
                    sys.stdout.write(
                        "rexp expression (aexp bop aexp) encounted exception"
                        + "\n"
                    )

                try:
                    current_lexer = copy.deepcopy(lexer)
                    t1, current_lexer = self._bgrd_expression(current_lexer, level)

                    root_node = Node(
                        self._rexp_expression.__name__,
                        level,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )

                    return (root_node, current_lexer)

                except ParseError as e:
                    raise e

            #raise ParseError(self._rexp_expression.__name__)

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._rexp_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _bop_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bop_expression.__name__
                    + "\n"
                )
            next_token = lexer.peek()

            if next_token.token_name == "<":
                t1 = self._eat("<", lexer, level)

            elif next_token.token_name == ">":
                t1 = self._eat(">", lexer, level)

            elif next_token.token_name == "<=":
                t1 = self._eat("<=", lexer, level)

            elif next_token.token_name == ">":
                t1 = self._eat(">=", lexer, level)

            elif next_token.token_name == "==":
                t1 = self._eat("==", lexer, level)

            elif next_token.token_name == "!=":
                t1 = self._eat("!=", lexer, level)

            else:
                raise ParseError(self._bop_expression.__name__)

            root_node = Node(
                self._bop_expression.__name__,
                level,
                [node for node in [t1] if isinstance(node, Node)],
                True
            )

            return (root_node, lexer)

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._bop_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _bgrd_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bgrd_expression.__name__
                    + "\n"
                )
            next_token = lexer.peek()

            if next_token.token_name == "!":
                t1 = self._eat("!", lexer, level)
                t2, lexer = self._bgrd_expression(lexer, level)

                not_left_p = Node('(', level)
                not_right_p = Node(')', level)

                bgrd_left_p = Node('(', level)
                bgrd_right_p = Node(')', level)

                root_node = Node(
                    self._bgrd_expression.__name__,
                    level,
                    [node for node in [not_left_p, t1, not_right_p, bgrd_left_p, t2, bgrd_right_p] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "true":
                t1 = self._eat("true", lexer, level)
                root_node = Node(
                    self._bgrd_expression.__name__,
                    level,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                return root_node, lexer

            elif next_token.token_name == "false":
                t1 = self._eat("false", lexer, level)
                root_node = Node(
                    self._bgrd_expression.__name__,
                    level,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                return root_node, lexer

            else:
                try:

                    if lexer.peek(1).token_name in "+-*/":
                        if self.debug:
                            sys.stdout.write("bgrd expression should not handle" + "\n")
                        # Defer to _aexp or _sexp if any of these operators
                        # are after the atom
                        raise InvalidExpressionError

                    t1, lexer = self._atom_expression(lexer, level)
                    root_node = Node(
                        self._bgrd_expression.__name__,
                        level,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )
                    return root_node, lexer

                except:
                    last_consumed_token = lexer.get_last_consumed_token()
                    raise ParseError(
                        self._bgrd_expression.__name__,
                        last_consumed_token.value,
                        last_consumed_token.start_index,
                        last_consumed_token.start_line
                    )

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._bgrd_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _aexp_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._aexp_expression.__name__
                    + "\n"
                )

            t1, lexer = self._term_expression(lexer, level)

            if self.debug:
                sys.stdout.write("Term expression found, returned to AExp expression" + "\n")

            t2, lexer, loop_count = self._aexpalpha_expression(lexer, level)

            # Custom logic to check if next token is a STRING_LITERAL
            # If STRING_LITERAL, throw exception to let SExp handle string concatenation
            next_token_1 = lexer.peek()
            next_token_2 = lexer.peek(1)

            if next_token_1.value in ['-', '+'] and next_token_2.token_name == 'STRING_LITERAL':
                raise ParseError(self._aexp_expression.__name__)


            if self.debug:
                sys.stdout.write("AExpalpha expression found, returned to AExp expression" + "\n")
                sys.stdout.write("Next two tokens: " + lexer.peek().value + " " + lexer.peek(1).value + "\n")

            left_p = []

            if t2:
                left_p = [Node("(", level) for i in range(loop_count)]


            root_node = Node(
                self._aexp_expression.__name__,
                level,
                [node for node in left_p + [t1, t2] if isinstance(node, Node)],
                True
            )
            return (
                root_node,
                lexer
            )

        except:
            if self.debug:
                sys.stdout.write("AExp expression exception encountered, backtracking" + "\n")

            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._aexp_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _aexpalpha_expression(self, lexer: Lexer, level: int, loop_count: int=0):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._aexpalpha_expression.__name__
                    + "\n"
                )

                sys.stdout.write("aexp alpha expression entered" + "\n")
                sys.stdout.write("Current loop count: " + str(loop_count) + "\n")

            current_lexer = copy.deepcopy(lexer)

            next_token = current_lexer.peek()

            if next_token.token_name == "+":
                t1 = self._eat("+", current_lexer, level)

            elif next_token.token_name == "-":
                t1 = self._eat("-", current_lexer, level)

            else:
                return (None, current_lexer, loop_count)

            t2, current_lexer = self._term_expression(current_lexer, level)

            if self.debug:
                sys.stdout.write("Term expression found, returned to AExpalpha expression" + "\n")

            t3, current_lexer, loop_count = self._aexpalpha_expression(current_lexer, level, loop_count+1)

            right_p = Node(")", level)

            root_node = Node(
                self._aexpalpha_expression.__name__,
                level,
                [node for node in [t1, t2, right_p, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer,
                loop_count
            )

        except:
            return (None, lexer, loop_count)

    def _term_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._term_expression.__name__
                    + "\n"
                )

            t1, lexer = self._ftr_expression(lexer, level)

            if self.debug:
                sys.stdout.write("Ftr expression found, returning to Term expression" + "\n")

            t2, lexer, loop_count = self._termalpha_expression(lexer, level)

            left_p = []

            if t2:
                left_p = [Node("(", level) for i in range(loop_count)]

            root_node = Node(
                self._term_expression.__name__,
                level,
                [node for node in left_p + [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            if self.debug:
                sys.stdout.write("Term expression exception encountered, backtracking" + "\n")

            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._term_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _termalpha_expression(self, lexer: Lexer, level: int, loop_count: int=0):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._termalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)
            next_token = current_lexer.peek()

            if next_token.token_name == "*":
                t1 = self._eat("*", current_lexer, level)

            elif next_token.token_name == "/":
                t1 = self._eat("/", current_lexer, level)

            else:
                return (None, current_lexer, loop_count)

            t2, current_lexer = self._ftr_expression(current_lexer, level)
            t3, current_lexer, loop_count = self._termalpha_expression(current_lexer, level, loop_count+1)

            right_p = Node(")", level)

            root_node = Node(
                self._termalpha_expression.__name__,
                level,
                [node for node in [t1, t2, right_p, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer,
                loop_count
            )

        except:
            return (None, lexer, loop_count)

    def _ftr_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._ftr_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "INTEGER_LITERAL":

                t1 = self._eat("INTEGER_LITERAL", lexer, level)
                left_p = None
                right_p = None

                if next_token.value[0] == '-':
                    left_p = Node('(', level)
                    right_p = Node(')', level)

                root_node = Node(
                    self._ftr_expression.__name__,
                    level,
                    [node for node in [left_p, t1, right_p] if isinstance(node, Node)],
                    True
                )

                return (root_node, lexer)

            elif next_token.token_name == "-":
                t1 = self._eat("-", lexer, level)
                t2, lexer = self._ftr_expression(lexer, level)

                root_node = Node(
                    self._ftr_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            else:

                try:
                    if self.debug:
                        sys.stdout.write(
                            "ftr expression going to atom expression"
                            + "\n"
                        )

                    t1, lexer = self._atom_expression(lexer, level)
                    root_node = Node(
                        self._ftr_expression.__name__,
                        level,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )

                    if self.debug:
                        sys.stdout.write(
                            "atom expression completed, returning to atom expression"
                            + "\n"
                        )

                    return root_node, lexer

                except:
                    last_consumed_token = lexer.get_last_consumed_token()
                    raise ParseError(
                        self._ftr_expression.__name__,
                        last_consumed_token.value,
                        last_consumed_token.start_index,
                        last_consumed_token.start_line
                    )

        except ParseError as e:
            if self.debug:
                sys.stdout.write("Ftr expression exception encountered, backtracking" + "\n")
            raise e

        except:
            if self.debug:
                sys.stdout.write("Ftr expression exception encountered, backtracking" + "\n")

            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._ftr_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _sexp_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._sexp_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()
            if next_token.token_name == "STRING_LITERAL":
                t1 = self._eat("STRING_LITERAL", lexer, level)

            else:
                if self.debug:
                    sys.stdout.write(
                        "SExp expression going to Atom expression"
                        + "\n"
                    )

                t1, lexer = self._atom_expression(lexer, level)

                if self.debug:
                    sys.stdout.write(
                        "Atom expression found, returned to SExp expression"
                        + "\n"
                    )

            t2, lexer = self._sexpalpha_expression(lexer, level)

            root_node = Node(
                self._sexp_expression.__name__,
                level,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._sexp_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _sexpalpha_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._sexpalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)

            t1 = self._eat("+", current_lexer, level)
            t2, current_lexer = self._sexp_expression(current_lexer, level)
            t3, current_lexer = self._sexpalpha_expression(current_lexer, level)

            root_node = Node(
                self._sexpalpha_expression.__name__,
                level,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:

            return (None, lexer)

    def _atom_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._atom_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "this":
                t1 = self._eat("this", lexer, level)
                t2, lexer = self._atomalpha_expression(lexer, level)

                root_node = Node(
                    self._atom_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "new":
                t1 = self._eat("new", lexer, level)
                t2 = self._eat("CLASS_NAME", lexer, level)
                t3 = self._eat("(", lexer, level)
                t4 = self._eat(")", lexer, level)
                t5, lexer = self._atomalpha_expression(lexer, level)

                if t2.value not in self.symbol_table.keys():
                    self.symbol_table[t2.value] = "CLASS_NAME"

                root_node = Node(
                    self._atom_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "(":
                t1 = self._eat("(", lexer, level)
                t2, lexer = self._exp_expression(lexer, level)
                t3 = self._eat(")", lexer, level)
                t4, lexer = self._atomalpha_expression(lexer, level)

                root_node = Node(
                    self._atom_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "null":
                t1 = self._eat("null", lexer, level)
                t2, lexer = self._atomalpha_expression(lexer, level)

                root_node = Node(
                    self._atom_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "IDENTIFIER":

                t1 = self._eat("IDENTIFIER", lexer, level)
                t2, lexer = self._atomalpha_expression(lexer, level)

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "IDENTIFIER"

                root_node = Node(
                    self._atom_expression.__name__,
                    level,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            else:
                last_consumed_token = lexer.get_last_consumed_token()
                raise ParseError(
                    self._atom_expression.__name__,
                    last_consumed_token.value,
                    last_consumed_token.start_index,
                    last_consumed_token.start_line
                )

        except ParseError as e:
            if self.debug:
                sys.stdout.write("Atom expression exception encountered, backtracking" + "\n")
            raise e

        except:
            if self.debug:
                sys.stdout.write("Atom expression exception encountered, backtracking" + "\n")

            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._atom_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def _atomalpha_expression(self, lexer: Lexer, level: int):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._atomalpha_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == ".":
                current_lexer = copy.deepcopy(lexer)
                t1 = self._eat(".", current_lexer, level)
                t2 = self._eat("IDENTIFIER", current_lexer, level)
                t3, current_lexer = self._atomalpha_expression(current_lexer, level)

                if t2.value not in self.symbol_table.keys():
                    self.symbol_table[t2.value] = "IDENTIFIER"

                root_node = Node(
                    self._atomalpha_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    current_lexer
                )

            elif next_token.token_name == "(":
                current_lexer = copy.deepcopy(lexer)
                t1 = self._eat("(", current_lexer, level)
                t2, current_lexer = self._explist_expression(current_lexer, level)
                t3 = self._eat(")", current_lexer, level)
                t4, current_lexer = self._atomalpha_expression(current_lexer, level)

                root_node = Node(
                    self._atomalpha_expression.__name__,
                    level,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    current_lexer
                )

            else:
                return (None, lexer)

        except:
            return (None, lexer)

    def _explist_expression(self, lexer: Lexer, level: int):

        try:
            t1, lexer = self._exp_expression(lexer, level)
            t2, lexer = self._kleene_closure_loop(self._exprest_expression, lexer, level)

            root_node = Node(
                self._explist_expression.__name__,
                level,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,lexer
            )

        except:
            return (None, lexer)

    def _exprest_expression(self, lexer: Lexer, level: int):

        try:
            t1 = self._eat(",", lexer, level)
            t2, lexer = self._exp_expression(lexer, level)

            root_node = Node(
                self._exprest_expression.__name__,
                level,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

        except:
            last_consumed_token = lexer.get_last_consumed_token()
            raise ParseError(
                self._exprest_expression.__name__,
                last_consumed_token.value,
                last_consumed_token.start_index,
                last_consumed_token.start_line
            )

    def parse(self, f) -> None:

        self.lex.lex_content(f)

        self.parse_tree = ParseTree(self._program_expression(self.lex))

    def pretty_print(self) -> None:

        sys.stdout.write("Parsed output: " + "\n\n")
        self.parse_tree.pretty_print(self.symbol_table)

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        parser = Parser(debug=False)
        parser.parse(f)

        parser.pretty_print()
        #sys.stdout.write(str(parser.parse_tree.total_nodes()))

if __name__ == "__main__":

    __main__()
