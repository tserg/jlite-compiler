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
    label_count: int

    def __init__(self, debug: bool=False) -> None:
        self.parser = Parser()
        self.debug = debug
        self.label_count = 0

    def _parse_content(self, f) -> None:
        self.parser.parse(f)
        self.parser.type_check()

    def _create_new_label(self) -> int:

        self.label_count += 1
        return self.label_count

    def _generate_ir3(self):

        # Reset label count
        self.label_count = 0
        return self._program_expression(self.parser.ast.head)

    def _program_expression(self, ast):

        program_node = Program3Node()

        if self.debug:
            sys.stdout.write("Program expression - Node received: " + str(ast) + "\n")

        cdata_node = self._get_cdata3(ast)
        cmtd_node = self._get_cmtd3(ast)

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

    def _get_cmtd3(self, ast_node: Any, mddata_node: Any=None):

        if self.debug:
            sys.stdout.write("Getting CMtd - Current AST node: " + str(ast_node.class_name) + "\n")

        # Get main class method declaration
        if isinstance(ast_node, MainClassNode):
            main_class_md_node = CMtd3Node()
            main_class_md_node.set_method_name("main")
            main_class_md_node.set_return_type(BasicType.VOID)

            argument_node = Arg3Node("this", ast_node.class_name)

            if ast_node.main_arguments:
                # Append additional arguments to argument node
                argument_node = self._get_fmllist(ast_node.main_arguments, argument_node)

            main_class_md_node.set_arguments(argument_node)

            if ast_node.main_variable_declarations:

                var_decl_node = self._get_var_decl(ast_node.main_variable_declarations)
                main_class_md_node.set_variable_declarations(var_decl_node)

            stmt_node = self._get_stmt(ast_node.main_statements)
            main_class_md_node.set_statements(stmt_node)

            mddata_node = main_class_md_node

            if self.debug:
                sys.stdout.write("Getting CMtd - Initialising main method node\n")

        # Get method declarations

        elif isinstance(ast_node, ClassDeclNode):

            if self.debug:
                sys.stdout.write("Getting CMtd - Subsequent class declaration found: " + str(ast_node.class_name) + "\n")

            new_md_decl_node = self._get_md_decl(ast_node.class_name, ast_node.method_declarations, mddata_node)
            #mddata_node.add_sibling(new_md_decl_node)

        if ast_node.sibling:
            mddata_node = self._get_cmtd3(ast_node.sibling, mddata_node)

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

    def _get_md_decl(self, class_name: str, ast_node: Any, md_decl_node: Any=None):

        if self.debug:
            sys.stdout.write("Getting MdDecl - Initiated.\n")
            sys.stdout.write("Getting MdDecl - Vardecl: " + str(ast_node.variable_declarations)+ "\n")


        new_md_decl_node = CMtd3Node()
        new_md_decl_node.set_method_name(ast_node.method_name)
        new_md_decl_node.set_return_type(ast_node.return_type)

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
        stmt_node = self._get_stmt(ast_node.statements)
        new_md_decl_node.set_statements(stmt_node)

        if md_decl_node:
            md_decl_node.add_sibling(new_md_decl_node)

        else:
            md_decl_node = new_md_decl_node

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting MdDecl - Additional MdDecl node detected.\n")

            md_decl_node = self._get_md_decl(class_name, ast_node.sibling, new_md_decl_node)

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

    def _get_stmt(self, ast_node: Any, stmt_node: Any=None):
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


            expression_node = self._get_exp3(ast_node.assigned_value)

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

            else_expression_node = self._get_stmt(ast_node.else_expression)
            goto_end_node = GoTo3Node(goto=end_expression_label_node.label_id)

            if self.debug:
                sys.stdout.write("Getting Stmt - If expression detected: " + str(ast_node.if_expression)+ "\n")

            if_expression_node = self._get_stmt(ast_node.if_expression)

            if_goto_node.add_child(else_expression_node)
            else_expression_node.add_child(goto_end_node)
            goto_end_node.add_child(if_expression_label_node)
            if_expression_label_node.add_child(if_expression_node)
            if_expression_node.add_child(end_expression_label_node)

            new_stmt_node = if_goto_node

        else:

            new_stmt_node = None

        if ast_node.sibling:
            self._get_stmt(ast_node.sibling, new_stmt_node)

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

    def _get_exp3(self, ast_node: Any):

        if self.debug:
            sys.stdout.write("Getting Exp - Initiated.\n")
            sys.stdout.write("Getting Exp - ASTNode: " + str(ast_node) + "\n")

        return None

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
