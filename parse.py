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
    ASTNode,
    MainClassNode,
    ClassDeclNode,
    MdDeclNode,
    ArithmeticOpNode,
    BinOpNode,
    RelOpNode,
    AssignmentNode,
    InstanceNode,
    ClassInstanceNode,
    ReturnNode,
    IfElseNode,
    WhileNode,
    ReadLnNode,
    PrintLnNode,
    ArgumentNode,
    VarDeclNode,
    ExpListNode,
    NegationNode,
    ComplementNode,
    AbstractSyntaxTree,
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
    ast: AbstractSyntaxTree
    symbol_table: dict
    debug: bool

    def __init__(self, debug: bool=False) -> None:
        self.lex = Lexer()
        self.symbol_table = {}
        self.debug = debug

    def _lex_content(self, f) -> None:
        self.lex.lex_content(f)

    def _eat(
        self,
        expected_token: str,
        lexer: Lexer,
        type: str=''
    ) -> Any:
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

            is_identifier = False

            if expected_token == "IDENTIFIER" or expected_token == "CLASS_NAME" or \
                found_token.value == 'this':
                is_identifier = True
            # Create node for found token
            new_node = ASTNode(found_token.value, type, is_identifier)

            if self.debug:
                sys.stdout.write((
                    "New node created with value " + new_node.value + \
                    " of type " + new_node.type + \
                    " and is identifier: " +str(new_node.is_identifier) +'\n'
                ))

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

                if self.debug:
                    sys.stdout.write("Expression found for " + expression.__name__ + " in positive closure.\n")


                last_node.add_sibling(temp_node)
                last_node = temp_node
                lexer = current_lexer

                if self.debug:
                    sys.stdout.write("Lexer updated for " + expression.__name__ + " in positive closure.\n")

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

            self._eat("class", lexer)
            class_name = self._eat("CLASS_NAME", lexer)
            self._eat("{", lexer)
            self._eat("Void", lexer)
            self._eat("main", lexer)
            self._eat("(", lexer)

            args, lexer = self._fmllist_expression(lexer)

            if self.debug:
                sys.stdout.write(
                    "FmlList expression found, returning to MainClass expression " + \
                    "\n"
                )

                sys.stdout.write(lexer.peek().value)
                sys.stdout.write(lexer.peek(1).value)
                sys.stdout.write(lexer.peek(2).value)

            self._eat(")", lexer)
            var_decl, stmt, lexer = self._mdbody_expression(lexer)
            self._eat("}", lexer)

            if class_name.value not in self.symbol_table.keys():
                self.symbol_table[class_name.value] = "IDENTIFIER"

            main_class_node = MainClassNode()
            main_class_node.set_class_name(class_name.value)
            main_class_node.set_arguments(args)
            main_class_node.set_variable_declarations(var_decl)
            main_class_node.set_statements(stmt)

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

            self._eat("class", lexer)
            t2 = self._eat("CLASS_NAME", lexer)
            self._eat("{", lexer)
            t4, lexer = self._kleene_closure_loop(self._vardecl_expression, lexer)

            if self.debug:
                sys.stdout.write("VarDecl expression found, returned to ClassDecl." + "\n")

            t5, lexer = self._kleene_closure_loop(self._mddecl_expression, lexer)

            if self.debug:
                sys.stdout.write("MdDecl expression found, returned to ClassDecl." + "\n")
                sys.stdout.write("Next token in ClassDecl: " + lexer.peek().value +"\n")

            self._eat("}", lexer)

            classdecl_node = ClassDeclNode('class', 'classDecl')
            classdecl_node.set_class_name(t2.value)

            if t4:
                classdecl_node.set_variable_declarations(t4)

            if t5:
                classdecl_node.set_method_declarations(t5)

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
            self._eat(";", lexer)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            var = VarDeclNode(t2.value, t1.value)

            return (
                var,
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
            self._eat("(", lexer)

            args, lexer = self._fmllist_expression(lexer)
            self._eat(")", lexer)

            var_decl, stmt, lexer = self._mdbody_expression(lexer)

            if t2.value not in self.symbol_table.keys():
                self.symbol_table[t2.value] = "IDENTIFIER"

            root_node = MdDeclNode(t1.value, 'MdDecl')

            root_node.set_method_name(t2.value)
            root_node.set_return_type(t1.value)
            root_node.set_arguments(args)
            root_node.set_variable_declarations(var_decl)
            root_node.set_statements(stmt)

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

            type_node = ArgumentNode(t2.value, t1.value)

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

            self._eat(",", lexer)
            t2, lexer = self._type_expression(lexer)
            t3 = self._eat("IDENTIFIER", lexer)

            if t3.value not in self.symbol_table.keys():
                self.symbol_table[t3.value] = "IDENTIFIER"

            type_node = ArgumentNode(t3.value, t2.value)

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

            self._eat("{", lexer)
            t2, lexer = self._kleene_closure_loop(
                self._vardecl_expression,
                lexer
            )

            t3, lexer = self._positive_closure_loop(
                self._stmt_expression,
                lexer
            )

            if self.debug:
                sys.stdout.write('Stmt expression exited, returned to MdBody expression.\n')
                sys.stdout.write('Next token: ' + lexer.peek().value + '\n')

            self._eat("}", lexer)

            return (
                t2, # variable declarations
                t3, # statements
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
        root_node: Any
        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmt_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == "if":

                self._eat("if", lexer)
                self._eat("(", lexer)
                condition, lexer = self._exp_expression(lexer)
                self._eat(")", lexer)
                self._eat("{", lexer)

                if_expression, lexer = self._positive_closure_loop(
                    self._stmt_expression,
                    lexer
                )

                self._eat("}", lexer)
                self._eat("else", lexer)
                self._eat("{", lexer)

                else_expression, lexer = self._positive_closure_loop(
                    self._stmt_expression,
                    lexer
                )

                t11 = self._eat("}", lexer)

                root_node = IfElseNode('if', 'ifElse')
                root_node.set_condition(condition)
                root_node.set_if_expression(if_expression)
                root_node.set_else_expression(else_expression)

            elif next_token.token_name == "while":

                self._eat("while", lexer)
                self._eat("(", lexer)
                condition, lexer = self._exp_expression(lexer)
                self._eat(")", lexer)
                self._eat("{", lexer)

                while_expression, lexer = self._kleene_closure_loop(
                    self._stmt_expression,
                    lexer
                )

                self._eat("}", lexer)

                root_node = WhileNode('while', 'while')
                root_node.set_condition(condition)
                root_node.set_while_expression(while_expression)

            elif next_token.token_name == "readln":

                self._eat("readln", lexer)
                self._eat("(", lexer)
                t3 = self._eat("IDENTIFIER", lexer)
                self._eat(")", lexer)
                self._eat(";", lexer)

                if t3.value not in self.symbol_table.keys():
                    self.symbol_table[t3.value] = "IDENTIFIER"

                root_node = ReadLnNode('readln', 'readln')
                root_node.set_identifier(t3)

            elif next_token.token_name == "println":

                self._eat("println", lexer)
                self._eat("(", lexer)
                t3, lexer = self._exp_expression(lexer)
                self._eat(")", lexer)
                self._eat(";", lexer)

                root_node = PrintLnNode('println', 'println')
                root_node.set_expression(t3)

            elif next_token.token_name == "IDENTIFIER" and \
                lexer.peek(1).value != '.':

                # If there is a ".", let else clause handle

                if self.debug:
                    sys.stdout.write("Stmt expression - Identifier found.\n")

                t1 = self._eat("IDENTIFIER", lexer)
                self._eat("=", lexer)
                t3, lexer = self._exp_expression(lexer)
                self._eat(";", lexer)

                if t1.value not in self.symbol_table.keys():
                    self.symbol_table[t1.value] = "IDENTIFIER"

                root_node = AssignmentNode('=')
                root_node.set_identifier(t1)
                root_node.set_assigned_value(t3)

            elif next_token.token_name == "return":
                t1 = self._eat("return", lexer)
                t2, lexer = self._stmtbeta_expression(lexer)

                if self.debug:
                    sys.stdout.write("Stmt expression - 'return' found" + "\n")
                    sys.stdout.write("Next token: " + lexer.peek().value + '\n')

                    sys.stdout.write("Return node to be created.\n")

                return_node = ReturnNode('return', 'return')

                if self.debug:
                    sys.stdout.write("Return node created.\n")

                if t2:
                    return_node.set_return_value(t2)

                root_node = return_node

                if self.debug:
                    sys.stdout.write("Return node created.\n")

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

    def _stmtbeta_expression(self, lexer: Lexer):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmtbeta_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if next_token.token_name == ";":
                self._eat(";", lexer)

                return None, lexer

            else:
                t1, lexer = self._exp_expression(lexer)

                if self.debug:
                    sys.stdout.write('Exp expression found, returned to Stmtbeta expression.\n')
                    if t1:
                        sys.stdout.write('Exp expression index 0: ' + t1.value + "\n")
                    if t1.child:
                        sys.stdout.write('Exp expression index 1: ' + t1.child.value + "\n")

                self._eat(";", lexer)

                return (
                    t1,
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

    def _stmtalpha_expression(self, lexer: Lexer, atom_node: ASTNode):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._stmtalpha_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if self.debug:
                sys.stdout.write(
                    "Stmtalpha expression - Next token: " + str(next_token.value) + "\n"
                )

            if next_token.token_name == ".":
                self._eat(".", lexer)
                t2 = self._eat("IDENTIFIER", lexer)

                if self.debug:
                    sys.stdout.write(
                        "Stmtalpha expression - Identifier token consumed.\n"
                    )

                self._eat("=", lexer)
                t4, lexer = self._exp_expression(lexer)
                self._eat(";", lexer)

                if self.debug:
                    sys.stdout.write(
                        "Stmtalpha expression - All tokens consumed.\n"
                    )

                instance_node = InstanceNode('instance', 'thisInstance')
                instance_node.set_atom(atom_node)
                instance_node.set_identifier(t2)

                root_node = AssignmentNode('=')
                root_node.set_identifier(instance_node)
                root_node.set_assigned_value(t4)

                return (
                    root_node,
                    lexer
                )

            else:

                self._eat("(", lexer)
                t2, lexer = self._explist_expression(lexer)
                self._eat(")", lexer)
                self._eat(";", lexer)

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
                    sys.stdout.write("Next token: " + str(lexer.peek().value) + "\n")

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
                        if self.debug:
                            sys.stdout.write("SExp expression exception encountered, returned to Exp expression" + "\n")

                        raise e

        except:
            if self.debug:
                sys.stdout.write("Expression exception encountered, backtracking" + "\n")

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
            if self.debug:
                sys.stdout.write("BExp expression exception encountered, backtracking" + "\n")
            raise e

    def _bexpalpha_expression(self, lexer: Lexer, left_node: Any):

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

            t1 = BinOpNode(t1.value, 'Bool')
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

    def _conjalpha_expression(self, lexer: Lexer, left_node: Any):

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

            t1 = BinOpNode(t1.value, 'Bool')
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


                binop_node = RelOpNode(t2.value, 'Bool')
                binop_node.set_left_operand(t1)
                binop_node.set_right_operand(t3)

                return (
                    binop_node,
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

            current_lexer = copy.deepcopy(lexer)

            if next_token.token_name == "!":
                t1 = self._eat("!", current_lexer)
                t2, current_lexer = self._bgrd_expression(current_lexer)

                negation_node = ComplementNode(
                    complement_expression=t2,
                    value='!',
                    type='Bool')

                t1 = negation_node

            elif next_token.token_name == "true":
                t1 = self._eat("true", current_lexer, 'Bool')

            elif next_token.token_name == "false":
                t1 = self._eat("false", current_lexer, 'Bool')

            else:
                try:

                    if current_lexer.peek(1).token_name in "+-*/":
                        if self.debug:
                            sys.stdout.write("bgrd expression should not handle" + "\n")
                        # Defer to _aexp or _sexp if any of these operators
                        # are after the atom
                        raise InvalidExpressionError

                    if self.debug:
                        sys.stdout.write("BGrd expression - Going to Atom expression.\n")

                    t1, current_lexer = self._atom_expression(current_lexer)

                except:
                    last_consumed_token = current_lexer.get_last_consumed_token()
                    raise ParseError(
                        self._bgrd_expression.__name__,
                        last_consumed_token.value,
                        last_consumed_token.start_index,
                        last_consumed_token.start_line
                    )

            if self.debug:
                sys.stdout.write("BGrd expression found.\n")
                sys.stdout.write("Lexer next token: " + str(current_lexer.peek().value) + "\n")

            if current_lexer.peek().value in '+-/*':

                if self.debug:
                    sys.stdout.write("Atom expression should not handle class attribute assignment." + "\n")
                # Defer to _sexp if any of these operators are after the atom
                raise InvalidExpressionError

            return (
                t1,
                current_lexer
            )

        except:

            if self.debug:
                sys.stdout.write("BGrd exception encountered, backtracking" + "\n")

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

    def _aexpalpha_expression(self, lexer: Lexer, left_node: Any):

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
                t1 = self._eat("+", current_lexer)

            elif next_token.token_name == "-":
                t1 = self._eat("-", current_lexer)

            else:
                return (left_node, current_lexer)

            t2, current_lexer = self._term_expression(current_lexer)

            t1 = ArithmeticOpNode(t1.value)
            t1.set_left_operand(left_node)
            t1.set_right_operand(t2)

            if self.debug:
                sys.stdout.write("Term expression found, returned to AExpalpha expression" + "\n")

            t3, current_lexer = self._aexpalpha_expression(current_lexer, t1)

            return (
                t3,
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

    def _termalpha_expression(self, lexer: Lexer, left_node: Any):

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

            t1 = ArithmeticOpNode(t1.value)
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

                t1 = self._eat("INTEGER_LITERAL", lexer, 'Int')

                return (t1, lexer)

            elif next_token.token_name == "-":
                self._eat("-", lexer)
                t2, lexer = self._ftr_expression(lexer)

                negation_node = NegationNode(
                    value='-',
                    type='Int',
                    negated_expression=t2
                )

                return (
                    negation_node,
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
                t1 = self._eat("STRING_LITERAL", lexer, 'String')

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

    def _sexpalpha_expression(self, lexer: Lexer, left_node: Any):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._sexpalpha_expression.__name__
                    + "\n"
                )

            current_lexer = copy.deepcopy(lexer)

            t1 = self._eat("+", current_lexer)

            next_token = current_lexer.peek()
            if next_token.token_name == "STRING_LITERAL":
                t2 = self._eat("STRING_LITERAL", current_lexer, 'String')

            else:
                t2, current_lexer = self._atom_expression(current_lexer)

            t1 = ArithmeticOpNode(t1.value)
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

                if self.debug:
                    sys.stdout.write(
                        "Atom expression - this identified.\n"
                    )

                t1 = self._eat("this", lexer)

                if str(lexer.peek(2).value) == '=':
                    if self.debug:
                        sys.stdout.write("Atom expression should not handle class attribute assignment." + "\n")
                    # Defer to _stmtalpha if it is an assignment of a class attribute
                    # Return "this" only
                    return t1, lexer

                t2, lexer = self._atomalpha_expression(lexer, t1)

                root_node = t2

            elif next_token.token_name == "new":
                t1 = self._eat("new", lexer)

                if self.debug:
                    sys.stdout.write('Atom expression - "new" found' + "\n")

                t2 = self._eat("CLASS_NAME", lexer)

                if self.debug:
                    sys.stdout.write('Atom expression - class found' + "\n")

                class_instance_node = ClassInstanceNode()
                class_instance_node.set_target_class(t2)

                self._eat("(", lexer)
                self._eat(")", lexer)

                t5, lexer = self._atomalpha_expression(lexer, class_instance_node)
                root_node = t5

                if t2.value not in self.symbol_table.keys():
                    self.symbol_table[t2.value] = "CLASS_NAME"

            elif next_token.token_name == "(":
                self._eat("(", lexer)
                t2, lexer = self._exp_expression(lexer)
                self._eat(")", lexer)
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

    def _atomalpha_expression(self, lexer: Lexer, left_node: Any):

        try:
            if self.debug:
                sys.stdout.write(
                    "Entering expression: " + \
                    self._atomalpha_expression.__name__
                    + "\n"
                )

            next_token = lexer.peek()

            if self.debug:
                sys.stdout.write("Atomalpha - Next next token: " + str(lexer.peek(2).value) + "\n")

            if next_token.token_name == "." and \
                lexer.peek(2).value != '=':
                current_lexer = copy.deepcopy(lexer)
                self._eat(".", current_lexer)

                if self.debug:
                    sys.stdout.write("Atomalpha expression: '.' eaten. \n")


                t2 = self._eat("IDENTIFIER", current_lexer)

                if self.debug:
                    sys.stdout.write("Atomalpha expression: id eaten. \n")

                if t2.value not in self.symbol_table.keys():
                    self.symbol_table[t2.value] = "IDENTIFIER"

                root_node = InstanceNode()

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
                self._eat("(", current_lexer)
                t2, current_lexer = self._explist_expression(current_lexer)

                if t2:
                    left_node.add_child(t2)

                self._eat(")", current_lexer)
                t4, current_lexer = self._atomalpha_expression(current_lexer, t2)

                return left_node, current_lexer

            return (left_node, lexer)

        except:
            return (left_node, lexer)


    def _explist_expression(self, lexer: Lexer):

        try:
            t1, lexer = self._exp_expression(lexer)
            t2, lexer = self._kleene_closure_loop(self._exprest_expression, lexer)

            explist_node = ExpListNode('ExpList', 'expression_list')

            if t1:
                explist_node.set_expression(t1)

            if t2:
                t1.add_sibling(t2)


            return (
                explist_node, lexer
            )

        except:
            explist_node = ExpListNode('ExpList', 'expression_list')
            return (explist_node, lexer)

    def _exprest_expression(self, lexer: Lexer):

        try:
            self._eat(",", lexer)
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

        self.ast = AbstractSyntaxTree(self._program_expression(self.lex))

    def type_check(self, debug=False) -> None:
        """
        Type checks the AST

        :param bool debug: display logging for troubleshooting
        """
        self.ast.type_check(debug)
        #sys.stdout.write("Type checking completed\n")

    def get_initial_env(self) -> None:
        """
        Retrieve the initial environment and store it in the AST
        """
        self.ast.initialise_env()
        #sys.stdout.write(str(self.ast.initial_env))

    def pretty_print(self) -> None:
        """
        Prints the AST of the parsed file
        """
        self.ast.pretty_print()

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        parser = Parser(debug=True)
        parser.parse(f)

        parser.pretty_print()

        parser.type_check(debug=True)
        #parser.get_initial_env()
        #sys.stdout.write(str(parser.parse_tree.total_nodes()))

if __name__ == "__main__":

    __main__()
