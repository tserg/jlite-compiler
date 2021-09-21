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

from ast import *

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

    def _eat(self, expected_token: str, lexer: Lexer, type: str=None) -> Any:
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

            found_token = lexer.get_next_token_from_queue()

            # Create node for found token
            if type:
                new_node = ASTNode(found_token.value, type)
            else:
                new_node = ASTNode(found_token.value, found_token.token_name)


            return new_node

        raise InvalidExpressionError

    def _kleene_closure_loop(
        self,
        expression: Callable,
        lexer: Lexer
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

            root_node, lexer = expression(lexer)

            if root_node:

                repeat_ended = False
                last_node = root_node

                while not repeat_ended:
                    current_lexer = copy.deepcopy(lexer)
                    if self.debug:
                        sys.stdout.write("Next token in Kleene's closure loop: " + current_lexer.peek().value + "\n")

                        sys.stdout.write(
                            ("Kleene closure repeat loop entered for expression: ")
                            + expression.__name__
                            + "\n"
                        )

                    try:
                        temp_node, current_lexer = expression(current_lexer)
                        if self.debug:
                            sys.stdout.write("Successful rep. Next token in Kleene's closure loop: " + current_lexer.peek().value + "\n")

                        last_node.add_sibling(temp_node)
                        if self.debug:
                            sys.stdout.write("Successful rep. Next token in Kleene's closure loop: " + current_lexer.peek().value + "\n")

                        last_node = temp_node
                        if self.debug:
                            sys.stdout.write("Successful rep. Next token in Kleene's closure loop: " + current_lexer.peek().value + "\n")

                        lexer = current_lexer
                        if self.debug:
                            sys.stdout.write("Successful rep. Next token in Kleene's closure loop: " + current_lexer.peek().value + "\n")



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

        if self.debug:
            sys.stdout.write("Kleene closure terminating with next token as: " + lexer.peek().value + "\n")

        return (root_node, lexer)

    def _positive_closure_loop(
        self,
        expression: Callable,
        lexer: Lexer
    ) -> Any:
        """
        Helper function to execute the positive closure on a given expression

        :param Callable expression: the expression with positive closure
        :param Lexer lexer: the lexer at the current state
        :return: tuple of the expression(s) found and the lexer in the state
            after the positive closure
        """

        root_node, lexer = expression(lexer)

        repeat_ended = False

        last_node = root_node

        while not repeat_ended:
            current_lexer = copy.deepcopy(lexer)
            if self.debug:
                sys.stdout.write(
                    ("Positive closure loop triggered for expression: ")
                    + expression.__name__
                    + "\n"
                )
            try:
                temp_node, current_lexer = expression(current_lexer)
                last_node.add_sibling(temp_node)
                last_node = temp_node
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

    def _mainclass_expression(self, lexer: Lexer):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._mainclass_expression.__name__
                    + "\n"
                )

            t1 = self._eat("class", lexer)
            t2 = self._eat("CLASS_NAME", lexer)
            t3 = self._eat("{", lexer)
            t4 = self._eat("Void", lexer)
            t5 = self._eat("main", lexer)
            t6 = self._eat("(", lexer)

            t7, lexer = self._fmllist_expression(lexer)

            if self.debug:
                sys.stdout.write(
                    "FmlList expression found, returning to MainClass expression " + \
                    "\n"
                )

                sys.stdout.write(lexer.peek().value)
                sys.stdout.write(lexer.peek(1).value)
                sys.stdout.write(lexer.peek(2).value)

            t8 = self._eat(")", lexer)
            t9, lexer = self._mdbody_expression(lexer)
            t10 = self._eat("}", lexer)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            main_class_node = MainClassNode('class', 'mainClass')
            main_class_node.set_class_name(t2)
            main_class_node.set_fml_list(t7)
            main_class_node.set_mdbody(t9)

            return (
                main_class_node,
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

    def _classdeclaration_expression(self, lexer: Lexer):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._classdeclaration_expression.__name__
                    + "\n"
                )

            t1 = self._eat("class", lexer)
            t2 = self._eat("CLASS_NAME", lexer)
            t3 = self._eat("{", lexer)
            t4, lexer = self._kleene_closure_loop(self._vardecl_expression, lexer)

            if self.debug:
                sys.stdout.write("VarDecl expression found, returned to ClassDecl." + "\n")

            t5, lexer = self._kleene_closure_loop(self._mddecl_expression, lexer)

            if self.debug:
                sys.stdout.write("MdDecl expression found, returned to ClassDecl." + "\n")
                sys.stdout.write("Next token in ClassDecl: " + lexer.peek().value +"\n")

            t6 = self._eat("}", lexer)

            classdecl_node = ClassDeclNode('class', 'classDecl')
            classdecl_node.set_class_name(t2)

            if t4:
                classdecl_node.set_var_decl(t4)

            if t5:
                classdecl_node.set_mddecl(t5)

            return (
                classdecl_node,
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

    def _vardecl_expression(self, lexer: Lexer):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._vardecl_expression.__name__
                    + "\n"
                )

            t1, lexer = self._type_expression(lexer)
            t2 = self._eat("IDENTIFIER", lexer)
            t3 = self._eat(";", lexer)

            t1.add_child(t2)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            return (
                t1,
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

    def _mddecl_expression(self, lexer: Lexer):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._mddecl_expression.__name__
                    + "\n"
                )

            t1, lexer = self._type_expression(lexer)
            t2 = self._eat("IDENTIFIER", lexer)
            t3 = self._eat("(", lexer)

            t4, lexer = self._fmllist_expression(lexer)
            t5 = self._eat(")", lexer)

            t6, lexer = self._mdbody_expression(lexer)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            root_node = MdDeclNode(t1.value, 'MdDecl')

            root_node.set_identifier(t2)
            root_node.set_fml_list(t4)
            root_node.set_mdbody(t6)

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

    def _fmllist_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._fmllist_expression.__name__
                    + "\n"
                )
            current_lexer = copy.deepcopy(lexer)
            t1, current_lexer = self._type_expression(current_lexer)
            t2 = self._eat("IDENTIFIER", current_lexer)

            type_node = FmlNode(t1.value, t1.type)
            type_node.set_identifier(t2)

            t3, current_lexer = self._kleene_closure_loop(self._fmlrest_expression, current_lexer)

            if self.debug:
                sys.stdout.write("FmlRest expression found, returned to FmlList expression" + "\n")
                sys.stdout.write("Next token in lexer: " + current_lexer.peek().value + "\n")

            type_node.add_sibling(t3)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            return (
                type_node,
                current_lexer
            )

        except:
            return (None, lexer)


    def _fmlrest_expression(self, lexer: Lexer):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._fmlrest_expression.__name__
                    + "\n"
                )

            t1 = self._eat(",", lexer)
            t2, lexer = self._type_expression(lexer)
            t3 = self._eat("IDENTIFIER", lexer)

            if t3.value not in self.symbol_table.keys():
                self.symbol_table[t3.value] = "IDENTIFIER"

            type_node = FmlNode(t2.value, t2.type)
            type_node.set_identifier(t3)

            if self.debug:
                sys.stdout.write("FmlRest expression - next token: " + lexer.peek().value + "\n")

            return (
                type_node,
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

    def _type_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._type_expression.__name__
                    + "\n"
                )

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

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "CLASS_NAME"

            else:
                last_consumed_token = lexer.get_last_consumed_token()
                raise ParseError(
                    self._type_expression.__name__,
                    last_consumed_token.value,
                    last_consumed_token.start_index,
                    last_consumed_token.start_line
                )
                raise ParseError(self._type_expression.__name__)

            return (t1, lexer)

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

    def _mdbody_expression(self, lexer: Lexer):

        try:

            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._mdbody_expression.__name__
                    + "\n"
                )

            t1 = self._eat("{", lexer)
            t2, lexer = self._kleene_closure_loop(
                self._vardecl_expression,
                lexer
            )

            t3, lexer = self._positive_closure_loop(
                self._stmt_expression,
                lexer
            )

            t4 = self._eat("}", lexer)

            root_node = MdBodyNode('MdBody', 'methodBody')
            root_node.set_vardecl(t2)
            root_node.set_stmt(t3)

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

    def _stmt_expression(self, lexer: Lexer):
        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmt_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "if":

                t1 = self._eat("if", lexer)


                t2 = self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat("{", lexer)

                t6, lexer = self._positive_closure_loop(
                    self._stmt_expression,
                    lexer
                )

                t7 = self._eat("}", lexer)
                t8 = self._eat("else", lexer)
                t9 = self._eat("{", lexer)

                t10, lexer = self._positive_closure_loop(
                    self._stmt_expression,
                    lexer
                )

                t11 = self._eat("}", lexer)

                root_node = IfElseNode('if', 'ifElse')
                root_node.set_condition(t3)
                root_node.set_if_expression(t6)
                root_node.set_else_expression(t10)

            elif next_token.token_name == "while":

                t1 = self._eat("while", lexer)
                t2 = self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat("{", lexer)

                t6, lexer = self._kleene_closure_loop(
                    self._stmt_expression,
                    lexer
                )

                t7 = self._eat("}", lexer)

                root_node = WhileNode('while', 'while')
                root_node.set_expression(t3)
                root_node.set_statement(t6)

            elif next_token.token_name == "readln":

                t1 = self._eat("readln", lexer)
                t2 = self._eat("(", lexer)
                t3 = self._eat("IDENTIFIER", lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat(";", lexer)

                if t3.value not in self.symbol_table.keys():
                    self.symbol_table[t3.value] = "IDENTIFIER"

                root_node = ReadLnNode('readln', 'readln')
                root_node.set_identifier(t3)

            elif next_token.token_name == "println":

                t1 = self._eat("println", lexer)
                t2 = self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(")", lexer)
                t5 = self._eat(";", lexer)

                root_node = PrintLnNode('println', 'println')
                root_node.set_expression(t3)

            elif next_token.token_name == "IDENTIFIER":

                t1 = self._eat("IDENTIFIER", lexer)
                t2 = self._eat("=", lexer)
                t3, lexer = self._exp_expression(lexer)
                t4 = self._eat(";", lexer)

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "IDENTIFIER"

                root_node = AssignmentNode('=', 'assignment')
                root_node.set_identifier(t1)
                root_node.set_assigned_value(t3)

            elif next_token.token_name == "return":
                t1 = self._eat("return", lexer)
                t2, lexer = self._stmtbeta_expression(lexer, t1)

                if self.debug:
                    sys.stdout.write("Stmt expression - 'return' found" + "\n")
                    if t2:
                        sys.stdout.write("Stmt beta expression found. Index 0: " + t2.value + "\n")

                    if t2.child:
                        sys.stdout.write("Stmt beta expression found. Index 1: " + t2.child.value + "\n")

                    if t2.child.child:
                        sys.stdout.write("Stmt beta expression found. Index 2: " + t2.child.child.value + "\n")

                return_node = ReturnNode(t2.value, 'return')
                return_node.set_return_value(t2.child)


                root_node = return_node

            else:

                t1, lexer = self._atom_expression(lexer)
                t2, lexer = self._stmtalpha_expression(lexer, t1)

                root_node = t2

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

    def _stmtbeta_expression(self, lexer: Lexer, left_node: Node):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmtbeta_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == ";":
                t1 = self._eat(";", lexer)

                return left_node, lexer

            else:
                t1, lexer = self._exp_expression(lexer)

                if self.debug:
                    sys.stdout.write('Exp expression found, returned to Stmtbeta expression.\n')
                    if t1:
                        sys.stdout.write('Exp expression index 0: ' + t1.value + "\n")
                    if t1.child:
                        sys.stdout.write('Exp expression index 1: ' + t1.child.value + "\n")

                t2 = self._eat(";", lexer)

                left_node.add_child(t1)

                return (
                    left_node,
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

    def _stmtalpha_expression(self, lexer: Lexer, atom_node: Node):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmtalpha_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == ".":
                t1 = self._eat(".", lexer)
                t2 = self._eat("IDENTIFIER", lexer)
                t3 = self._eat("=", lexer)
                t4, lexer = self._exp_expression(lexer)
                t5 = self._eat(";", lexer)


                instance_node = InstanceNode('instance', 'thisInstance')
                instance_node.set_atom(atom_node)
                instance_node.set_identifier(t2)

                root_node = AssignmentNode('=', 'assignment')
                root_node.set_identifier(instance_node)
                root_node.set_expression(t4)

                return (
                    root_node,
                    lexer
                )

            else:

                t1 = self._eat("(", lexer)
                t2, lexer = self._explist_expression(lexer)
                t3 = self._eat(")", lexer)
                t4 = self._eat(";", lexer)

                if t2:
                    atom_node.add_child(t2)

                return (
                    atom_node,
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

    def _exp_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._exp_expression.__name__
                    + "\n"
                )

            try:
                current_lexer = copy.deepcopy(lexer)

                t1, current_lexer = self._bexp_expression(current_lexer)

                if self.debug:
                    sys.stdout.write("BExp expression found, returning to Exp expression" + "\n")

                return (t1, current_lexer)

            except:

                if self.debug:
                    sys.stdout.write("BExp expression exception encountered, returned to Exp expression" + "\n")

                try:
                    current_lexer = copy.deepcopy(lexer)
                    t1, current_lexer = self._aexp_expression(current_lexer)

                    if self.debug:
                        sys.stdout.write("AExp expression found, returning to Exp expression" + "\n")

                    return (t1, current_lexer)
                except:

                    if self.debug:
                        sys.stdout.write("AExp expression exception encountered, returned to Exp expression" + "\n")

                    try:
                        current_lexer = copy.deepcopy(lexer)
                        if self.debug:
                            sys.stdout.write("Exp expression going to SExp expression" + "\n")
                            sys.stdout.write("Next token: " + lexer.peek().value + "\n")

                        t1, current_lexer = self._sexp_expression(current_lexer)

                        if self.debug:
                            sys.stdout.write("SExp expression found, returned to Exp expression" + "\n")

                        return (t1, current_lexer)

                    except ParseError as e:
                        raise e

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

    def _bexp_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bexp_expression.__name__
                    + "\n"
                )

            t1, lexer = self._conj_expression(lexer)
            t2, lexer = self._bexpalpha_expression(lexer, t1)

            return (
                t2,
                lexer
            )

        except ParseError as e:
            raise e

    def _bexpalpha_expression(self, lexer: Lexer, left_node: Node):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bexpalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)

            t1 = self._eat("||", current_lexer)
            t2, current_lexer = self._conj_expression(current_lexer)

            t1 = BinOpNode(t1.value, 'binOp')
            t1.set_left_operand(left_node)
            t1.set_right_operand(t2)

            t3, current_lexer = self._bexpalpha_expression(current_lexer, t1)

            if t3:
                root_node = t3
            else:
                root_node = t1

            return (
                root_node,
                current_lexer
            )

        except:
            return (left_node, lexer)

    def _conj_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._conj_expression.__name__
                    + "\n"
                )
            t1, lexer = self._rexp_expression(lexer)
            t2, lexer = self._conjalpha_expression(lexer, t1)

            return (
                t2,
                lexer
            )

        except ParseError as e:
            raise e

    def _conjalpha_expression(self, lexer: Lexer, left_node: Node):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._conjalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)
            t1 = self._eat("&&", current_lexer)
            t2, current_lexer = self._rexp_expression(current_lexer)

            t1 = BinOpNode(t1.value, 'binOp')
            t1.set_left_operand(left_node)
            t1.set_right_operand(t2)

            t3, current_lexer = self._conjalpha_expression(current_lexer, t1)

            if t3:
                root_node = t3
            else:
                root_node = t1

            return (
                root_node,
                current_lexer
            )

        except:
            return (left_node, lexer)

    def _rexp_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._rexp_expression.__name__
                    + "\n"
                )

            try:
                current_lexer = copy.deepcopy(lexer)
                t1, current_lexer = self._aexp_expression(current_lexer)

                if self.debug:
                    sys.stdout.write(
                        ("aexp expression resolved, "
                        "returning to rexp expression first time")
                        + "\n"
                    )


                t2, current_lexer = self._bop_expression(current_lexer)

                if self.debug:
                    sys.stdout.write(
                        ("bop expression resolved, "
                        "returning to rexp expression")
                        + "\n"
                    )

                t3, current_lexer = self._aexp_expression(current_lexer)

                if self.debug:
                    sys.stdout.write(
                        ("aexp expression resolved, "
                        "returning to rexp expression second time")
                        + "\n"
                    )

                t1.add_sibling(t2)
                t2.add_sibling(t3)

                return (
                    t1,
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
                    t1, current_lexer = self._bgrd_expression(current_lexer)

                    return (t1, current_lexer)

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

    def _bop_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bop_expression.__name__
                    + "\n"
                )
            next_token = lexer.peek()

            if next_token.token_name == "<":
                t1 = self._eat("<", lexer)

            elif next_token.token_name == ">":
                t1 = self._eat(">", lexer)

            elif next_token.token_name == "<=":
                t1 = self._eat("<=", lexer)

            elif next_token.token_name == ">=":
                t1 = self._eat(">=", lexer)

            elif next_token.token_name == "==":
                t1 = self._eat("==", lexer)

            elif next_token.token_name == "!=":
                t1 = self._eat("!=", lexer)

            else:
                last_consumed_token = lexer.get_last_consumed_token()
                raise ParseError(
                    self._bop_expression.__name__,
                    last_consumed_token.value,
                    last_consumed_token.start_index,
                    last_consumed_token.start_line
                )

            return (t1, lexer)

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

    def _bgrd_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._bgrd_expression.__name__
                    + "\n"
                )
            next_token = lexer.peek()

            if next_token.token_name == "!":
                t1 = self._eat("!", lexer)
                t2, lexer = self._bgrd_expression(lexer)

                negation_node = NegationNode(
                    negated_expression=t2,
                    value='!',
                    type='negation')

                t1 = negation_node

            elif next_token.token_name == "true":
                t1 = self._eat("true", lexer)

            elif next_token.token_name == "false":
                t1 = self._eat("false", lexer)

            else:
                try:

                    if lexer.peek(1).token_name in "+-*/":
                        if self.debug:
                            sys.stdout.write("bgrd expression should not handle" + "\n")
                        # Defer to _aexp or _sexp if any of these operators
                        # are after the atom
                        raise InvalidExpressionError

                    t1, lexer = self._atom_expression(lexer)

                except:
                    last_consumed_token = lexer.get_last_consumed_token()
                    raise ParseError(
                        self._bgrd_expression.__name__,
                        last_consumed_token.value,
                        last_consumed_token.start_index,
                        last_consumed_token.start_line
                    )

            return (
                t1,
                lexer
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

    def _aexp_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._aexp_expression.__name__
                    + "\n"
                )

            t1, lexer = self._term_expression(lexer)

            if self.debug:
                sys.stdout.write("Term expression found, returned to AExp expression" + "\n")

            t2, lexer = self._aexpalpha_expression(lexer, t1)

            # Custom logic to check if next token is a STRING_LITERAL
            # If STRING_LITERAL, throw exception to let SExp handle string concatenation
            next_token_1 = lexer.peek()
            next_token_2 = lexer.peek(1)

            if next_token_1.value in ['-', '+'] and next_token_2.token_name == 'STRING_LITERAL':
                raise InvalidExpressionError

            if self.debug:
                sys.stdout.write("AExpalpha expression found, returned to AExp expression" + "\n")
                sys.stdout.write("Next two tokens: " + lexer.peek().value + " " + lexer.peek(1).value + "\n")

            return (
                t2,
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

    def _aexpalpha_expression(self, lexer: Lexer, left_node: Node):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._aexpalpha_expression.__name__
                    + "\n"
                )

                sys.stdout.write("aexp alpha expression entered" + "\n")

            current_lexer = copy.deepcopy(lexer)

            next_token = current_lexer.peek()

            if next_token.token_name == "+":
                t1 = self._eat("+", current_lexer, 'binOp')

            elif next_token.token_name == "-":
                t1 = self._eat("-", current_lexer, 'binOp')

            else:
                return (left_node, current_lexer)

            t2, current_lexer = self._term_expression(current_lexer)

            t1 = ArithmeticOpNode(t1.value, 'arithmeticOp')
            t1.set_left_operand(left_node)
            t1.set_right_operand(t2)

            if self.debug:
                sys.stdout.write("Term expression found, returned to AExpalpha expression" + "\n")

            t3, current_lexer = self._aexpalpha_expression(current_lexer, t1)

            if t3:
                root_node = t3
            else:
                root_node = t1

            return (
                root_node,
                current_lexer,
            )

        except:
            return (left_node, lexer)

    def _term_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._term_expression.__name__
                    + "\n"
                )

            t1, lexer = self._ftr_expression(lexer)

            if self.debug:
                sys.stdout.write("Ftr expression found, returning to Term expression" + "\n")

            t2, lexer = self._termalpha_expression(lexer, t1)

            return (
                t2,
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

    def _termalpha_expression(self, lexer: Lexer, left_node: Node):

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
                t1 = self._eat("*", current_lexer)

            elif next_token.token_name == "/":
                t1 = self._eat("/", current_lexer)

            else:
                return (left_node, current_lexer)

            t2, current_lexer = self._ftr_expression(current_lexer)

            t1 = ArithmeticOpNode(t1.value, 'arithmeticOp')
            t1.set_left_operand(left_node)
            t1.set_right_operand(t2)

            t3, current_lexer = self._termalpha_expression(current_lexer, t1)

            if t3:
                root_node = t3
            else:
                root_node = t1

            return (
                root_node,
                current_lexer
            )

        except:
            return (left_node, lexer)

    def _ftr_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._ftr_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "INTEGER_LITERAL":

                t1 = self._eat("INTEGER_LITERAL", lexer)

                return (t1, lexer)

            elif next_token.token_name == "-":
                t1 = self._eat("-", lexer)
                t2, lexer = self._ftr_expression(lexer)

                t2.value = "-" + t2.value

                return (
                    t2,
                    lexer
                )

            else:

                try:
                    if self.debug:
                        sys.stdout.write(
                            "ftr expression going to atom expression"
                            + "\n"
                        )

                    t1, lexer = self._atom_expression(lexer)

                    if self.debug:
                        sys.stdout.write(
                            "atom expression completed, returning to atom expression"
                            + "\n"
                        )

                    return t1, lexer

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

    def _sexp_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._sexp_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()
            if next_token.token_name == "STRING_LITERAL":
                t1 = self._eat("STRING_LITERAL", lexer)

            else:
                if self.debug:
                    sys.stdout.write(
                        "SExp expression going to Atom expression"
                        + "\n"
                    )

                t1, lexer = self._atom_expression(lexer)

                if self.debug:
                    sys.stdout.write(
                        "Atom expression found, returned to SExp expression"
                        + "\n"
                    )

            t2, lexer = self._sexpalpha_expression(lexer, t1)

            return (
                t2,
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

    def _sexpalpha_expression(self, lexer: Lexer, left_node: Node):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._sexpalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)

            t1 = self._eat("+", current_lexer, 'binOp')
            t2, current_lexer = self._sexp_expression(current_lexer)

            t1 = ArithmeticOpNode(t1.value, 'arithmeticOp')
            t1.set_left_operand(left_node)
            t1.set_right_operand(t2)

            t3, current_lexer = self._sexpalpha_expression(current_lexer, t1)

            return (
                t3,
                current_lexer
            )

        except:

            return (left_node, lexer)

    def _atom_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._atom_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "this":
                t1 = self._eat("this", lexer)
                t2, lexer = self._atomalpha_expression(lexer, t1)

                root_node = t2

            elif next_token.token_name == "new":
                t1 = self._eat("new", lexer)

                if self.debug:
                    sys.stdout.write('Atom expression - "new" found' + "\n")

                t2 = self._eat("CLASS_NAME", lexer)

                if self.debug:
                    sys.stdout.write('Atom expression - class found' + "\n")


                t3 = self._eat("(", lexer)
                t4 = self._eat(")", lexer)

                class_instance_node = ClassInstanceNode('new', 'newClassInstance')
                class_instance_node.set_class_name(t2)

                t5, lexer = self._atomalpha_expression(lexer, class_instance_node)
                root_node = t5

                if t2.value not in self.symbol_table.keys():
                    self.symbol_table[t2.value] = "CLASS_NAME"

            elif next_token.token_name == "(":
                t1 = self._eat("(", lexer)
                t2, lexer = self._exp_expression(lexer)
                t3 = self._eat(")", lexer)
                t4, lexer = self._atomalpha_expression(lexer, t2)

                root_node = t4

            elif next_token.token_name == "null":
                t1 = self._eat("null", lexer)
                t2, lexer = self._atomalpha_expression(lexer, t1)

                root_node = t2

            elif next_token.token_name == "IDENTIFIER":

                t1 = self._eat("IDENTIFIER", lexer)
                t2, lexer = self._atomalpha_expression(lexer, t1)

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "IDENTIFIER"

                root_node = t2

            else:
                last_consumed_token = lexer.get_last_consumed_token()
                raise ParseError(
                    self._atom_expression.__name__,
                    last_consumed_token.value,
                    last_consumed_token.start_index,
                    last_consumed_token.start_line
                )

            return (
                root_node,
                lexer
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

    def _atomalpha_expression(self, lexer: Lexer, left_node: Node):

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
                t1 = self._eat(".", current_lexer)

                if self.debug:
                    sys.stdout.write("Atomalpha expression: '.' eaten. \n")


                t2 = self._eat("IDENTIFIER", current_lexer)

                if self.debug:
                    sys.stdout.write("Atomalpha expression: id eaten. \n")

                if t2.value not in self.symbol_table.keys():
                    self.symbol_table[t2.value] = "IDENTIFIER"

                root_node = InstanceNode('this', 'thisInstance')

                if self.debug:
                    sys.stdout.write("Atomalpha expression: Root node created. \n")

                root_node.set_atom(left_node)

                if self.debug:
                    sys.stdout.write("Atomalpha expression: Atom of root node set. \n")

                root_node.set_identifier(t2)

                if self.debug:
                    sys.stdout.write('Atomalpha expression: Identifier of root node set: ' + root_node.value + "\n")

                t3, current_lexer = self._atomalpha_expression(current_lexer, root_node)

                return t3, current_lexer

            elif next_token.token_name == "(":
                current_lexer = copy.deepcopy(lexer)
                t1 = self._eat("(", current_lexer)
                t2, current_lexer = self._explist_expression(current_lexer)

                if t2:
                    left_node.add_child(t2)

                t3 = self._eat(")", current_lexer)
                t4, current_lexer = self._atomalpha_expression(current_lexer, t2)



                return left_node, current_lexer

            return (left_node, lexer)

        except:
            return (left_node, lexer)


    def _explist_expression(self, lexer: Lexer):

        try:
            t1, lexer = self._exp_expression(lexer)
            t2, lexer = self._kleene_closure_loop(self._exprest_expression, lexer)

            if t1:
                explist_node.set_expression(t1)

            if t2:
                t1.add_sibling(t2)

            explist_node = ExpListNode('ExpList', 'expression_list')

            return (
                explist_node, lexer
            )

        except:
            explist_node = ExpListNode('ExpList', 'expression_list')
            return (explist_node, lexer)

    def _exprest_expression(self, lexer: Lexer):

        try:
            t1 = self._eat(",", lexer)
            t2, lexer = self._exp_expression(lexer)

            return (
                t2,
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
        """
        Lexes the input file into a stream of tokens, then parses using recursive descent parsing

        :param TextIO f: the input file
        """

        self._lex_content(f)

        self.parse_tree = AbstractSyntaxTree(self._program_expression(self.lex))

    def pretty_print(self) -> None:
        """
        Prints the parsed file
        """

        sys.stdout.write("Parsed output: " + "\n\n")
        self.parse_tree.pretty_print()

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
