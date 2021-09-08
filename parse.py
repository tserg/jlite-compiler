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

    expression: str
    message: str

    def __init__(self, expression: str='') -> None:
        self.expression = expression
        self.message = "Invalid expression at: "

    def __str__(self) -> str:

        return f'{self.message} {self.expression}'

class InvalidExpressionError(Exception):

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
    _eat(supposed_token, lexer)
        Checks if the next token in the lexer matches the supposed_token. If yes,
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

    def __init__(self) -> None:
        self.lex = Lexer()
        self.parse_tree = ParseTree()

    def _lex_content(self, f) -> None:
        self.lex.lex_content(f)

    def _eat(self, supposed_token, lexer) -> Node:
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
        print("Eat")
        check_next_token = lexer.peek()
        print("Next token: " + check_next_token.value)
        if check_next_token == 'EOF':
            lexer.get_next_token_from_queue()
            return None

        print("Checking for: " + supposed_token)
        print(check_next_token.token_name)
        if check_next_token.token_name == supposed_token:
            print("Current token is valld")
            found_token = lexer.get_next_token_from_queue().value

            # Create node for found token
            new_node = Node(found_token)

            return new_node

        raise InvalidExpressionError

    def _concatenate_parsed(self, token_list) -> str:
        return ''.join([t + " " for t in token_list])

    def _kleene_closure_loop(
        self,
        expression: Callable,
        lexer: Lexer
    ) -> Tuple[Node, Lexer]:
        """
        Helper function to execute Kleene's closure on a given expression

        :param Callable expression: the expression with Kleene's closure
        :param Lexer lexer: the lexer at the current state
        :return: tuple of the expression(s) found and the lexer in the state
            after the Kleene closure
        """

        try:
            print("program expression going to kleene closure loop for expression: " + expression.__name__)
            root_node, lexer = expression(lexer)

            if root_node:

                repeat_ended = False

                while not repeat_ended:
                    current_lexer = copy.deepcopy(lexer)
                    print("kleene closure repeat loop entered for expression: " + expression.__name__)
                    try:
                        temp_node, current_lexer = expression(current_lexer)
                        root_node.add_child(temp_node)
                        lexer = current_lexer

                    except:
                        repeat_ended = True
                        print("terminate kleene closure repeat loop")
        except:
            root_node = None

        return (root_node, lexer)

    def _positive_closure_loop(
        self,
        expression: Callable,
        lexer: Lexer
    ) -> Tuple[Token, Lexer]:

        root_node, lexer = expression(lexer)

        repeat_ended = False

        while not repeat_ended:
            current_lexer = copy.deepcopy(lexer)
            print("positive closure loop entered")
            try:
                temp_node, current_lexer = expression(current_lexer)
                root_node.add_child(temp_node)
                lexer = current_lexer

            except:
                repeat_ended = True
                print("terminate positive closure loop in " + expression.__name__)

        return (root_node, lexer)

    def _program_expression(self, lexer):

        try:
            print("program expression entered")


            t1, lexer = self._mainclass_expression(lexer)
            print("program expression - mainclass found")
            t2, lexer = self._kleene_closure_loop(self._classdeclaration_expression, lexer)

            root_node = Node(
                self._program_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return root_node

        except ParseError as e:
            raise e

        except:
            raise ParseError(self._program_expression.__name__)

    def _mainclass_expression(self, lexer):

        try:

            t1 = self._eat("class", lexer)
            t2 = self._eat("CLASS_NAME", lexer)
            t3 = self._eat("{", lexer)
            t4 = self._eat("Void", lexer)
            t5 = self._eat("main", lexer)
            t6 = self._eat("(", lexer)

            t7, lexer = self._fmllist_expression(lexer)
            t8 = self._eat(")", lexer)
            t9, lexer = self._mdbody_expression(lexer)
            t10 = self._eat("}", lexer)

            root_node = Node(
                self._mainclass_expression.__name__,
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
            raise ParseError(self._mainclass_expression.__name__)

    def _classdeclaration_expression(self, lexer):

        try:
            t1 = self._eat("class", lexer)
            t2 = self._eat("CLASS_NAME", lexer)
            t3 = self._eat("{", lexer)
            t4, lexer = self._kleene_closure_loop(self._vardecl_expression, lexer)
            t5, lexer = self._kleene_closure_loop(self._mddecl_expression, lexer)
            t6 = self._eat("}", lexer)

            root_node = Node(
                self._mddecl_expression.__name__,
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
            raise ParseError(self._classdeclaration_expression.__name__)

    def _vardecl_expression(self, lexer):

        try:
            t1, lexer = self._type_expression(lexer)
            t2 = self._eat("IDENTIFIER", lexer)
            t3 = self._eat(";", lexer)

            root_node = Node(
                self._vardecl_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:

            raise ParseError(self._vardecl_expression.__name__)

    def _mddecl_expression(self, lexer):
        print("mddecl expression entered")
        try:
            t1, lexer = self._type_expression(lexer)
            t2 = self._eat("IDENTIFIER", lexer)
            t3 = self._eat("(", lexer)

            print("mddecl expression going to fmllist expression")
            t4, lexer = self._fmllist_expression(lexer)

            t5 = self._eat(")", lexer)

            t6, lexer = self._mdbody_expression(lexer)


            root_node = Node(
                self._mddecl_expression.__name__,
                [node for node in [t1, t2, t3, t4, t5, t6] if isinstance(node, Node)],
                True
            )

            print("mddecl expression exited")
            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

        except:
            raise ParseError(self._mddecl_expression.__name__)

    def _fmllist_expression(self, lexer):

        try:
            print("fmllist expression entered")
            current_lexer = copy.deepcopy(lexer)
            t1, current_lexer = self._type_expression(current_lexer)
            print("type expression exited, returning to fmllist expression")
            t2 = self._eat("IDENTIFIER", current_lexer)

            t3, current_lexer = self._kleene_closure_loop(self._fmlrest_expression, current_lexer)

            root_node = Node(
                self._fmllist_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:
            return (None, lexer)


    def _fmlrest_expression(self, lexer):
        print("fmlrest expression entered")

        try:
            t1 = self._eat(",", lexer)
            t2, lexer = self._type_expression(lexer)
            t3 = self._eat("IDENTIFIER", lexer)

            root_node = Node(
                self._fmlrest_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            raise ParseError(self._fmlrest_expression.__name__)

    def _type_expression(self, lexer):

        try:
            print("Type expression entered")
            next_token = lexer.peek()

            if next_token.token_name == "Int":
                t1 = self._eat("Int", lexer)

            elif next_token.token_name == "Bool":
                t1 = self._eat("Bool", lexer)

            elif next_token.token_name == "String":
                t1 = self._eat("String", lexer)

            elif next_token.token_name == "Void":
                t1 = self._eat("Void", lexer)

            elif next_token.token_name == "CLASS_NAME":
                t1 = self._eat("CLASS_NAME", lexer)

            else:
                raise ParseError

            root_node = Node(
                self._type_expression.__name__,
                [node for node in [t1] if isinstance(node, Node)],
                True
            )
            print("Terminating type expression")
            return (root_node, lexer)

        except:
            raise ParseError(self._type_expression.__name__)

    def _mdbody_expression(self, lexer):

        print("mdbody expression entered")

        try:
            t1 = self._eat("{", lexer)
            t2, lexer = self._kleene_closure_loop(self._vardecl_expression, lexer)
            t3, lexer = self._positive_closure_loop(self._stmt_expression, lexer)

            t4 = self._eat("}", lexer)

            root_node = Node(
                self._mdbody_expression.__name__,
                [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            raise ParseError(self._fmlrest_expression.__name__)

    def _stmt_expression(self, lexer):
        try:
            print("stmt expression entered")
            next_token = lexer.peek()

            if next_token.token_name == "if":
                print("Type checking for if")
                t1 = self._eat("if", lexer)
                t2 = self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat("{", lexer)
                t6, lexer = self._positive_closure_loop(self._stmt_expression, lexer)
                t7 = self._eat("}", lexer)
                t8 = self._eat("else", lexer)
                t9 = self._eat("{", lexer)
                t10, lexer = self._positive_closure_loop(self._stmt_expression, lexer)
                t11 = self._eat("}", lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "while":
                print("Type checking for while")
                t1 = self._eat("while", lexer)
                t2 = self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat("{", lexer)
                t6, lexer = self._kleene_closure_loop(self._stmt_expression, lexer)
                t7 = self._eat("}", lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2, t3, t4, t5, t6, t7] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "readln":

                t1 = self._eat("readln", lexer)
                t2 = self._eat("(", lexer)
                t3 = self._eat("IDENTIFIER", lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat(";", lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "println":

                t1 = self._eat("println", lexer)
                t2 = self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat(";", lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "IDENTIFIER":
                print("stmt expression - IDENTIFER entered")

                t1 = self._eat("IDENTIFIER", lexer)
                t2 = self._eat("=", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(";", lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

            elif next_token.token_name == "return":
                t1 = self._eat("return", lexer)
                t2, lexer = self._stmtalpha_expression(lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

            else:
                print("STMT expression going into atom expression")
                t1, lexer = self._atom_expression(lexer)
                t2, lexer = self._stmtbeta_expression(lexer)

                root_node = Node(
                    self._stmt_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )


            return (
                root_node,
                lexer
            )

        except ParseError as e:
            print("Type expression encountered exception")
            raise e

        except Exception as f:
            print("Type expression encountered exception")
            print(f)
            raise ParseError(self._type_expression.__name__)

    def _stmtalpha_expression(self, lexer):

        try:
            print("stmt alpha expression entered")
            next_token = lexer.peek()

            if next_token.token_name == ";":
                t1 = self._eat(";", lexer)
                root_node = Node(
                    self._stmtalpha_expression.__name__,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                return root_node, lexer

            else:
                t1, lexer = self._exp_expression(lexer)

                print("exp expression exited, returning to stmt alpha expression")
                t2 = self._eat(";", lexer)

                root_node = Node(
                    self._stmtalpha_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

        except:
            raise ParseError(self._stmtalpha_expression.__name__)

    def _stmtbeta_expression(self, lexer):

        try:
            print("stmt beta expression entered")
            next_token = lexer.peek()

            if next_token.token_name == ".":
                t1 = self._eat(".", lexer)
                t2 = self._eat("IDENTIFIER", lexer)
                t3 = self._eat("=", lexer)
                t4, lexer = self._exp_expression(lexer)
                t5 = self._eat(";", lexer)

                root_node = Node(
                    self._stmtbeta_expression.__name__,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            else:

                t1 = self._eat("(", lexer)
                t2, lexer = self._explist_expression(lexer)
                t3 = self._eat(")", lexer)
                t4 = self._eat(";", lexer)

                root_node = Node(
                    self._stmtbeta_expression.__name__,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

        except:
            raise ParseError(self._stmtbeta_expression.__name__)

    def _exp_expression(self, lexer):

        try:
            print("exp expression entered")
            try:
                print("exp expression going to bexp")
                t1, lexer = self._bexp_expression(lexer)
                root_node = Node(
                    self._exp_expression.__name__,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                print("bexp expression found, returning to exp expression")
                return (root_node, lexer)
            except:
                print("exp expression left bexp for aexp")
                try:
                    print("exp expression going to aexp")
                    t1, lexer = self._aexp_expression(lexer)
                    print("Aexp expression found in exp expression")
                    root_node = Node(
                        self._exp_expression.__name__,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )
                    return (root_node, lexer)
                except:
                    print("exp expression going to sexp")
                    try:
                        t1, lexer = self._sexp_expression(lexer)
                        root_node = Node(
                            self._exp_expression.__name__,
                            [node for node in [t1] if isinstance(node, Node)],
                            True
                        )
                        return (root_node, lexer)
                    except ParseError as e:
                        print("exp expression unable to find match")
                        raise ParseError(self._exp_expression.__name__)

        except ParseError as e:
            print("exp expression exciting with exception")
            raise e

        except:
            raise ParseError(self._exp_expression.__name__)

    def _bexp_expression(self, lexer):

        try:
            print("bexp expression entered")
            t1, lexer = self._conj_expression(lexer)

            print("conj expression resolved, returning to bexp expression")
            t2, lexer = self._bexpalpha_expression(lexer)
            print("bexpalpha expression resolved, returning to bexp expression")
            root_node = Node(
                self._bexp_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )
            return (
                root_node,
                lexer
            )

        except ParseError as e:
            print("bexp expression exited with exception")
            raise e

    def _bexpalpha_expression(self, lexer):

        try:
            current_lexer = copy.deepcopy(lexer)
            print("bexp alpha expression entered")
            t1 = self._eat("||", current_lexer)
            t2, current_lexer = self._conj_expression(current_lexer)
            t3, current_lexer = self._bexpalpha_expression(current_lexer)

            root_node = Node(
                self._bexpalpha_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:
            print("bexp alpha expression exited with exception")
            return (None, lexer)

    def _conj_expression(self, lexer):

        try:
            print("conj expression entered")
            t1, lexer = self._rexp_expression(lexer)

            print("rexp expression resolved, returning to conj expression")
            t2, lexer = self._conjalpha_expression(lexer)
            print("conjalpha expression resolved, returning to conj expression")
            root_node = Node(
                self._conj_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )
            return (
                root_node,
                lexer
            )

        except ParseError as e:
            raise e

    def _conjalpha_expression(self, lexer):

        try:
            current_lexer = copy.deepcopy(lexer)
            t1 = self._eat("&&", current_lexer)
            t2, current_lexer = self._rexp_expression(current_lexer)
            print("rexp expression resolved, returning to conjalpha expression")
            t3, current_lexer = self._conjalpha_expression(current_lexer)

            root_node = Node(
                self._conjalpha_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:
            return (None, lexer)

    def _rexp_expression(self, lexer):

        try:
            print("rexp expression entered")
            print("lexer next token: " + lexer.peek().value)

            try:
                current_lexer = copy.deepcopy(lexer)
                t1, current_lexer = self._aexp_expression(current_lexer)
                print("aexp expression resolved, returning to rexp expression first time")

                t2, current_lexer = self._bop_expression(current_lexer)
                print("bop expression resolved, returning to rexp expression")
                t3, current_lexer = self._aexp_expression(current_lexer)
                print("aexp expression resolved, returning to rexp expression second time")

                root_node = Node(
                    self._rexp_expression.__name__,
                    [node for node in [t1, t2, t3] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    current_lexer
                )

            except:
                print("rexp expression (aexp bop aexp) encounted exception")
                try:
                    current_lexer = copy.deepcopy(lexer)
                    t1, current_lexer = self._bgrd_expression(current_lexer)

                    root_node = Node(
                        self._rexp_expression.__name__,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )

                    return (root_node, current_lexer)

                except ParseError as e:
                    raise ParseError(self._rexp_expression.__name__)

            raise ParseError(self._rexp_expression.__name__)

        except:
            raise ParseError(self._rexp_expression.__name__)

    def _bop_expression(self, lexer):

        try:
            print("bop expression entered")
            next_token = lexer.peek()

            if next_token.token_name == "<":
                t1 = self._eat("<", lexer)

            elif next_token.token_name == ">":
                t1 = self._eat(">", lexer)

            elif next_token.token_name == "<=":
                t1 = self._eat("<=", lexer)

            elif next_token.token_name == ">":
                t1 = self._eat(">=", lexer)

            elif next_token.token_name == "==":
                t1 = self._eat("==", lexer)

            elif next_token.token_name == "!=":
                t1 = self._eat("!=", lexer)

            else:
                print("bop expression exiting with exception")
                raise ParseError(self._bop_expression.__name__)

            root_node = Node(
                self._bop_expression.__name__,
                [node for node in [t1] if isinstance(node, Node)],
                True
            )

            return (root_node, lexer)

        except ParseError as e:
            raise e

        except:
            raise ParseError(self._bop_expression.__name__)

    def _bgrd_expression(self, lexer):

        try:
            print("bgrd expression entered")
            next_token = lexer.peek()

            if next_token.token_name == "!":
                t1 = self._eat("!", lexer)
                t2, lexer = self._bgrd_expression(lexer)

                root_node = Node(
                    self._bgrd_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "true":
                t1 = self._eat("true", lexer)
                root_node = Node(
                    self._bgrd_expression.__name__,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                return root_node, lexer

            elif next_token.token_name == "false":
                t1 = self._eat("false', lexer")
                root_node = Node(
                    self._bgrd_expression.__name__,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )
                return root_node, lexer

            else:
                try:

                    print("Token after atom: " + lexer.peek(1).token_name)
                    if lexer.peek(1).token_name in "+-*/":
                        print("bgrd should not handle")
                        # Defer to _aexp or _sexp if any of these operators
                        # are after the atom
                        raise ParseError(self._bgrd_expression.__name__)
                    print("bgrd expression going into atom expression")
                    t1, lexer = self._atom_expression(lexer)
                    root_node = Node(
                        self._bgrd_expression.__name__,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )
                    return root_node, lexer

                except:
                    print("atom expression exited with exception, returning to bgrd expression")
                    raise ParseError(self._bgrd_expression.__name__)
        except:
            raise ParseError(self._bgrd_expression.__name__)

    def _aexp_expression(self, lexer):

        try:
            print("aexp expression entered")
            t1, lexer = self._term_expression(lexer)

            print("term expression resolved, returning to aexp expression")
            t2, lexer = self._aexpalpha_expression(lexer)

            print("aexp expression found and exited")
            root_node = Node(
                self._aexp_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )
            return (
                root_node,
                lexer
            )

        except:
            raise ParseError(self._aexp_expression.__name__)

    def _aexpalpha_expression(self, lexer):

        try:
            current_lexer = copy.deepcopy(lexer)
            print("aexp alpha expression entered")
            next_token = current_lexer.peek()

            if next_token.token_name == "+":
                t1 = self._eat("+", current_lexer)

            elif next_token.token_name == "-":
                t1 = self._eat("-", lexer)

            else:
                print("aexp alpha expression returns empty string")
                return (None, current_lexer)

            t2, current_lexer = self._term_expression(current_lexer)
            t3, current_lexer = self._aexpalpha_expression(current_lexer)



            root_node = Node(
                self._aexpalpha_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:
            return (None, lexer)

    def _term_expression(self, lexer):

        try:
            print("term expression entered")
            t1, lexer = self._ftr_expression(lexer)
            t2, lexer = self._termalpha_expression(lexer)

            root_node = Node(
                self._term_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            print("term expression exited")
            return (
                root_node,
                lexer
            )

        except:
            raise ParseError(self._term_expression.__name__)

    def _termalpha_expression(self, lexer):

        try:
            current_lexer = copy.deepcopy(lexer)
            print("term alpha expression entered")
            next_token = current_lexer.peek()

            if next_token.token_name == "*":
                t1 = self._eat("*", current_lexer)

            elif next_token.token_name == "/":
                t1 = self._eat("/", lexer)

            else:
                print("term alpha expression returns empty string")
                return (None, current_lexer)

            t2, current_lexer = self._termalpha_expression(current_lexer)

            root_node = Node(
                self._termalpha_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:
            return (None, lexer)

    def _ftr_expression(self, lexer):

        try:
            print("ftr expression entered")
            next_token = lexer.peek()

            if next_token.token_name == "INTEGER_LITERAL":
                t1 = self._eat("INTEGER_LITERAL", lexer)

                root_node = Node(
                    self._ftr_expression.__name__,
                    [node for node in [t1] if isinstance(node, Node)],
                    True
                )

                return (root_node, lexer)

            elif next_token.token_name == "-":
                t1 = self._eat("-", lexer)
                t2, lexer = self._ftr_expression(lexer)

                root_node = Node(
                    self._ftr_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            else:

                try:
                    print("ftr expression going to atom expression")
                    t1, lexer = self._atom_expression(lexer)
                    root_node = Node(
                        self._ftr_expression.__name__,
                        [node for node in [t1] if isinstance(node, Node)],
                        True
                    )
                    print("atom expression completed, returning to atom expression")
                    return root_node, lexer

                except:
                    raise ParseError(self._ftr_expression.__name__)

        except:
            raise ParseError(self._ftr_expression.__name__)

    def _sexp_expression(self, lexer):

        try:
            print("sexp expression entered")
            next_token = lexer.peek()
            if next_token.token_name == "STRING_LITERAL":
                t1 = self._eat("STRING_LITERAL", lexer)

            else:
                print("sexp going into atom expression")
                t1, lexer = self._atom_expression(lexer)
                print("sexp found atom expression")

            t2, lexer = self._sexpalpha_expression(lexer)

            root_node = Node(
                self._sexp_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                lexer
            )

        except:
            print("sexp expression exited with exception")
            raise ParseError(self._sexp_expression.__name__)

    def _sexpalpha_expression(self, lexer):

        try:
            current_lexer = copy.deepcopy(lexer)
            print("sexp alpha expression entered")
            t1 = self._eat("+", current_lexer)
            t2, current_lexer = self._sexp_expression(current_lexer)
            t3, current_lexer = self._sexpalpha_expression(current_lexer)

            root_node = Node(
                self._sexpalpha_expression.__name__,
                [node for node in [t1, t2, t3] if isinstance(node, Node)],
                True
            )

            return (
                root_node,
                current_lexer
            )

        except:

            return (None, lexer)

    def _atom_expression(self, lexer):

        try:
            print("atom expression entered")
            next_token = lexer.peek()
            print("atom expression - next token: " + next_token.token_name)

            if next_token.token_name == "this":
                t1 = self._eat("this", lexer)
                t2, lexer = self._atomalpha_expression(lexer)

                root_node = Node(
                    self._atom_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "new":
                t1 = self._eat("new", lexer)
                t2 = self._eat("CLASS_NAME", lexer)
                t3 = self._eat("(", lexer)
                t4 = self._eat(")", lexer)
                t5, lexer = self._atomalpha_expression(lexer)

                root_node = Node(
                    self._atom_expression.__name__,
                    [node for node in [t1, t2, t3, t4, t5] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "(":
                t1 = self._eat("(", lexer)
                t2, lexer = self._exp_expression(lexer)
                t3 = self._eat(")", lexer)
                t4, lexer = self._atomalpha_expression(lexer)

                root_node = Node(
                    self._atom_expression.__name__,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "null":
                t1 = self._eat("null", lexer)
                t2, lexer = self._atomalpha_expression(lexer)

                root_node = Node(
                    self._atom_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    lexer
                )

            elif next_token.token_name == "IDENTIFIER":
                print("atom expression - IDENTIFER")
                t1 = self._eat("IDENTIFIER", lexer)
                t2, lexer = self._atomalpha_expression(lexer)


                root_node = Node(
                    self._atom_expression.__name__,
                    [node for node in [t1, t2] if isinstance(node, Node)],
                    True
                )
                print("atom expression - IDENTIFER exited")
                return (
                    root_node,
                    lexer
                )

            else:
                raise ParseError(self._atom_expression.__name__)

        except:
            print("atom expression exited with exception")
            raise ParseError(self._atom_expression.__name__)

    def _atomalpha_expression(self, lexer):

        try:
            print("atom alpha expression entered")
            next_token = lexer.peek()

            if next_token.token_name == ".":
                current_lexer = copy.deepcopy(lexer)
                t1 = self._eat(".", current_lexer)
                t2 = self._eat("IDENTIFIER", current_lexer)
                t3, current_lexer = self._atomalpha_expression(current_lexer)

                root_node = Node(
                    self._atomalpha_expression.__name__,
                    [node for node in [t1, t2, t3] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    current_lexer
                )

            elif next_token.token_name == "(":
                current_lexer = copy.deepcopy(lexer)
                t1 = self._eat("(", current_lexer)
                t2, current_lexer = self._explist_expression(current_lexer)
                t3 = self._eat(")", current_lexer)
                t4, current_lexer = self._atomalpha_expression(current_lexer)

                root_node = Node(
                    self._atomalpha_expression.__name__,
                    [node for node in [t1, t2, t3, t4] if isinstance(node, Node)],
                    True
                )

                return (
                    root_node,
                    current_lexer
                )

            else:
                print("atom alpha expression returns empty string")
                return (None, lexer)

        except:
            return (None, lexer)

    def _explist_expression(self, lexer):

        try:
            t1, lexer = self._exp_expression(lexer)
            t2, lexer = self._kleene_closure_loop(self._exprest_expression, lexer)

            root_node = Node(
                self._explist_expression.__name__,
                [node for node in [t1, t2] if isinstance(node, Node)],
                True
            )

            return (
                root_node,lexer
            )

        except:
            return (None, lexer)

    def _exprest_expression(self, lexer):

        try:
            t1 = self._eat(",", lexer)
            t2, lexer = self._exp_expression(lexer)

            root_node = Node(
                self._exprest_expression.__name__,
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
            raise ParseError(self._exprest_expression.__name__)

    def parse(self, f) -> None:

        self.lex.lex_content(f)

        self.parse_tree.head = self._program_expression(self.lex)

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        parser = Parser()
        #sys.stdout.write(str(parser.parse(f) + "\n"))
        parser.parse(f)
        sys.stdout.write(str(parser.parse_tree.head) + "\n")
        sys.stdout.write(str(parser.parse_tree.head.children) + "\n")
        sys.stdout.write(str(parser.parse_tree.head.children[0].children) + "\n")
        sys.stdout.write(str(parser.parse_tree.pretty_print()) + "\n")
        #sys.stdout.write(str(parser.parse_tree.total_nodes()))

if __name__ == "__main__":

    __main__()
