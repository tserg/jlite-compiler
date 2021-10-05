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

    def _get_stmt(self, ast_node: Any):
        if self.debug:
            sys.stdout.write("Getting Stmt - Initiated.\n")
        pass

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
