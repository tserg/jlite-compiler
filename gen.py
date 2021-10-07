import os
import sys
import copy

from collections import deque

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

from symbol_table import *

from ast import *

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
    symbol_table_stack: Deque
    label_count: int
    temp_var_count: int

    def __init__(self, debug: bool=False) -> None:
        self.parser = Parser()
        self.debug = debug
        self.label_count = 0
        self.temp_var_count = 0
        self.symbol_table_stack = deque()

    def add_symbol_table(self, symbol_table: SymbolTable):
        self.symbol_table_stack.append(symbol_table)

    def pop_symbol_table(self) -> None:
        self.symbol_table.pop()

    def _get_temp_var_count(self) -> int:
        self.temp_var_count += 1
        return self.temp_var_count

    def _parse_content(self, f) -> None:
        self.parser.parse(f)
        self.parser.type_check()

    def _create_new_label(self) -> int:

        self.label_count += 1
        return self.label_count

    def _initialise_symbol_table(self) -> "SymbolTable":

        self.parser.get_initial_env()

        symbol_table = SymbolTable()

        for j in range(1, len(self.parser.ast.initial_env)):

            class_descriptor = self.parser.ast.initial_env[j]

            methods = class_descriptor[1][1]
            class_name = class_descriptor[0]

            if len(methods) > 0:

                for i in range(len(methods)):
                    md = methods[i]
                    symbol_table.insert(
                        md[0],
                        md[1],
                        "%" + str(class_name) + "_" +  str(i),
                        "class_methods"
                    )

        return symbol_table

    def _generate_ir3(self):

        # Reset label count
        self.label_count = 0
        self.temp_var_count = 0

        # Set up initial environment
        symbol_table = self._initialise_symbol_table()

        if self.debug:
            sys.stdout.write("Generating IR3 - Initialised symbol table: " + str(symbol_table) + "\n")

        return self._program_expression(symbol_table, self.parser.ast.head)

    def _program_expression(self, symbol_table: Deque, ast: Any):

        # Set up initial symbol table
        symbol_table = self._initialise_symbol_table()

        program_node = Program3Node()

        if self.debug:
            sys.stdout.write("Program expression - Node received: " + str(ast) + "\n")

        cdata_node = self._get_cdata3(ast)
        cmtd_node = self._get_cmtd3(symbol_table, ast)

        if self.debug:
            sys.stdout.write("Program expression - CData received: " + str(cdata_node) + "\n")
            sys.stdout.write("Program expression - MdData received: " + str(cmtd_node) + "\n")

        program_node.set_class_data(cdata_node)
        program_node.set_method_data(cmtd_node)

        if self.debug:
            sys.stdout.write("Program expression - CData processed.\n")

        return program_node

    def _get_cdata3(self, ast_node: Any, cdata_node: Any=None):

        if isinstance(ast_node, MainClassNode) or isinstance(ast_node, ClassDeclNode):

            if self.debug:
                sys.stdout.write("Getting CData - Class node detected.\n")

            new_cdata_node = CData3Node(ast_node.class_name)

            # Get variable declarations

            if isinstance(ast_node, ClassDeclNode) and ast_node.variable_declarations:

                if self.debug:
                    sys.stdout.write("Getting CData - Variable declarations detected in class: " + str(ast_node.class_name) + "\n")

                var_decl_node = self._get_var_decl(ast_node.variable_declarations)

                if self.debug:
                    sys.stdout.write("Getting CData - Variable declarations added in class: " + str(ast_node.class_name) + "\n")

                new_cdata_node.set_var_decl(var_decl_node)

            # If there is a sibling before, add newly created node as a sibling

            if cdata_node:
                cdata_node.sibling = new_cdata_node

                if self.debug:
                    sys.stdout.write("Getting CData - Adding class node as sibling: " + str(ast_node.class_name) + "\n")

            # Otherwise, set current node
            else:
                cdata_node = new_cdata_node

                if self.debug:
                    sys.stdout.write("Getting CData - No IR3 node, initialising IR3 node to current class: " + str(ast_node.class_name) + "\n")

        # If there are more class declarations, call this function recursively
        if isinstance(ast_node.sibling, ClassDeclNode):
            cdata_node = self._get_cdata3(ast_node.sibling, new_cdata_node)

        return cdata_node

    def _get_cmtd3(self, symbol_table: Deque, ast_node: Any, mddata_node: Any=None):

        if self.debug:
            sys.stdout.write("Getting CMtd - Current AST node: " + str(ast_node.class_name) + "\n")
            sys.stdout.write("Getting Cmtd - Current symbol table: " + str(symbol_table) + "\n")
        # Get main class method declaration
        if isinstance(ast_node, MainClassNode):
            main_class_md_node = CMtd3Node("main", BasicType.VOID)

            argument_node = Arg3Node("this", ast_node.class_name)

            if ast_node.main_arguments:
                # Append additional arguments to argument node
                argument_node = self._get_fmllist(ast_node.main_arguments, argument_node)

            main_class_md_node.set_arguments(argument_node)

            if ast_node.main_variable_declarations:

                var_decl_node = self._get_var_decl(ast_node.main_variable_declarations)
                main_class_md_node.set_variable_declarations(var_decl_node)

            stmt_node = self._get_stmt(symbol_table, ast_node.main_statements)
            main_class_md_node.set_statements(stmt_node)

            mddata_node = main_class_md_node

            if self.debug:
                sys.stdout.write("Getting CMtd - Initialising main method node\n")

        # Get method declarations

        elif isinstance(ast_node, ClassDeclNode):

            if self.debug:
                sys.stdout.write("Getting CMtd - Subsequent class declaration found: " + str(ast_node.class_name) + "\n")
                sys.stdout.write("Getting CMtd - Current symbol table: " + str(symbol_table) + "\n")
            new_md_decl_node = self._get_md_decl(symbol_table, ast_node.class_name, ast_node.method_declarations, mddata_node)
            #mddata_node.add_sibling(new_md_decl_node)

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting CMtd - Passing symbol table to sibling: " + str(symbol_table) + "\n")

            mddata_node = self._get_cmtd3(symbol_table, ast_node.sibling, mddata_node)

        return mddata_node

    def _get_var_decl(self, ast_node: Any, var_decl_node: Any=None):

        if self.debug:
            sys.stdout.write("Getting VarDecl - Value detected: " + str(ast_node.value) + "\n")

        new_var_decl_node = VarDecl3Node(ast_node.value, ast_node.type)

        if self.debug:
            sys.stdout.write("Getting VarDecl - New VarDecl node added.\n")

        if var_decl_node:
            var_decl_node.add_sibling(new_var_decl_node)

        else:
            var_decl_node = new_var_decl_node

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting VarDecl - Additional VarDecl node detected.\n")

            new_var_decl_node = self._get_var_decl(ast_node.sibling, new_var_decl_node)

        return var_decl_node

    def _get_md_decl(self, symbol_table: Deque, class_name: str, ast_node: Any, md_decl_node: Any=None):

        if self.debug:
            sys.stdout.write("Getting MdDecl - Initiated.\n")
            sys.stdout.write("Getting MdDecl - Current node: " + str(ast_node)+ "\n")
            sys.stdout.write("Getting MdDecl - Method name: " + str(ast_node.method_name)+ "\n")
            sys.stdout.write("Getting MdDecl - Symbol table: " + str(symbol_table) + "\n")

        temp_md_id = symbol_table.lookup(ast_node.method_name)[3]

        new_md_decl_node = CMtd3Node(method_id=temp_md_id, return_type=ast_node.return_type)

        if self.debug:
            sys.stdout.write("Getting MdDecl - New MdDecl node added for method: " + str(ast_node.method_name)+ "\n")

        # Get arguments
        argument_node = Arg3Node("this", class_name)
        new_md_decl_node.set_arguments(argument_node)

        if ast_node.arguments:

            if self.debug:
                sys.stdout.write("Getting MdDecl - Arguments detected.\n")

            argument_node = self._get_fmllist(ast_node.arguments, argument_node)

        if self.debug:
            sys.stdout.write("Getting MdDecl - Vardecl: " + str(ast_node.variable_declarations)+ "\n")

        # Get variable declarations
        if ast_node.variable_declarations:

            if self.debug:
                sys.stdout.write("Getting MdDecl - Variable declarations detected.\n")

            var_decl_node = self._get_var_decl(ast_node.variable_declarations)

            if var_decl_node:
                if self.debug:
                    sys.stdout.write("Getting MdDecl - Variable declarations node created.\n")

            new_md_decl_node.set_variable_declarations(var_decl_node)

        # Get statements
        stmt_node = self._get_stmt(symbol_table, ast_node.statements)
        new_md_decl_node.set_statements(stmt_node)

        if md_decl_node:
            md_decl_node.add_sibling(new_md_decl_node)

        else:
            md_decl_node = new_md_decl_node

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting MdDecl - Additional MdDecl node detected.\n")

            md_decl_node = self._get_md_decl(symbol_table, class_name, ast_node.sibling, new_md_decl_node)

        return md_decl_node

    def _get_fmllist(self, ast_node: Any, argument_node: Any=None):
        if self.debug:
            sys.stdout.write("Getting FmlList - Initiated.\n")

        if isinstance(ast_node, ArgumentNode):
            if self.debug:
                sys.stdout.write("Getting FmlList - ArgumentNode detected.\n")

            arg_ir3_node = Arg3Node(ast_node.value, ast_node.type)

            if argument_node:
                argument_node.add_sibling(arg_ir3_node)

            else:
                argument_node = arg_ir3_node

        if ast_node.sibling:
            argument_node = self._get_fmllist(ast_node.sibling, arg_ir3_node)

        return argument_node

    def _get_stmt(self, symbol_table: Deque, ast_node: Any, stmt_node: Any=None):
        if self.debug:
            sys.stdout.write("Getting Stmt - Initiated.\n")

        if isinstance(ast_node, ReadLnNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - ReadLn detected.\n")

            new_stmt_node = ReadLn3Node(id3=ast_node.identifier.value)

        elif isinstance(ast_node, PrintLnNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - PrintLn detected.\n")
                sys.stdout.write("Getting Stmt - PrintLn value: " + str(ast_node.expression.value) + "\n")

            new_stmt_node = PrintLn3Node(expression=ast_node.expression.value)

        elif isinstance(ast_node, AssignmentNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - Assignment detected.\n")
                sys.stdout.write("Getting Stmt - Identifier: " + str(ast_node.identifier) + "\n")

            if isinstance(ast_node.identifier, InstanceNode):

                if self.debug:
                    sys.stdout.write("Getting Stmt - Class attribute assignment detected.\n")

                new_stmt_node = ClassAttributeAssignment3Node(
                    ast_node.identifier.atom.value,
                    ast_node.identifier.identifier.value
                )

            else:
                new_stmt_node = Assignment3Node()
                new_stmt_node.set_identifier(ast_node.identifier.value)

            expression_node = self._get_exp3(symbol_table, ast_node.assigned_value)
            new_stmt_node.set_assigned_value(expression_node)

        elif isinstance(ast_node, IfElseNode):

            if self.debug:
                sys.stdout.write("Getting Stmt - IfElse detected.\n")

            if_expression_label_node = Label3Node(label_id=self._create_new_label())
            end_expression_label_node = Label3Node(label_id=self._create_new_label())

            if self.debug:
                sys.stdout.write("Getting Stmt - Condition detected: " + str(ast_node.condition)+ "\n")

            condition_node = self._get_rel_exp3(ast_node.condition)

            if_goto_node = IfGoTo3Node(
                rel_exp=condition_node,
                goto=if_expression_label_node.label_id
            )

            if self.debug:
                sys.stdout.write("Getting Stmt - Else expression detected: " + str(ast_node.else_expression)+ "\n")

            else_expression_node = self._get_stmt(symbol_table, ast_node.else_expression)
            goto_end_node = GoTo3Node(goto=end_expression_label_node.label_id)

            if self.debug:
                sys.stdout.write("Getting Stmt - If expression detected: " + str(ast_node.if_expression)+ "\n")

            if_expression_node = self._get_stmt(symbol_table, ast_node.if_expression)

            if_goto_node.add_child(else_expression_node)

            last_of_else_expression = else_expression_node

            while last_of_else_expression.sibling:
                last_of_else_expression = last_of_else_expression.sibling

            last_of_else_expression.add_child(goto_end_node)
            goto_end_node.add_child(if_expression_label_node)
            if_expression_label_node.add_child(if_expression_node)

            last_of_if_expression = if_expression_node

            while last_of_if_expression.sibling:
                last_of_if_expression = last_of_if_expression.sibling

            last_of_if_expression.add_child(end_expression_label_node)

            new_stmt_node = if_goto_node

        elif isinstance(ast_node, ReturnNode):

            if self.debug:
                sys.stdout.write("Getting Stmt - Return detected.\n")

            if ast_node.return_value:

                if self.debug:
                    sys.stdout.write("Getting Stmt - Return value detected.\n")

                return_exp = self._get_exp3(symbol_table, ast_node.return_value)
                return_node = Return3Node(return_exp.value)

                last_return_exp = return_exp

                while last_return_exp.child:
                    last_return_exp = last_return_exp.child

                last_return_exp.add_child(return_node)

                new_stmt_node = return_exp

            else:

                if self.debug:
                    sys.stdout.write("Getting Stmt - No return value detected.\n")

                new_stmt_node = Return3Node()

        else:

            new_stmt_node = None

        if ast_node.sibling:
            new_stmt_node = self._get_stmt(symbol_table, ast_node.sibling, new_stmt_node)

        if stmt_node:
            stmt_node.add_sibling(new_stmt_node)

        else:
            stmt_node = new_stmt_node

        return stmt_node

    def _get_rel_exp3(self, ast_node: Any):

        if self.debug:
            sys.stdout.write("Getting RelExp - Initiated.\n")
            sys.stdout.write("Getting RelExp - ASTNode: " + str(ast_node) + "\n")

        if isinstance(ast_node, RelOpNode):

            if self.debug:
                sys.stdout.write("Getting RelExp - RelOp detected.\n")

            new_node = RelOp3Node(
                ast_node.left_operand.value,
                ast_node.right_operand.value,
                ast_node.value
            )

        else:
            new_node = IR3Node(ast_node.value)

        return new_node

    def _get_exp3(self, symbol_table: Deque, ast_node: Any):

        if self.debug:
            sys.stdout.write("Getting Exp - Initiated.\n")
            sys.stdout.write("Getting Exp - ASTNode: " + str(ast_node) + "\n")

        if isinstance(ast_node, NegationNode) or isinstance(ast_node, ComplementNode) or \
            isinstance(ast_node, RelOpNode):
            # <Uop3><idc3>
            new_exp_node = None

        elif isinstance(ast_node, InstanceNode):

            if self.debug:
                sys.stdout.write("Getting Exp - InstanceNode detected.\n")

            if isinstance(ast_node.child, ExpListNode):
                # <id3>(<VList3>)
                if self.debug:
                    sys.stdout.write("Getting Exp - Method call detected.\n")

                temp_md_id = symbol_table.lookup(ast_node.identifier.value)[3]

                if self.debug:
                    sys.stdout.write("Getting Exp - Temp method identifier found: " + str(temp_md_id) + "\n")
                    sys.stdout.write("Getting Exp - Identifier value: " + str(ast_node.identifier.type) + "\n")

                new_exp_node = MethodCall3Node(method_id=temp_md_id)
                args = self._get_vlist(ast_node.child)

                class_instance_node = IR3Node(ast_node.atom.value)
                class_instance_node.add_child(args)

                new_exp_node.set_arguments(class_instance_node)

            else:
                # <id3>.<id3>
                new_exp_node = None

        elif isinstance(ast_node, ClassInstanceNode):
            # new <cname>()
            if self.debug:
                sys.stdout.write("Getting Exp - ClassInstance node detected.\n")

            new_exp_node = ClassInstance3Node(ast_node.target_class.value)


        elif isinstance(ast_node, BinOpNode) or isinstance(ast_node, ArithmeticOpNode):
            # <idc3> <Bop3> <idc3>
            new_exp_node = None

        else:

            if self.debug:
                sys.stdout.write("Getting Exp - Checking for identifier and constant.\n")

            # <idc3>

            if ast_node.is_identifier:
                # <id3>
                if self.debug:
                    sys.stdout.write("Getting Exp - Identifier detected.\n")

                new_exp_node = None
            else:
                # <Const>
                if self.debug:
                    sys.stdout.write("Getting Exp - Constant detected.\n")

                temp_var_count = self._get_temp_var_count()
                temp_var = "_t"+str(temp_var_count)

                temp_var_node = VarDecl3Node(temp_var, ast_node.type)

                temp_var_assignment_node = Assignment3Node()
                temp_var_assignment_node.set_identifier(temp_var)

                assigned_value_node = IR3Node(ast_node.value)
                temp_var_assignment_node.set_assigned_value(assigned_value_node)

                temp_var_node.add_child(temp_var_assignment_node)
                if self.debug:
                    sys.stdout.write("Getting Exp - temp var node child: " + str(temp_var_node.child) + "\n")

                new_exp_node = temp_var_node

        return new_exp_node

    def _get_vlist(self, ast_node: Any, v_node: Any=None):

        if self.debug:
            sys.stdout.write("Getting VList - Initiated.\n")
            sys.stdout.write("Getting VList - ASTNode: " + str(ast_node) + "\n")

        if ast_node.expression:
            new_v_node = IR3Node(value=ast_node.expression.value)

        if ast_node.expression.child:
            new_v_node = IR3Node(ast_node.expression.child, new_v_node)

        if v_node:
            v_node.add_child(new_v_node)

        else:
            v_node = new_v_node

        return v_node

    def generate_ir3(self, f) -> None:
        self._parse_content(f)
        self.ir3_tree = IR3Tree(self._generate_ir3())

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
