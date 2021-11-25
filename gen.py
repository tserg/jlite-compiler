import os
import sys
import copy

from collections import deque

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Deque,
    Union,
    TextIO,
)

from parse import (
    Parser,
)

from symbol_table import SymbolTableStack

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
    ExpListNode,
    NegationNode,
    ComplementNode,
)

from ir3 import (
    IR3Node,
    Program3Node,
    CData3Node,
    CMtd3Node,
    VarDecl3Node,
    Arg3Node,
    Label3Node,
    IfGoTo3Node,
    GoTo3Node,
    ReadLn3Node,
    PrintLn3Node,
    ClassInstance3Node,
    ClassAttribute3Node,
    Assignment3Node,
    MethodCall3Node,
    Return3Node,
    RelOp3Node,
    BinOp3Node,
    UnaryOp3Node,
    IR3Tree,
)

from jlite_type import (
    BasicType,
    FunctionType,
)

class IR3Generator:
    """
    IR3 Generator instance to generate IR3 tree from Parser's AST
    ...

    Attributes
    ----------
    parser: Parser
    debug: bool
    ir3_tree: IR3Tree
    label_count: int
    temp_var_count: int

    Methods
    -------
    _parse_content(f)
        Run the parser through the given file
    _get_temp_var_count()
        Get the count of temporary variables to be used as index for
        next temporary variable
    _create_new_label()
        Returns the index of the next label to be used
    _initialise_symbol_table()
        Initialise a SymbolTableStack with information from the Parser
    _get_last_child(IR3Node)
        Helper function to get the last child of an IR3Node
    _generate_ir3
        Helper function to traverse the AST from the Parser and generate the IR3
        tree
    generate_ir3()
        Generate the IR3Tree from a given file
    pretty_print()
        Prints the generated IR3Tree

    """
    parser: Parser
    debug: bool
    ir3_tree: IR3Tree
    label_count: int
    temp_var_count: int
    symbol_table: "SymbolTableStack"

    def __init__(self, debug: bool=False) -> None:

        self.debug = debug
        self.parser = Parser(self.debug)
        self.label_count = 0
        self.temp_var_count = 0

    def _parse_content(self, f: TextIO) -> None:
        """
        Helper function to parse a file

        :param TextIO f: the input file
        """
        self.parser.parse(f)
        self.parser.type_check(self.debug)

    def _get_temp_var_count(self) -> int:
        """
        Helper function to get the count of temporary variables to be used as
        index for next temporary variable

        :return: the index to be used for the next temporary variable
        """
        self.temp_var_count += 1
        return self.temp_var_count

    def _create_new_label(self) -> int:
        """
        Helper function to get the index for the next label

        :return: the index to be used for the next label
        """
        self.label_count += 1
        return self.label_count

    def _initialise_symbol_table(self) -> "SymbolTableStack":
        """
        Helper function to set up the SymbolTableStack with information from the
        Parser

        :return: the SymbolTableStack to be used for IR3 code generation
        """
        self.parser.get_initial_env()

        symbol_table = SymbolTableStack()

        for j in range(1, len(self.parser.ast.initial_env)):

            class_descriptor = self.parser.ast.initial_env[j]

            methods = class_descriptor[1][1]
            class_name = class_descriptor[0]

            if len(methods) > 0:



                for i in range(len(methods)):
                    md = methods[i]

                    if self.debug:
                        sys.stdout.write("Initialising symbol table methods - " + str(md[1].basic_type_list) + "\n")
                    symbol_table.insert(
                        value=md[0],
                        type=md[1],
                        temp_id="%" + str(class_name) + "_" +  str(i),
                    )

        return symbol_table

    def _get_last_child(
        self,
        ir3_node: Any,
        return_last_parent: bool=False
    ) -> Any:
        """
        Helper function to get the last child of an IR3Node

        :return: the last child of the given IR3Node
        """
        if not ir3_node:
            return None

        last_node = ir3_node
        last_parent_node = None

        if last_node.child:
            while last_node.child:
                last_parent_node = last_node
                last_node = last_node.child

        if return_last_parent:
            return last_node, last_parent_node

        return last_node

    def _generate_ir3(self) -> IR3Node:
        """
        Helper function to traverse the AST from the Parser and generate the IR3
        tree

        :return: the root IR3Node
        """
        # Reset label count
        self.label_count = 0
        self.temp_var_count = 0

        return self._program_expression(self.parser.ast.head)

    def _compute_relop_node_with_constants(
        self,
        ast_node: RelOpNode
    ) -> Any:

        left_operand: Any
        right_operand: Any
        computed_value: bool = False

        bool_from_jlite = {
            'true': True,
            'false': False
        }

        bool_to_jlite = {
            True: 'true',
            False: 'false'
        }

        if ast_node.left_operand.type == BasicType.INT:
            left_operand = int(ast_node.left_operand.value)
            right_operand = int(ast_node.right_operand.value)

        elif ast_node.left_operand.type == BasicType.BOOL:
            left_operand = bool_from_jlite[ast_node.left_operand.value]
            right_operand = bool_from_jlite[ast_node.right_operand.value]

        elif ast_node.left_operand.type == BasicType.STRING:
            left_operand = str(ast_node.left_operand.value)
            right_operand = str(ast_node.right_operand.value)

        if ast_node.value == '>':

            computed_value = left_operand > right_operand

        elif ast_node.value == '>=':

            computed_value = left_operand >= right_operand

        elif ast_node.value == '<':

            computed_value = left_operand < right_operand

        elif ast_node.value == '<=':

            computed_value = left_operand <= right_operand

        elif ast_node.value == '==':

            computed_value = left_operand == right_operand

        elif ast_node.value == '!=':

            computed_value = left_operand != right_operand

        return bool_to_jlite[computed_value]

    def _compute_binop_node_with_constants(
        self,
        ast_node: BinOpNode
    ) -> Any:

        computed_value: Union[str, int, float]

        if ast_node.value == '||':

            if ast_node.left_operand.value == 'true' or \
                ast_node.right_operand.value == 'true':

                return "true"

            return "false"

        elif ast_node.value == "&&":

            if ast_node.left_operand.value == 'false' or \
                ast_node.right_operand.value == 'false':

                return "false"

            return "true"

    def _compute_arithmetic_node_with_constants(
        self,
        ast_node: ArithmeticOpNode
    ) -> Any:

        computed_value: Union[str, int, float]

        if ast_node.value == '+':

            if ast_node.type == BasicType.INT:
                computed_value = int(ast_node.left_operand.value) + \
                    int(ast_node.right_operand.value)

            else:
                # Otherwise, concatenate the strings
                if ast_node.left_operand.value == 'null':
                    left_string = ''
                else:
                    left_string = ast_node.left_operand.value[1:-1]

                if ast_node.right_operand.value == 'null':
                    right_string = ''
                else:
                    right_string = ast_node.right_operand.value[1:-1]

                computed_value = '"' + left_string + \
                    right_string + '"'

        elif ast_node.value == '-':
            computed_value = int(ast_node.left_operand.value) - \
                int(ast_node.right_operand.value)

        elif ast_node.value == '*':
            computed_value = int(ast_node.left_operand.value) * \
                int(ast_node.right_operand.value)

        elif ast_node.value == '/':
            computed_value = int(int(ast_node.left_operand.value) / \
                int(ast_node.right_operand.value))

        return str(computed_value)

    def _derive_ifgoto_condition(
        self,
        ast_node: Any,
        symbol_table: SymbolTableStack
    ) -> Any:

        condition_node: Any

        if self.debug:
            sys.stdout.write("Deriving ifgoto condition.\n")

        if type(ast_node.condition) == RelOpNode and \
            not ast_node.condition.child and \
            not ast_node.condition.sibling and \
            ast_node.condition.left_operand.is_raw_value and \
            ast_node.condition.right_operand.is_raw_value:

            # Shortcut to derive RelOp expression directly if dealing with
            # identifiers/constants only

            if self.debug:
                sys.stdout.write("Getting Stmt - Shortcut to Exp - "
                    "Double constants detected: [" + \
                    str(ast_node.condition.left_operand.value) + "] and [" + \
                    str(ast_node.condition.right_operand.value) + "]\n")
            # If both operands are constants, construct the
            # RelOp3Node directly

            condition_node = RelOp3Node(
                type=BasicType.BOOL,
                left_operand=ast_node.condition.left_operand.value,
                right_operand=ast_node.condition.right_operand.value,
                operator=ast_node.condition.value,
                left_operand_is_raw_value=ast_node.condition.left_operand.is_raw_value,
                right_operand_is_raw_value=ast_node.condition.right_operand.is_raw_value
            )

        else:

            condition_node = self._get_exp3(symbol_table, ast_node.condition)

        return condition_node

    def _program_expression(
        self,
        ast: Any
    ) -> IR3Node:

        # Set up initial symbol table
        symbol_table = self._initialise_symbol_table()
        self.symbol_table = symbol_table

        program_node = Program3Node()

        if self.debug:
            sys.stdout.write("Program expression - Node received: " + \
                str(ast) + "\n")

        cdata_node = self._get_cdata3(symbol_table, ast)
        cmtd_node = self._get_cmtd3(symbol_table, ast)

        if self.debug:
            sys.stdout.write("Program expression - CData received: " + \
                str(cdata_node) + "\n")
            sys.stdout.write("Program expression - MdData received: " + \
                str(cmtd_node) + "\n")

        program_node.set_class_data(cdata_node)
        program_node.set_method_data(cmtd_node)

        if self.debug:
            sys.stdout.write("Program expression - CData processed.\n")

        return program_node

    def _get_cdata3(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any,
        cdata_node: Any=None
    ) -> Optional[IR3Node]:

        new_cdata_node: Any

        if isinstance(ast_node, MainClassNode) or \
            isinstance(ast_node, ClassDeclNode):

            if self.debug:
                sys.stdout.write("Getting CData - Class node detected.\n")

            new_cdata_node = CData3Node(class_name=ast_node.class_name)

            # Get variable declarations

            if isinstance(ast_node, ClassDeclNode):

                if self.debug:
                    sys.stdout.write("Getting CData - "
                        "Variable declarations detected in class: " + \
                        str(ast_node.class_name) + "\n")

                var_decl_node = self._get_var_decl(
                    symbol_table,
                    ast_node.variable_declarations
                )

                if self.debug:
                    sys.stdout.write("Getting CData - "
                        "Variable declarations added in class: " + \
                        str(ast_node.class_name) + "\n")

                new_cdata_node.set_var_decl(var_decl_node)

            # If there is a sibling before, add newly created node as a sibling

            if cdata_node:
                cdata_last_node = self._get_last_child(cdata_node)
                cdata_last_node.add_child(new_cdata_node)

                if self.debug:
                    sys.stdout.write("Getting CData - "
                        "Adding class node as sibling: " + \
                        str(ast_node.class_name) + "\n")

            # Otherwise, set current node
            else:
                cdata_node = new_cdata_node

                if self.debug:
                    sys.stdout.write("Getting CData - No IR3 node, "
                        "initialising IR3 node to current class: " + \
                        str(ast_node.class_name) + "\n")

        # If there are more class declarations, call this function recursively
        if isinstance(ast_node.sibling, ClassDeclNode):
            new_cdata_node = self._get_cdata3(
                symbol_table,
                ast_node.sibling,
                new_cdata_node
            )

        return cdata_node

    def _get_cmtd3(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any,
        mddata_node: Any=None
    ) -> Optional[Any]:

        if self.debug:
            sys.stdout.write("Getting CMtd - Current AST node: " + \
                str(ast_node.class_name) + "\n")
            sys.stdout.write("Getting Cmtd - Current symbol table: " + \
                str(symbol_table) + "\n")
        # Get main class method declaration

        symbol_table.add_empty_st()

        if isinstance(ast_node, MainClassNode):

            argument_node: Any = None

            main_class_md_node = CMtd3Node(
                method_id="main",
                return_type=BasicType.VOID
            )

            argument_node = Arg3Node(
                value="this",
                type=ast_node.class_name
            )

            if ast_node.main_arguments:
                # Append additional arguments to argument node
                argument_node = self._get_fmllist(
                    symbol_table,
                    ast_node.main_arguments,
                    argument_node
                )

            main_class_md_node.set_arguments(argument_node)

            if ast_node.main_variable_declarations:

                var_decl_node = self._get_var_decl(
                    symbol_table,
                    ast_node.main_variable_declarations
                )
                main_class_md_node.set_variable_declarations(var_decl_node)

            stmt_node = self._get_stmt(symbol_table, ast_node.main_statements)
            main_class_md_node.set_statements(stmt_node)

            mddata_node = main_class_md_node

            if self.debug:
                sys.stdout.write("Getting CMtd - "
                    "Initialising main method node\n")

        # Get method declarations

        elif isinstance(ast_node, ClassDeclNode):

            if self.debug:
                sys.stdout.write("Getting CMtd - "
                    "Subsequent class declaration found: " + \
                    str(ast_node.class_name) + "\n")
                sys.stdout.write("Getting CMtd - Current symbol table: " + \
                    str(symbol_table) + "\n")

            if ast_node.variable_declarations:
                var_decl_node = self._get_var_decl(
                    symbol_table,
                    ast_node.variable_declarations
                )

            if ast_node.method_declarations:
                new_md_decl_node = self._get_md_decl(
                    symbol_table,
                    ast_node.class_name,
                    ast_node.method_declarations,
                    mddata_node
                )

        symbol_table.pop_st()

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting CMtd - "
                    "Passing symbol table to sibling: " + \
                    str(symbol_table) + "\n")

            mddata_node = self._get_cmtd3(
                symbol_table,
                ast_node.sibling,
                mddata_node
            )

        return mddata_node

    def _get_var_decl(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any,
        var_decl_node: Any=None
    ) -> Optional[VarDecl3Node]:

        if not ast_node:
            return None

        if self.debug:
            sys.stdout.write("Getting VarDecl - Value detected: " + \
                str(ast_node.value) + "\n")
            sys.stdout.write("Getting VarDecl - Symbol table received: " + \
                str(symbol_table) + "\n")

        new_var_decl_node = VarDecl3Node(
            value=ast_node.value,
            type=ast_node.type
        )

        symbol_table.insert(ast_node.value, ast_node.type)

        if self.debug:
            sys.stdout.write("Getting VarDecl - New VarDecl node added.\n")
            sys.stdout.write("Getting VarDecl - Insert into symbol table" + \
                str(symbol_table) + "\n")

        if var_decl_node:
            var_decl_last_node = self._get_last_child(var_decl_node)
            var_decl_last_node.add_child(new_var_decl_node)

        else:
            var_decl_node = new_var_decl_node

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting VarDecl - "
                    "Additional VarDecl node detected.\n")

            new_var_decl_node = self._get_var_decl(
                symbol_table,
                ast_node.sibling,
                new_var_decl_node
            )

        return var_decl_node

    def _get_md_decl(
        self,
        symbol_table: SymbolTableStack,
        class_name: str,
        ast_node: Any,
        md_decl_node: Any=None
    ) -> CMtd3Node:

        if self.debug:
            sys.stdout.write("Getting MdDecl - Initiated.\n")
            sys.stdout.write("Getting MdDecl - Current node: " + \
                str(ast_node)+ "\n")
            sys.stdout.write("Getting MdDecl - Method name: " + \
                str(ast_node.method_name)+ "\n")
            sys.stdout.write("Getting MdDecl - Symbol table: " + \
                str(symbol_table) + "\n")

        st_lookup: Any = symbol_table.lookup(ast_node.method_name)
        if st_lookup:
            if self.debug:
                sys.stdout.write("Getting MdDecl - Symbol table result - " + \
                    str(st_lookup) + "\n")

            if type(st_lookup) == list:
                args_type = ast_node.get_arguments().basic_type_list

                for st_result in st_lookup:

                    if self.debug:
                        sys.stdout.write("Getting MdDecl - Symbol table multiple results - " + \
                            str(st_result) + "\n")
                        sys.stdout.write(str(args_type) + "\n")
                        sys.stdout.write(str(st_result['type'].basic_type_list) + "\n")

                    if st_result['type'].basic_type_list == args_type:
                        temp_md_id = st_result['temp_id']
            else:
                temp_md_id = st_lookup['temp_id']
        else:
            temp_md_id = st_lookup['temp_id']

        new_md_decl_node = CMtd3Node(
            method_id=temp_md_id,
            return_type=ast_node.return_type
        )

        symbol_table.add_empty_st()

        if self.debug:
            sys.stdout.write("Getting MdDecl - "
                "New MdDecl node added for method: " + \
                str(ast_node.method_name)+ "\n")

        # Get arguments
        argument_node: Optional[Arg3Node] = Arg3Node(
            value="this",
            type=class_name
        )

        symbol_table.insert("this", class_name)

        new_md_decl_node.set_arguments(argument_node)

        if ast_node.arguments:

            if self.debug:
                sys.stdout.write("Getting MdDecl - Arguments detected.\n")

            argument_node = self._get_fmllist(
                symbol_table,
                ast_node.arguments,
                argument_node
            )

        if self.debug:
            sys.stdout.write("Getting MdDecl - Vardecl: " + \
                str(ast_node.variable_declarations)+ "\n")

        # Get variable declarations
        if ast_node.variable_declarations:

            if self.debug:
                sys.stdout.write("Getting MdDecl - "
                    "Variable declarations detected.\n")

            var_decl_node = self._get_var_decl(
                symbol_table,
                ast_node.variable_declarations
            )

            if var_decl_node:
                if self.debug:
                    sys.stdout.write("Getting MdDecl - "
                        "Variable declarations node created.\n")

            new_md_decl_node.set_variable_declarations(var_decl_node)

        # Get statements
        stmt_node = self._get_stmt(symbol_table, ast_node.statements)

        if self.debug:
            sys.stdout.write("Getting MdDecl - Statements detected.\n")
            sys.stdout.write("Getting MdDecl - First statement: " + \
                str(ast_node.statements) + "\n")

        new_md_decl_node.set_statements(stmt_node)

        symbol_table.pop_st()

        if md_decl_node:
            md_decl_last_node = self._get_last_child(md_decl_node)
            md_decl_last_node.add_child(new_md_decl_node)

        else:
            md_decl_node = new_md_decl_node

        if ast_node.sibling:
            if self.debug:
                sys.stdout.write("Getting MdDecl - "
                    "Additional MdDecl node detected.\n")

            md_decl_node = self._get_md_decl(
                symbol_table,
                class_name,
                ast_node.sibling,
                new_md_decl_node
            )

        return md_decl_node

    def _get_fmllist(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any,
        argument_node: Arg3Node=None
    ) -> Optional[Arg3Node]:
        if self.debug:
            sys.stdout.write("Getting FmlList - Initiated.\n")

        if isinstance(ast_node, ArgumentNode):
            if self.debug:
                sys.stdout.write("Getting FmlList - ArgumentNode detected.\n")

            arg_ir3_node: Optional[Arg3Node] = Arg3Node(
                value=ast_node.value,
                type=ast_node.type
            )
            symbol_table.insert(ast_node.value, ast_node.type)

            if argument_node:
                argument_node.add_child(arg_ir3_node)

            else:
                argument_node = arg_ir3_node

            if ast_node.sibling:
                arg_ir3_node = self._get_fmllist(
                    symbol_table,
                    ast_node.sibling,
                    arg_ir3_node
                )

        return argument_node

    def _get_stmt(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any,
        stmt_node: Any=None
    ) -> Any:

        new_stmt_node: Any = None

        if self.debug:
            sys.stdout.write("Getting Stmt - Initiated.\n")
            sys.stdout.write("Getting Stmt - Current AST node type: " + \
                str(type(ast_node)) + "\n")
            sys.stdout.write("Getting Stmt - Current AST node value: " + \
                str(ast_node.value) + "\n")

        if isinstance(ast_node, ReadLnNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - ReadLn detected.\n")

            new_stmt_node = ReadLn3Node(id3=ast_node.identifier.value)

        elif isinstance(ast_node, PrintLnNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - PrintLn detected.\n")
                sys.stdout.write("Getting Stmt - PrintLn value: " + \
                    str(ast_node.expression.value) + "\n")

            if type(ast_node.expression) == ASTNode:
                new_stmt_node = PrintLn3Node(
                    expression=ast_node.expression.value,
                    type=ast_node.expression.type,
                    is_raw_value=ast_node.expression.is_raw_value
                )

            elif type(ast_node.expression) == InstanceNode:

                if self.debug:
                    sys.stdout.write("Getting Stmt - "
                        "PrintLn for class attribute detected.\n")

                println_class_attribute = self._get_exp3(symbol_table, ast_node.expression)

                temp_var = "_t"+str(self._get_temp_var_count())
                temp_var_node = VarDecl3Node(
                    value=temp_var,
                    type=ast_node.expression.type
                )

                symbol_table.insert(temp_var, ast_node.expression.type)

                # Assign value to temporary variable

                temp_var_assignment_node = Assignment3Node(type=ast_node.expression.type)
                temp_var_assignment_node.set_identifier(temp_var)
                temp_var_assignment_node.set_assigned_value(println_class_attribute)
                temp_var_node.add_child(temp_var_assignment_node)

                println_node = PrintLn3Node(
                    expression=temp_var,
                    type=ast_node.expression.type,
                    is_raw_value=ast_node.expression.is_raw_value
                )

                temp_var_assignment_node.add_child(println_node)
                new_stmt_node = temp_var_node

            else:

                if self.debug:
                    sys.stdout.write("Getting Stmt - "
                        "PrintLn value is an expression.\n")

                expression_node = self._get_exp3(
                    symbol_table,
                    ast_node.expression
                )

                last_of_expression = self._get_last_child(expression_node)

                println_node = PrintLn3Node(
                    expression=last_of_expression.identifier,
                    type=last_of_expression.type
                )
                last_of_expression.add_child(println_node)
                new_stmt_node = expression_node

        elif isinstance(ast_node, AssignmentNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - Assignment detected.\n")
                sys.stdout.write("Getting Stmt - Identifier: " + \
                    str(ast_node.identifier) + "\n")
                sys.stdout.write("Getting Stmt - Type: " + \
                    str(ast_node.type) + "\n")

            new_assignment_node = Assignment3Node(type=ast_node.type)
            new_stmt_node = new_assignment_node

            if isinstance(ast_node.identifier, InstanceNode):

                if self.debug:
                    sys.stdout.write("Getting Stmt - "
                        "Class attribute assignment detected.\n")

                object_name=ast_node.identifier.atom.value

                if type(ast_node.identifier.atom) == InstanceNode:

                    if self.debug:
                        sys.stdout.write("Getting Stmt - "
                            "Nested class attribute assignment detected.\n")

                    nested_identifier_node = self._get_exp3(
                        symbol_table,
                        ast_node.identifier.atom
                    )

                    last_of_nested_identifier, parent_of_last_of_nested_identifier = self._get_last_child(
                        nested_identifier_node,
                        return_last_parent=True
                    )

                    if not parent_of_last_of_nested_identifier:
                        parent_of_last_of_nested_identifier = nested_identifier_node

                    if self.debug:
                        sys.stdout.write("Getting Stmt - "
                            "Nested class attribute identifer: " + \
                            str(type(nested_identifier_node)) + "\n")
                        sys.stdout.write("Getting Stmt - "
                            "Nested class attribute identifer last child: " + \
                            str(type(last_of_nested_identifier)) + "\n")
                        sys.stdout.write("Getting Stmt - "
                            "Nested class attribute identifer parent of last child: " + \
                            str(type(parent_of_last_of_nested_identifier)) + "\n")

                    # If single ClassAttribute3Node is retrieved, break it up
                    # into its own variable declaration

                    if type(last_of_nested_identifier) == ClassAttribute3Node:

                        temp_id_var = "_t"+str(self._get_temp_var_count())
                        temp_id_var_node = VarDecl3Node(
                            value=temp_id_var,
                            type=last_of_nested_identifier.type
                        )

                        symbol_table.insert(temp_id_var, last_of_nested_identifier.type)

                        # Assign value to temporary variable

                        temp_id_var_assignment_node = Assignment3Node(
                            type=last_of_nested_identifier.type
                        )
                        temp_id_var_assignment_node.set_identifier(temp_id_var)
                        temp_id_var_assignment_node.set_assigned_value(
                            last_of_nested_identifier
                        )


                        # Link to nested node

                        if nested_identifier_node == last_of_nested_identifier:
                            nested_identifier_node = temp_id_var_node
                        else:
                            parent_of_last_of_nested_identifier.add_child(temp_id_var_node)

                        temp_id_var_node.add_child(temp_id_var_assignment_node)
                        temp_id_var_assignment_node.add_child(new_assignment_node)
                        new_stmt_node = nested_identifier_node

                        object_name = temp_id_var_node.value

                    else:

                        object_name = last_of_nested_identifier.identifier

                class_attribute_node = ClassAttribute3Node(
                    type=ast_node.identifier.type,
                    object_name=object_name,
                    target_attribute=ast_node.identifier.identifier.value,
                    class_name=ast_node.identifier.class_name
                )

                new_assignment_node.set_identifier(class_attribute_node)

            else:

                new_assignment_node.set_identifier(ast_node.identifier.value)

            if type(ast_node.assigned_value) == ASTNode:
                if self.debug:
                    sys.stdout.write("Getting Stmt - "
                        "AssignmentNode - Constant detected.\n")
                    sys.stdout.write("Getting Stmt - "
                        "AssignmentNode - Constant: " + \
                        str(ast_node.assigned_value.value) + "\n")
                    sys.stdout.write("Getting Stmt - "
                        "AssignmentNode - Is raw value: " + \
                        str(ast_node.assigned_value.is_raw_value) + "\n")

                new_assignment_node.set_assigned_value(
                    ast_node.assigned_value.value,
                    ast_node.assigned_value.is_raw_value
                )

            else:
                if self.debug:
                    sys.stdout.write("Getting Stmt - AssignmentNode - "
                        "Expression detected.\n")

                assigned_expression_node = self._get_exp3(
                    symbol_table,
                    ast_node.assigned_value
                )

                if self.debug:
                    sys.stdout.write("Getting Stmt - AssignmentNode - "
                        "Expression found: " + \
                        str(assigned_expression_node) + "\n")

                if assigned_expression_node.child:
                    assigned_expression_last_node = self._get_last_child(assigned_expression_node)
                    new_assignment_node.set_assigned_value(
                        assigned_expression_last_node.identifier
                    )

                    if isinstance(ast_node.identifier, InstanceNode) and \
                        type(ast_node.identifier.atom) == InstanceNode:

                        temp_id_var_assignment_node.add_child(assigned_expression_node)
                        assigned_expression_last_node.add_child(new_assignment_node)

                    else:
                        assigned_expression_last_node.add_child(new_assignment_node)

                        new_stmt_node = assigned_expression_node
                else:
                    new_assignment_node.set_assigned_value(
                        assigned_expression_node
                    )

            if isinstance(ast_node.identifier, InstanceNode) and \
                type(ast_node.identifier.atom) == InstanceNode:

                new_stmt_node = nested_identifier_node

        elif isinstance(ast_node, IfElseNode):

            if self.debug:
                sys.stdout.write("Getting Stmt - IfElse detected.\n")

            if_expression_label_node = Label3Node(
                label_id=self._create_new_label()
            )
            end_expression_label_node = Label3Node(
                label_id=self._create_new_label()
            )

            if self.debug:
                sys.stdout.write("Getting Stmt - Condition detected: " + \
                    str(ast_node.condition)+ "\n")

            condition_node = self._derive_ifgoto_condition(
                ast_node,
                symbol_table
            )

            condition_last_node = self._get_last_child(condition_node)

            # Set rel_exp value to the last child node of condition
            rel_exp_value = condition_last_node

            if self.debug:
                sys.stdout.write("Getting Stmt - IfElse - Last condition: " + \
                    str(condition_last_node)+ "\n")

            # But update to last identifier if last child node of condition
            # is not the condition node itself
            if condition_last_node != condition_node:
                if self.debug:
                    sys.stdout.write("Getting Stmt - IfElse - "
                        "Condition last child is different from condition.\n")

                rel_exp_value = condition_last_node.identifier

            if_goto_node = IfGoTo3Node(
                rel_exp=rel_exp_value,
                goto=if_expression_label_node.label_id
            )

            if self.debug:
                sys.stdout.write("Getting Stmt - Else expression detected: " + \
                    str(ast_node.else_expression)+ "\n")

            # Add symbol table for else scope
            symbol_table.add_empty_st()

            else_expression_node = self._get_stmt(
                symbol_table,
                ast_node.else_expression
            )

            # Pop symbol table for if scope
            symbol_table.pop_st()

            goto_end_node = GoTo3Node(goto=end_expression_label_node.label_id)

            if self.debug:
                sys.stdout.write("Getting Stmt - If expression detected: " + \
                    str(ast_node.if_expression)+ "\n")

            # Add symbol table for else scope
            symbol_table.add_empty_st()

            if_expression_node = self._get_stmt(
                symbol_table,
                ast_node.if_expression
            )

            # Pop symbol table for else scope
            symbol_table.pop_st()

            # Link nodes together

            if condition_last_node != condition_node:
                condition_last_node.add_child(if_goto_node)
                new_stmt_node = condition_node
            else:
                new_stmt_node = if_goto_node

            if_goto_node.add_child(else_expression_node)
            last_of_else_expression = self._get_last_child(else_expression_node)
            last_of_else_expression.add_child(goto_end_node)

            goto_end_node.add_child(if_expression_label_node)
            if_expression_label_node.add_child(if_expression_node)

            last_of_if_expression_node = self._get_last_child(if_expression_node)
            last_of_if_expression_node.add_child(end_expression_label_node)

        elif isinstance(ast_node, WhileNode):
            if self.debug:
                sys.stdout.write("Getting Stmt - While loop detected.\n")

            # Add symbol table for while loop

            symbol_table.add_empty_st()

            while_loop_start_label_node = Label3Node(
                label_id=self._create_new_label()
            )
            while_loop_expression_start_label_node = Label3Node(
                label_id=self._create_new_label()
            )
            while_loop_exit_label_node = Label3Node(
                label_id=self._create_new_label()
            )

            condition_node = self._derive_ifgoto_condition(
                ast_node,
                symbol_table
            )

            if self.debug:
                sys.stdout.write("Getting Stmt - While loop - "
                    "Condition node created: " + str(condition_node) +"\n")
                sys.stdout.write("Getting Stmt - While loop - "
                    "Condition node value: " + str(condition_node.value) +"\n")

            condition_last_node = self._get_last_child(condition_node)

            if self.debug:
                sys.stdout.write("Getting Stmt - While loop - "
                    "Last child of condition found: " + \
                    str(condition_last_node) +"\n")

            # Set rel_exp value to the last child node of condition
            rel_exp_value = condition_last_node

            if self.debug:
                sys.stdout.write("Getting Stmt - While - Last condition: " + \
                    str(condition_last_node)+ "\n")

            # But update to last identifier if last child node of condition
            # is not the condition node itself
            if condition_last_node != condition_node:
                if self.debug:
                    sys.stdout.write("Getting Stmt - While - "
                        "Condition last child is different from condition.\n")

                rel_exp_value = condition_last_node.identifier
                #condition_last_node.add_child(while_loop_start_label_node)
                while_loop_start_label_node.add_child(condition_node)
                #new_stmt_node = condition_node
                new_stmt_node = while_loop_start_label_node

            else:
                new_stmt_node = while_loop_start_label_node

            if_true_goto_node = IfGoTo3Node(
                rel_exp=rel_exp_value,
                goto=while_loop_expression_start_label_node.label_id
            )

            while_expression_node = self._get_stmt(
                symbol_table,
                ast_node.while_expression
            )
            if self.debug:
                sys.stdout.write("Getting Stmt - While loop - "
                    "While expression found:" + \
                    str(while_expression_node) +"\n")

            false_goto_node = GoTo3Node(
                goto=while_loop_exit_label_node.label_id
            )

            #while_loop_start_label_node.add_child(if_true_goto_node)
            condition_last_node.add_child(if_true_goto_node)
            if_true_goto_node.add_child(false_goto_node)
            false_goto_node.add_child(while_loop_expression_start_label_node)

            goto_while_start_node = GoTo3Node(
                goto=while_loop_start_label_node.label_id
            )

            while_loop_expression_start_label_node.add_child(while_expression_node)
            while_expression_last_node = self._get_last_child(while_expression_node)
            while_expression_last_node.add_child(goto_while_start_node)

            goto_while_start_node.add_child(while_loop_exit_label_node)

            # Remove symbol table for while loop
            symbol_table.pop_st()

        elif isinstance(ast_node, ReturnNode):

            if self.debug:
                sys.stdout.write("Getting Stmt - Return detected.\n")

            if ast_node.return_value:

                if self.debug:
                    sys.stdout.write("Getting Stmt - Return value type: " + \
                        str(type(ast_node.return_value)) + " with value: " + \
                        str(ast_node.return_value.value) +  "\n")
                    sys.stdout.write("Getting Stmt - Return value node detected.\n")

                if ast_node.return_value.is_identifier and \
                    type(ast_node.return_value.type) != FunctionType:
                    # Set return value as variable name directly if return value
                    # is an <id> as defined in JLITE

                    return_node = Return3Node(return_value=ast_node.return_value.value)
                    new_stmt_node = return_node

                    if self.debug:
                        sys.stdout.write("Getting Stmt - Return exp identifier found: " + \
                            str(ast_node.return_value) + " with value: " + \
                            str(ast_node.return_value.value) + " and type " + \
                            str(ast_node.return_value.type) + "\n")

                else:
                    return_exp = self._get_exp3(symbol_table, ast_node.return_value)

                    if self.debug:
                        sys.stdout.write("Getting Stmt - Return Exp found - " + \
                        "first node: " + str(type(return_exp)) + " with value " + \
                        str(return_exp.value) + ".\n")

                    return_exp_last_node = self._get_last_child(return_exp)
                    return_node = Return3Node(return_value=ast_node.value)

                    if return_exp != return_exp_last_node:

                        if self.debug:
                            sys.stdout.write("Getting Stmt - Last return node is different: " + \
                            str(type(return_exp_last_node)) + \
                            "\n")

                            if type(return_exp_last_node) == MethodCall3Node:
                                sys.stdout.write("Getting Stmt - Last return node is different: " + \
                                str(type(return_exp_last_node)) + " with method_id " + \
                                str(return_exp_last_node.method_id) + "\n")

                        return_node = Return3Node(return_value=return_exp_last_node.identifier)
                        return_exp_last_node.add_child(return_node)
                        new_stmt_node = return_exp

                    elif type(return_exp) == ClassAttribute3Node:
                        # Manually generate label

                        # Create new temporary variable

                        temp_var = "_t"+str(self._get_temp_var_count())
                        temp_var_node = VarDecl3Node(
                            value=temp_var,
                            type=return_exp.type
                        )

                        symbol_table.insert(temp_var, return_exp.type)

                        # Assign value to temporary variable

                        temp_var_assignment_node = Assignment3Node(type=return_exp.type)
                        temp_var_assignment_node.set_identifier(temp_var)
                        temp_var_assignment_node.set_assigned_value(return_exp)
                        temp_var_node.add_child(temp_var_assignment_node)

                        return_node = Return3Node(return_value=temp_var)
                        temp_var_assignment_node.add_child(return_node)
                        new_stmt_node = temp_var_node

                    else:

                        return_exp.add_child(return_node)
                        new_stmt_node = return_exp

            else:
                if self.debug:
                    sys.stdout.write("Getting Stmt - No return value detected.\n")

                new_stmt_node = Return3Node()

        if ast_node.sibling:
            new_stmt_node = self._get_stmt(
                symbol_table,
                ast_node.sibling,
                new_stmt_node
            )

        if stmt_node:
            stmt_last_node = self._get_last_child(stmt_node)
            stmt_last_node.add_child(new_stmt_node)

        else:
            stmt_node = new_stmt_node

        return stmt_node

    '''
    def _get_rel_exp3(
        self,
        ast_node: Any
    ) -> Union[IR3Node, RelOp3Node]:

        if self.debug:
            sys.stdout.write("Getting RelExp - Initiated.\n")
            sys.stdout.write("Getting RelExp - ASTNode: " + str(ast_node) + "\n")

        if isinstance(ast_node, RelOpNode):

            if self.debug:
                sys.stdout.write("Getting RelExp - RelOp detected.\n")

            return RelOp3Node(
                type=ast_node.type,
                left_operand=ast_node.left_operand.value,
                right_operand=ast_node.right_operand.value,
                operator=ast_node.value,
                left_operand_is_raw_value=ast_node.left_operand.is_raw_value,
                right_operand_is_raw_value=ast_node.right_operand.is_raw_value
            )

        else:
            return IR3Node(value=ast_node.value, type=ast_node.type)
        '''

    def _check_complex_operand_in_binop(
        self,
        ir3_node: Any,
        parent_ir3_node: Optional[Any],
        return_top_node: Optional[bool]=False,
    ) -> Any:

        if type(ir3_node) in [ClassAttribute3Node, MethodCall3Node]:
            temp_var_count = self._get_temp_var_count()
            temp_var = "_t"+str(temp_var_count)

            temp_var_node = VarDecl3Node(
                value=temp_var,
                type=ir3_node.type
            )

            temp_var_assignment_node = Assignment3Node(
                type=ir3_node.type
            )
            temp_var_assignment_node.set_identifier(temp_var)
            temp_var_assignment_node.set_assigned_value(ir3_node)

            temp_var_node.add_child(temp_var_assignment_node)

            if parent_ir3_node:
                parent_ir3_node.add_child(temp_var_node)
            '''
            ir3_node.add_child(temp_var_node)
            ir3_node = temp_var_assignment_node
            '''

            if return_top_node:
                return temp_var_node

            else:
                return temp_var_assignment_node

        return ir3_node

    def _get_exp3(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any
    ) -> Any:

        if self.debug:
            sys.stdout.write("Getting Exp - Initiated.\n")
            sys.stdout.write("Getting Exp - ASTNode: " + str(ast_node) + "\n")

        if isinstance(ast_node, NegationNode) or \
            isinstance(ast_node, ComplementNode):
            # <Uop3><idc3>
            if self.debug:
                sys.stdout.write("Getting Exp - "
                    "NegationNode or ComplementNode detected.\n")

            if isinstance(ast_node, NegationNode):

                negated_exp_node = self._get_exp3(
                    symbol_table,
                    ast_node.negated_expression
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - NegationNode - "
                        "Negated expression node created: " + \
                        str(negated_exp_node) + "\n")

                negated_exp_last_node = self._get_last_child(negated_exp_node)

                negated_exp_last_child_id = negated_exp_node.value
                if negated_exp_last_node != negated_exp_node:
                    negated_exp_last_child_id = negated_exp_last_node.identifier

                # Create new temporary variable

                temp_var = "_t"+str(self._get_temp_var_count())
                temp_var_node = VarDecl3Node(
                    value=temp_var,
                    type=BasicType.INT
                )

                symbol_table.insert(temp_var, BasicType.INT)

                # Assign value to temporary variable

                temp_var_assignment_node = Assignment3Node(
                    type=BasicType.INT
                )
                temp_var_assignment_node.set_identifier(temp_var)

                negation_node = UnaryOp3Node(
                    operator='-',
                    operand=negated_exp_last_child_id,
                    type=BasicType.INT
                )
                temp_var_assignment_node.set_assigned_value(negation_node)

                if negated_exp_last_node != negated_exp_node:
                    negated_exp_last_node.add_child(temp_var_node)
                    temp_var_node.add_child(temp_var_assignment_node)
                    new_exp_node = negated_exp_node
                else:
                    temp_var_node.add_child(temp_var_assignment_node)
                    new_exp_node = temp_var_node

                return new_exp_node

            elif isinstance(ast_node, ComplementNode):

                complement_exp_node = self._get_exp3(
                    symbol_table,
                    ast_node.complement_expression
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - ComplementNode - "
                        "Complement expression node created: " + \
                        str(complement_exp_node) + "\n")

                complement_exp_last_node = self._get_last_child(complement_exp_node)

                complement_exp_last_child_id = complement_exp_node.value
                if complement_exp_last_node != complement_exp_node:
                    complement_exp_last_child_id = complement_exp_last_node.identifier

                # Create new temporary variable

                temp_var = "_t"+str(self._get_temp_var_count())
                temp_var_node = VarDecl3Node(value=temp_var, type=BasicType.BOOL)

                symbol_table.insert(temp_var, BasicType.BOOL)

                # Assign value to temporary variable

                temp_var_assignment_node = Assignment3Node(type=BasicType.BOOL)
                temp_var_assignment_node.set_identifier(temp_var)

                complement_node = UnaryOp3Node(
                    type=BasicType.BOOL,
                    operator='!',
                    operand=complement_exp_last_child_id
                )
                temp_var_assignment_node.set_assigned_value(complement_node)

                if complement_exp_last_node != complement_exp_node:
                    complement_exp_last_node.add_child(temp_var_node)
                    temp_var_node.add_child(temp_var_assignment_node)
                    new_exp_node = complement_exp_node
                else:
                    temp_var_node.add_child(temp_var_assignment_node)
                    new_exp_node = temp_var_node

                return new_exp_node

        elif isinstance(ast_node, RelOpNode):

            if self.debug:
                sys.stdout.write("Getting Exp - RelOpNode detected.\n")

            left_operand_node = self._get_exp3(
                symbol_table,
                ast_node.left_operand
            )
            right_operand_node = self._get_exp3(
                symbol_table,
                ast_node.right_operand
            )

            if self.debug:
                sys.stdout.write("Getting Exp - RelOpNode - Right operand expression: " + \
                    str(type(right_operand_node)) + "\n")

            temp_var = "_t"+str(self._get_temp_var_count())
            temp_var_node = VarDecl3Node(value=temp_var, type=BasicType.BOOL)

            symbol_table.insert(temp_var, BasicType.BOOL)

            if type(ast_node.left_operand) == ASTNode and \
                not ast_node.left_operand.is_identifier and \
                type(ast_node.right_operand) == ASTNode and \
                not ast_node.right_operand.is_identifier:

                # Short circuit if it is a binary operation and both operands
                # are constants

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "Two int constants rel op short circuit.\n")

                computed_value = self._compute_relop_node_with_constants(ast_node)

                # Assign value to temporary variable

                temp_var_assignment_node = Assignment3Node(type=ast_node.type)
                temp_var_assignment_node.set_identifier(temp_var)
                temp_var_assignment_node.set_assigned_value(
                    computed_value,
                    assigned_value_is_raw_value=True
                )

                temp_var_node.add_child(temp_var_assignment_node)
                new_exp_node = temp_var_node
                return new_exp_node

            # Assign value to temporary variable

            temp_var_assignment_node = Assignment3Node(type=BasicType.BOOL)
            temp_var_assignment_node.set_identifier(temp_var)

            left_operand_last_node = self._get_last_child(left_operand_node)
            right_operand_last_node = self._get_last_child(right_operand_node)

            left_operand_last_child_id = left_operand_node.value
            if left_operand_last_node != left_operand_node:
                left_operand_last_child_id = left_operand_last_node.identifier

            right_operand_last_child_id = right_operand_node.value
            if right_operand_last_node != right_operand_node:
                right_operand_last_child_id = right_operand_last_node.identifier


            relop_node = RelOp3Node(
                type=BasicType.BOOL,
                left_operand=left_operand_last_child_id,
                right_operand=right_operand_last_child_id,
                operator=ast_node.value,
                left_operand_is_raw_value=ast_node.left_operand.is_raw_value,
                right_operand_is_raw_value=ast_node.right_operand.is_raw_value
            )

            temp_var_assignment_node.set_assigned_value(relop_node)

            if left_operand_last_node == left_operand_node and \
                right_operand_last_node == right_operand_node:
                new_exp_node = temp_var_node

            elif left_operand_last_node == left_operand_node:
                new_exp_node = right_operand_node
                right_operand_last_node.add_child(temp_var_node)

            elif right_operand_last_node == right_operand_node:
                left_operand_last_node.add_child(temp_var_node)
                new_exp_node = left_operand_node

            else:
                left_operand_last_node.add_child(right_operand_node)
                right_operand_last_node.add_child(temp_var_node)
                new_exp_node = left_operand_node

            temp_var_node.add_child(temp_var_assignment_node)

            return new_exp_node

        elif isinstance(ast_node, InstanceNode):

            if self.debug:
                sys.stdout.write("Getting Exp - InstanceNode detected.\n")
                sys.stdout.write("Getting Exp - InstanceNode - Atom: " + \
                    ast_node.atom.value + "\n")
                sys.stdout.write("Getting Exp - InstanceNode - Identifier: " + \
                    ast_node.identifier.value + "\n")

            atom_value = ast_node.atom.value
            atom_type = ast_node.atom.type

            if type(ast_node.atom) == InstanceNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - InstanceNode - nested InstanceNode detected.\n")

                expression_node = self._get_exp3(
                    symbol_table,
                    ast_node.atom
                )

                last_of_expression = self._get_last_child(expression_node)

                last_of_expression, parent_of_last_of_expression = self._get_last_child(
                    expression_node,
                    return_last_parent=True
                )

                if type(last_of_expression) == ClassAttribute3Node:

                    if last_of_expression and \
                        parent_of_last_of_expression and \
                        last_of_expression != parent_of_last_of_expression:

                        if self.debug:
                            sys.stdout.write("Getting Exp - InstanceNode - nested" + \
                                " - unique last expression is ClassAttribute3Node.\n")
                            sys.stdout.write("Getting Exp - InstanceNode - nested" + \
                                " - Type of last expression ClassAttribute3Node: " + \
                                str(last_of_expression.type) + "\n")


                        # Define new temp variable for class attribute node
                        temp_var = "_t"+str(self._get_temp_var_count())
                        temp_var_node = VarDecl3Node(
                            value=temp_var,
                            type=last_of_expression.type
                        )

                        symbol_table.insert(temp_var, last_of_expression.type)

                        # Assign value to temporary variable

                        temp_var_assignment_node = Assignment3Node(type=last_of_expression.type)
                        temp_var_assignment_node.set_identifier(temp_var)
                        temp_var_assignment_node.set_assigned_value(last_of_expression)
                        temp_var_node.add_child(temp_var_assignment_node)

                        parent_of_last_of_expression.add_child(temp_var_node)
                        last_of_expression = temp_var_assignment_node

                        atom_value = temp_var_assignment_node.identifier
                        atom_type = temp_var_assignment_node.type

                    else:

                        if self.debug:
                            sys.stdout.write("Getting Exp - InstanceNode - nested" + \
                                " - single ClassAttribute3Node.\n")

                        # Create new temporary variable

                        temp_var_nested = "_t"+str(self._get_temp_var_count())
                        temp_var_nested_node = VarDecl3Node(
                            value=temp_var_nested,
                            type=ast_node.atom.type
                        )

                        symbol_table.insert(temp_var_nested, ast_node.atom.type)

                        # Assign value to temporary variable

                        temp_var_nested_assignment_node = Assignment3Node(type=ast_node.atom.type)
                        temp_var_nested_assignment_node.set_identifier(temp_var_nested_node)
                        temp_var_nested_assignment_node.set_assigned_value(last_of_expression)
                        temp_var_nested_node.add_child(temp_var_nested_assignment_node)

                        new_exp_node = temp_var_nested_node

                        atom_value = last_of_expression
                        atom_type = last_of_expression.type

                else:

                    atom_value = last_of_expression.identifier
                    atom_type = last_of_expression.type

            if isinstance(ast_node.child, ExpListNode) or \
                isinstance(ast_node.identifier.child, ExpListNode):
                # <id3>(<VList3>)
                if self.debug:
                    sys.stdout.write("Getting Exp - Method call detected.\n")


                exp_list_node = ast_node.child
                if ast_node.identifier.child:

                    if isinstance(ast_node.identifier.child, ExpListNode):
                        exp_list_node = ast_node.identifier.child

                st_lookup: Any = symbol_table.lookup(ast_node.identifier.value)
                if st_lookup:
                    if self.debug:
                        sys.stdout.write("Getting Exp - Symbol table result - " + \
                            str(st_lookup) + "\n")

                    if type(st_lookup) == list:

                        args_type = exp_list_node.get_arguments_type()

                        if self.debug:
                            sys.stdout.write("Getting Exp - Arguments of ExpListNode - " + \
                                str(args_type) + "\n")

                        for st_result in st_lookup:

                            if self.debug:
                                sys.stdout.write("Getting Exp - Symbol table multiple results - " + \
                                    str(st_result) + "\n")
                                sys.stdout.write(str(args_type) + "\n")
                                sys.stdout.write(str(st_result['type'].basic_type_list) + "\n")

                            if st_result['type'].basic_type_list == args_type:
                                temp_md_id = st_result['temp_id']

                                sys.stdout.write("Getting Exp - Overloaded method found.\n")
                    else:
                        temp_md_id = st_lookup['temp_id']
                else:
                    temp_md_id = st_lookup['temp_id']

                if self.debug:
                    if temp_md_id:
                        sys.stdout.write("Getting Exp - "
                            "Temp method identifier found: " + \
                            str(temp_md_id) + "\n")
                        sys.stdout.write("Getting Exp - Identifier value: " + \
                            str(ast_node.identifier.type) + "\n")
                        sys.stdout.write("Getting Exp - Return type of method: " + \
                            str(st_lookup['type'].return_type) + "\n")

                md_call_node = MethodCall3Node(
                    method_id=temp_md_id,
                    return_type=st_lookup['type']
                )

                class_instance_node = IR3Node(
                    value=atom_value,
                    type=atom_type
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - Method call detected - Class Instance value: " + \
                        str(atom_value) + " of type: " + \
                        str(atom_type) + "\n")

                prior_instructions = None
                if exp_list_node.expression:
                    args, prior_instructions = self._get_vlist(
                        symbol_table,
                        exp_list_node.expression
                    )

                    if self.debug:
                        sys.stdout.write("Getting Exp - InstanceNode - Method call detected - first arg: " + \
                            str(args.value) + " of type " + str(args.type) + "\n")

                        if prior_instructions:
                            sys.stdout.write("Getting Exp - Method call detected - Prior instructions retrieved.\n")

                        else:
                            sys.stdout.write("Getting Exp - Method call detected - No prior instructions.\n")

                    class_instance_node.add_child(args)

                if self.debug:

                    sys.stdout.write("Getting Exp - First argument node: " + \
                        str(type(class_instance_node)) + "\n")
                    sys.stdout.write("Getting Exp - First argument value: " + \
                        str(class_instance_node.value)+ "\n")

                md_call_node.set_arguments(class_instance_node)

                # Set method call to temporary variable

                temp_var = "_t"+str(self._get_temp_var_count())
                temp_var_node = VarDecl3Node(
                    value=temp_var,
                    type=st_lookup['type'].return_type
                )

                symbol_table.insert(temp_var, st_lookup['type'].return_type)
                temp_var_assignment_node = Assignment3Node(
                    type=st_lookup['type'].return_type
                )
                temp_var_assignment_node.set_identifier(temp_var)
                temp_var_assignment_node.set_assigned_value(
                    md_call_node,
                    assigned_value_is_raw_value=False
                )

                temp_var_node.add_child(temp_var_assignment_node)

                try:

                    temp_var_nested_node.add_child(temp_var_node)
                    new_exp_node = temp_var_nested_node

                except:

                    new_exp_node = temp_var_node

                if prior_instructions:

                    # Link prior instructions with temporary variable declaration
                    # for method call
                    prior_instructions_last = self._get_last_child(prior_instructions)
                    try:

                        prior_instructions_last.add_child(temp_var_nested_node)

                    except:

                        prior_instructions_last.add_child(temp_var_node)

                    new_exp_node = prior_instructions

            else:
                # <id3>.<id3>
                if self.debug:
                    sys.stdout.write("Getting Exp - Class attribute detected.\n")
                    sys.stdout.write("Getting Exp - Class attribute AST value: " + \
                        str(ast_node.value) + "\n")
                    sys.stdout.write("Getting Exp - Class attribute AST type: " + \
                        str(ast_node.type) + "\n")

                new_exp_node = ClassAttribute3Node(
                    type=ast_node.type,
                    object_name=atom_value,
                    target_attribute=ast_node.identifier.value,
                    class_name=ast_node.class_name
                )

                try:

                    temp_var_nested_node.add_child(new_exp_node)
                    new_exp_node = temp_var_nested_node

                except:

                    pass

                if self.debug:
                    sys.stdout.write("Getting Exp - Class identifier: " + \
                        str(atom_value) + "\n")
                    sys.stdout.write("Getting Exp - Class attribute: " + \
                        str(ast_node.identifier.value) + "\n")

            if type(ast_node.atom) == InstanceNode:

                last_of_expression.add_child(new_exp_node)
                new_exp_node = expression_node

        elif isinstance(ast_node, ClassInstanceNode):
            # new <cname>()
            if self.debug:
                sys.stdout.write("Getting Exp - ClassInstance node detected.\n")

            new_exp_node = ClassInstance3Node(
                target_class=ast_node.target_class.value
            )


        elif isinstance(ast_node, BinOpNode) or \
            isinstance(ast_node, ArithmeticOpNode):
            # <idc3> <Bop3> <idc3>

            if self.debug:
                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp node detected.\n")
                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp left operand: " + \
                    str(ast_node.left_operand) + "\n")
                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp left operand: " + \
                    str(ast_node.left_operand.value) + "\n")

                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp operator: " + \
                    str(ast_node.value) + "\n")

                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp right operand: " + \
                    str(ast_node.right_operand) + "\n")
                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp right operand: " + \
                    str(ast_node.right_operand.value) + "\n")

            # Declare temporary variable

            temp_var_count = self._get_temp_var_count()
            temp_var = "_t"+str(temp_var_count)
            temp_var_node = VarDecl3Node(value=temp_var, type=ast_node.type)

            symbol_table.insert(temp_var, ast_node.type)

            if isinstance(ast_node, ArithmeticOpNode) and \
                type(ast_node.left_operand) == ASTNode and \
                not ast_node.left_operand.is_identifier and \
                type(ast_node.right_operand) == ASTNode and \
                not ast_node.right_operand.is_identifier:

                # Short circuit if it is an arithmetic operation and both operands
                # are constants

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "Two constants short circuit.\n")

                computed_value = self._compute_arithmetic_node_with_constants(ast_node)

                # Assign value to temporary variable

                temp_var_assignment_node = Assignment3Node(type=ast_node.type)
                temp_var_assignment_node.set_identifier(temp_var)
                temp_var_assignment_node.set_assigned_value(
                    computed_value,
                    assigned_value_is_raw_value=True
                )

                temp_var_node.add_child(temp_var_assignment_node)
                new_exp_node = temp_var_node
                return new_exp_node

            if isinstance(ast_node, BinOpNode) and \
                type(ast_node.left_operand) == ASTNode and \
                not ast_node.left_operand.is_identifier and \
                type(ast_node.right_operand) == ASTNode and \
                not ast_node.right_operand.is_identifier:

                # Short circuit if it is a binary operation and both operands
                # are constants

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "Two boolean constants short circuit.\n")

                computed_value = self._compute_binop_node_with_constants(ast_node)

                # Assign value to temporary variable

                temp_var_assignment_node = Assignment3Node(type=ast_node.type)
                temp_var_assignment_node.set_identifier(temp_var)
                temp_var_assignment_node.set_assigned_value(
                    computed_value,
                    assigned_value_is_raw_value=True
                )

                temp_var_node.add_child(temp_var_assignment_node)
                new_exp_node = temp_var_node
                return new_exp_node

            if type(ast_node.left_operand) == ASTNode and \
                type(ast_node.right_operand) == ASTNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: creating nodes for simple operations on both operands\n")


                new_binop_node = BinOp3Node(
                    type=ast_node.type,
                    left_operand=ast_node.left_operand.value,
                    right_operand=ast_node.right_operand.value,
                    operator=ast_node.value,
                    left_operand_is_raw_value=ast_node.left_operand.is_raw_value,
                    right_operand_is_raw_value=ast_node.right_operand.is_raw_value
                )

            elif type(ast_node.left_operand) == ASTNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: creating nodes for complex operation on right only\n")

                right_operand_node = self._get_exp3(
                    symbol_table,
                    ast_node.right_operand
                )

                right_operand_last_node, right_operand_last_parent_node = self._get_last_child(
                    right_operand_node,
                    return_last_parent=True
                )

                if self.debug:
                    sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                        "Right operand first node: " + str(type(right_operand_node)) + \
                        " with value " + str(right_operand_node.value) + "\n")
                    sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                        "Right operand last node: " + str(type(right_operand_last_node)) + \
                        " with value " + str(right_operand_last_node.value) + "\n")

                if type(right_operand_last_node) == ClassAttribute3Node:
                    new_right_operand_node = self._check_complex_operand_in_binop(
                        right_operand_last_node,
                        parent_ir3_node=right_operand_last_parent_node,
                        return_top_node=True
                    )

                    if right_operand_last_node != new_right_operand_node:
                        right_operand_last_node, right_operand_last_parent_node = self._get_last_child(
                            new_right_operand_node,
                            return_last_parent=True
                        )
                        right_operand_node = new_right_operand_node

                    if self.debug:
                        sys.stdout.write("Test print after checking complex operand: \n\n")
                        right_operand_node.pretty_print()
                        sys.stdout.write("\n")
                        sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                            "new left operand last node is: " + \
                            str(type(right_operand_last_node)) + " with identifier " + \
                            str(right_operand_last_node.identifier) + "\n")

                new_binop_node = BinOp3Node(
                    type=ast_node.type,
                    left_operand=ast_node.left_operand.value,
                    right_operand=right_operand_last_node.identifier,
                    operator=ast_node.value,
                    left_operand_is_raw_value=ast_node.left_operand.is_raw_value,
                    right_operand_is_raw_value=ast_node.right_operand.is_raw_value
                )

            elif type(ast_node.right_operand) == ASTNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: creating nodes for complex operation on left only\n")


                left_operand_node = self._get_exp3(
                    symbol_table,
                    ast_node.left_operand
                )

                if self.debug:
                    sys.stdout.write("Test print before checking complex operand: \n\n")
                    left_operand_node.pretty_print()
                    sys.stdout.write("\n")

                left_operand_last_node, left_operand_last_parent_node = self._get_last_child(
                    left_operand_node,
                    return_last_parent=True
                )

                if self.debug:
                    sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                        "Left operand first node: " + str(type(left_operand_node)) + \
                        " with value " + str(left_operand_node.value) + "\n")
                    sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                        "Left operand last node: " + str(type(left_operand_last_node)) + \
                        " with value " + str(left_operand_last_node.value) + "\n")

                if type(left_operand_last_node) == ClassAttribute3Node:
                    new_left_operand_node = self._check_complex_operand_in_binop(
                        left_operand_last_node,
                        parent_ir3_node=left_operand_last_parent_node,
                        return_top_node=True
                    )

                    if left_operand_node != new_left_operand_node:
                        left_operand_last_node, left_operand_last_parent_node = self._get_last_child(
                            new_left_operand_node,
                            return_last_parent=True
                        )
                        left_operand_node = new_left_operand_node

                    if self.debug:
                        sys.stdout.write("Test print after checking complex operand: \n\n")
                        left_operand_node.pretty_print()
                        sys.stdout.write("\n")
                        sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                            "new left operand last node is: " + \
                            str(type(left_operand_last_node)) + " with identifier " + \
                            str(left_operand_last_node.identifier) + "\n")


                new_binop_node = BinOp3Node(
                    type=ast_node.type,
                    left_operand=left_operand_last_node.identifier,
                    right_operand=ast_node.right_operand.value,
                    operator=ast_node.value,
                    left_operand_is_raw_value=ast_node.left_operand.is_raw_value,
                    right_operand_is_raw_value=ast_node.right_operand.is_raw_value
                )

            else:

            # Get left and right operands

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: creating nodes for complex operations on both operands\n")

                left_operand_node = self._get_exp3(
                    symbol_table,
                    ast_node.left_operand
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - BinOp/ArithmeticOp left operand: " + \
                        str(left_operand_node) + "\n")

                # Get last node of left operand
                left_operand_last_node, left_operand_last_parent_node = self._get_last_child(
                    left_operand_node,
                    return_last_parent=True
                )

                if type(left_operand_last_node) == ClassAttribute3Node:
                    new_left_operand_node = self._check_complex_operand_in_binop(
                        left_operand_last_node,
                        parent_ir3_node=left_operand_last_parent_node,
                        return_top_node=True
                    )

                    if left_operand_node != new_left_operand_node:
                        left_operand_last_node, left_operand_last_parent_node = self._get_last_child(
                            new_left_operand_node,
                            return_last_parent=True
                        )
                        left_operand_node = new_left_operand_node

                    if self.debug:
                        sys.stdout.write("Test print after checking complex operand: \n\n")
                        left_operand_node.pretty_print()
                        sys.stdout.write("\n")
                        sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                            "new left operand last node is: " + \
                            str(type(left_operand_last_node)) + " with identifier " + \
                            str(left_operand_last_node.identifier) + "\n")

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp node [Last child of left operand]: " + \
                        str(left_operand_last_node) + "\n")

                right_operand_node = self._get_exp3(
                    symbol_table,
                    ast_node.right_operand
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - Complex BinOp/ArithmeticOp right operand: " + \
                        str(type(right_operand_node)) + "\n")

                # Get last node of right operand
                right_operand_last_node, right_operand_last_parent_node = self._get_last_child(
                    right_operand_node,
                    return_last_parent=True
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - BinOp/ArithmeticOp right operand last node: " + \
                        str(type(right_operand_last_node)) + "\n")

                if type(right_operand_last_node) == ClassAttribute3Node:
                    new_right_operand_node = self._check_complex_operand_in_binop(
                        right_operand_last_node,
                        parent_ir3_node=right_operand_last_parent_node,
                        return_top_node=True
                    )

                    if right_operand_last_node != new_right_operand_node:
                        right_operand_last_node, right_operand_last_parent_node = self._get_last_child(
                            new_right_operand_node,
                            return_last_parent=True
                        )
                        right_operand_node = new_right_operand_node

                    if self.debug:
                        sys.stdout.write("Test print after checking complex operand: \n\n")
                        right_operand_node.pretty_print()
                        sys.stdout.write("\n")
                        sys.stdout.write("Getting Exp- BinOp/ArithmeticOp - " + \
                            "new left operand last node is: " + \
                            str(type(right_operand_last_node)) + " with identifier " + \
                            str(right_operand_last_node.identifier) + "\n")

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp node [Last child of right operand]: " + \
                        str(left_operand_last_node) + "\n")

                new_binop_node = BinOp3Node(
                    type=ast_node.type,
                    left_operand=left_operand_last_node.identifier,
                    right_operand=right_operand_last_node.identifier,
                    operator=ast_node.value,
                    left_operand_is_raw_value=ast_node.left_operand.is_raw_value,
                    right_operand_is_raw_value=ast_node.right_operand.is_raw_value
                )

            # Assign value to temporary variable

            temp_var_assignment_node = Assignment3Node(type=ast_node.type)
            temp_var_assignment_node.set_identifier(temp_var)
            temp_var_assignment_node.set_assigned_value(new_binop_node)

            # Link nodes together
            if type(ast_node.left_operand) == ASTNode and \
                type(ast_node.right_operand) == ASTNode:

                new_exp_node = temp_var_node

            elif type(ast_node.left_operand) == ASTNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: linking nodes for complex operation on right only\n")

                new_exp_node = right_operand_node
                right_operand_last_node.add_child(temp_var_node)

            elif type(ast_node.right_operand) == ASTNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: linking nodes for complex operation on left only\n")

                new_exp_node = left_operand_node
                left_operand_last_node.add_child(temp_var_node)

            else:

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "BinOp/ArithmeticOp: linking nodes for complex operations\n")

                new_exp_node = left_operand_node
                left_operand_last_node.add_child(right_operand_node)
                right_operand_last_node.add_child(temp_var_node)

            temp_var_node.add_child(temp_var_assignment_node)

            if self.debug:
                sys.stdout.write("Getting Exp - BinOp/ArithmeticOp completed.\n")

        elif isinstance(ast_node, AssignmentNode):

            # <id3> = <Exp3>
            if self.debug:
                sys.stdout.write("Getting Exp - Assignment node detected.\n")

            assignment_node = Assignment3Node(type=ast_node.identifier.type)
            assignment_node.set_identifier(ast_node.identifier.value)
            # If assigned value is expression, get expression first, and assign at the end

            if type(ast_node.assigned_value) != ASTNode:

                if self.debug:
                    sys.stdout.write("Getting Exp - Assigned value is not ASTNode: " + \
                        str(type(ast_node.assigned_value)) + "\n")

                assigned_value_expression_node = self._get_exp3(
                    symbol_table,
                    ast_node.assigned_value
                )
                assigned_value_expression_last_child = self._get_last_child(
                    assigned_value_expression_node
                )

                assignment_node.set_assigned_value(
                    assigned_value_expression_last_child.identifier
                )

                assigned_value_expression_last_child.add_child(assignment_node)
                new_exp_node = assigned_value_expression_node

            # Otherwise, assign directly
            else:

                if self.debug:
                    sys.stdout.write("Getting Exp - Assigned value is ASTNode: " + \
                        str(type(ast_node.assigned_value.value)) + "\n")


                assignment_node.set_assigned_value(
                    ast_node.assigned_value.value,
                    assigned_value_is_raw_value=ast_node.assigned_value.is_raw_value
                )
                new_exp_node = assignment_node

            return new_exp_node

        else:

            if self.debug:
                sys.stdout.write("Getting Exp - "
                    "Checking for identifier and constant.\n")

            # <idc3>

            if ast_node.is_identifier:
                # <id3>
                if self.debug:
                    sys.stdout.write("Getting Exp - Identifier detected.\n")

                identifier = symbol_table.lookup(ast_node.value)

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "Checking if identifier is found in symbol table: " + \
                        str(identifier) + "\n")

                # Check for method name in symbol table
                st_lookup = symbol_table.lookup(ast_node.value)

                if st_lookup:
                    if self.debug:
                        sys.stdout.write("Getting Exp - Symbol table result - " + \
                            str(st_lookup) + "\n")

                if type(identifier['type']) == FunctionType:
                    if self.debug:
                        sys.stdout.write("Getting Exp - FunctionType detected.\n")
                        sys.stdout.write("Getting Exp - Method call detected.\n")
                        sys.stdout.write("Getting Exp - Type: " + str(ast_node.type) + "\n")

                    if st_lookup:

                        if type(st_lookup) == list:

                            args_type = ast_node.child.get_arguments_type()

                            if self.debug:
                                sys.stdout.write("Getting Exp - Arguments of ExpListNode - " + \
                                    str(args_type) + "\n")

                            for st_result in st_lookup:

                                if self.debug:
                                    sys.stdout.write("Getting Exp - Symbol table multiple results - " + \
                                        str(st_result) + "\n")
                                    sys.stdout.write(str(args_type) + "\n")
                                    sys.stdout.write(str(st_result['type'].basic_type_list) + "\n")

                                if st_result['type'].basic_type_list == args_type:
                                    temp_md_id = st_result['temp_id']

                                    sys.stdout.write("Getting Exp - Overloaded method found.\n")
                        else:
                            temp_md_id = st_lookup['temp_id']
                    else:
                        temp_md_id = st_lookup['temp_id']

                    md_call_node = MethodCall3Node(
                        method_id=temp_md_id,
                        return_type=identifier['type'].return_type
                    )

                    class_instance_node = IR3Node(
                        value="this",
                        type=identifier['type'].class_name
                    )

                    md_call_node.set_arguments(class_instance_node)

                    if self.debug:
                        sys.stdout.write("Getting Exp - Method call detected - Class Instance value: " + \
                            str(ast_node.value) + " of type: " + \
                            str(ast_node.type) + "\n")


                    prior_instructions = None
                    if ast_node.child.expression:
                        args, prior_instructions = self._get_vlist(
                            symbol_table,
                            ast_node.child.expression
                        )

                        if self.debug:
                            sys.stdout.write("Getting Exp - idc3 - Method call detected - first arg: " + \
                                str(args.value) + " of type " + str(args.type) + "\n")

                            if prior_instructions:
                                sys.stdout.write("Getting Exp - Method call detected - Prior instructions retrieved.\n")


                        class_instance_node.add_child(args)

                    temp_var_count = self._get_temp_var_count()
                    temp_var = "_t"+str(temp_var_count)

                    temp_var_node = VarDecl3Node(
                        value=temp_var,
                        type=identifier['type'].return_type
                    )

                    symbol_table.insert(
                        temp_var,
                        identifier['type'].return_type,
                        state=None
                    )

                    if self.debug:
                        sys.stdout.write("Getting Exp - "
                            "Inserting into symbol table: " + \
                            str(symbol_table) + "\n")

                    temp_var_assignment_node = Assignment3Node(
                        type=identifier['type'].return_type
                    )
                    temp_var_assignment_node.set_identifier(temp_var)

                    temp_var_assignment_node.set_assigned_value(
                        md_call_node,
                        assigned_value_is_raw_value=False
                    )

                    temp_var_node.add_child(temp_var_assignment_node)

                    new_exp_node = temp_var_node
                    if prior_instructions:
                        prior_instructions_last = self._get_last_child(prior_instructions)
                        prior_instructions_last.add_child(temp_var_node)
                        new_exp_node = prior_instructions

                else:

                    if self.debug:
                        sys.stdout.write("Getting Exp - Returning raw node: " + \
                            str(ast_node.value) + "\n")
                        sys.stdout.write("Is identifier: " + str(ast_node.is_identifier) + "\n")

                    return IR3Node(value=ast_node.value, type=ast_node.type)

            else:
                # <Const>
                if self.debug:
                    sys.stdout.write("Getting Exp - Constant detected.\n")
                    sys.stdout.write("Getting Exp - Type of constant: " + \
                        str(ast_node.type) + "\n")
                    sys.stdout.write("Getting Exp - Value of constant: " + \
                        str(ast_node.value) + "\n")
                    sys.stdout.write("Getting Exp - Type of node: " + \
                        str(type(ast_node)) + "\n")

                temp_var_count = self._get_temp_var_count()
                temp_var = "_t"+str(temp_var_count)

                temp_var_node = VarDecl3Node(
                    value=temp_var,
                    type=ast_node.type
                )
                symbol_table.insert(
                    temp_var,
                    ast_node.type,
                    state=ast_node.value
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - "
                        "Inserting into symbol table: " + \
                        str(symbol_table) + "\n")

                temp_var_assignment_node = Assignment3Node(
                    type=ast_node.type
                )
                temp_var_assignment_node.set_identifier(temp_var)

                assigned_value_node = IR3Node(
                    value=ast_node.value,
                    type=ast_node.type
                )
                temp_var_assignment_node.set_assigned_value(
                    assigned_value_node,
                    assigned_value_is_raw_value=ast_node.is_raw_value
                )

                if self.debug:
                    sys.stdout.write("Getting Exp - raw value found: " + \
                        str(ast_node.value) + "\n")

                temp_var_node.add_child(temp_var_assignment_node)
                if self.debug:
                    sys.stdout.write("Getting Exp - temp var node child: " + \
                        str(temp_var_node.child) + "\n")

                new_exp_node = temp_var_node
                return new_exp_node

        return new_exp_node

    def _get_vlist(
        self,
        symbol_table: SymbolTableStack,
        ast_node: Any,
        v_node: Optional[Any]=None,
        prior_instructions: Optional[Any]=None
    ) -> Optional[Any]:

        if self.debug:
            sys.stdout.write("Getting VList - Initiated.\n")
            sys.stdout.write("Getting VList - ASTNode: " + str(ast_node.value) + "\n")
            sys.stdout.write("Getting VList - ASTNode type: " + str(type(ast_node)) + "\n")

        if not ast_node.value:
            return v_node

        new_v_node: Any

        if type(ast_node) != ASTNode or \
            (type(ast_node) == ASTNode and type(ast_node.type) == FunctionType):

            if self.debug:
                sys.stdout.write("Getting VList - Complex node detected: " + \
                    str(type(ast_node)) + "\n")

            symbol_table_copy = copy.deepcopy(symbol_table)

            # Prepare prior instructions if it is a complex node e.g. method call

            new_prior_instructions = self._get_exp3(symbol_table_copy, ast_node)

            if new_prior_instructions:

                if self.debug:
                    sys.stdout.write("Getting VList - Complex node detected - Prior instructions generated: " + \
                        str(type(new_prior_instructions)) + "\n")

                new_prior_instructions_last = self._get_last_child(new_prior_instructions)

                if self.debug:
                    sys.stdout.write("Getting VList - Complex node detected - Prior instructions last child generated: " + \
                        str(type(new_prior_instructions_last)) + "\n")

                if new_prior_instructions_last == new_prior_instructions and \
                    type(new_prior_instructions_last) == MethodCall3Node:

                    if self.debug:
                        sys.stdout.write("Getting VList - Method call is last node of prior instructions.\n")


                    temp_var_count = self._get_temp_var_count()
                    temp_var = "_t"+str(temp_var_count)

                    temp_var_node = VarDecl3Node(
                        value=temp_var,
                        type=ast_node.type.return_type
                    )

                    symbol_table.insert(
                        temp_var,
                        ast_node.type.return_type,
                        state=None
                    )

                    if self.debug:
                        sys.stdout.write("Getting Exp - "
                            "Inserting into symbol table: " + \
                            str(symbol_table) + "\n")

                    temp_var_assignment_node = Assignment3Node(
                        type=ast_node.type.return_type
                    )
                    temp_var_assignment_node.set_identifier(temp_var)

                    temp_var_assignment_node.set_assigned_value(
                        new_prior_instructions_last,
                        assigned_value_is_raw_value=False
                    )

                    temp_var_node.add_child(temp_var_assignment_node)
                    if self.debug:
                        sys.stdout.write("Getting Exp - temp var node child: " + \
                            str(temp_var_node.child) + "\n")

                    new_prior_instructions = temp_var_node

                    new_v_node = IR3Node(
                        value=temp_var_assignment_node.identifier,
                        type=temp_var_assignment_node.type,
                        is_raw_value=False
                    )

                else:
                    new_v_node = IR3Node(
                        value=new_prior_instructions_last.identifier,
                        type=new_prior_instructions_last.type,
                        is_raw_value=False
                    )

            else:

                new_v_node = IR3Node(
                    value=ast_node.value,
                    type=ast_node.type,
                    is_raw_value=ast_node.is_raw_value
                )

            if prior_instructions and new_prior_instructions:
                prior_instructions_last = self._get_last_child(prior_instructions)
                prior_instructions_last.add_child(new_prior_instructions)

            elif new_prior_instructions:
                prior_instructions = new_prior_instructions

        else:

            new_v_node = IR3Node(
                value=ast_node.value,
                type=ast_node.type,
                is_raw_value=ast_node.is_raw_value
            )

        if ast_node.sibling:
            symbol_table_copy = copy.deepcopy(symbol_table)
            new_v_node, prior_instructions = self._get_vlist(
                symbol_table_copy,
                ast_node.sibling,
                new_v_node,
                prior_instructions
            )

        if v_node:
            v_node_last = self._get_last_child(v_node)
            v_node_last.add_child(new_v_node)

        else:
            v_node = new_v_node

        return v_node, prior_instructions

    def generate_ir3(self, f) -> None:
        """
        Lexes, parses and type checks the input file, then generates
        the IR3 tree.

        :param TextIO f: the input file
        """
        self._parse_content(f)
        self.ir3_tree = IR3Tree(self._generate_ir3())

    def pretty_print(self) -> None:
        """
        Prints the generated IR3Tree
        """
        self.ir3_tree.pretty_print()

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. "
            "Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        gen = IR3Generator(debug=True)
        gen.generate_ir3(f)
        gen.pretty_print()

if __name__ == "__main__":

    __main__()
