import sys

import copy
from collections import deque

from enum import Enum

from typing import (
    Deque,
    Dict,
    List,
    Optional,
    Any,
    Union,
    Tuple,
)

class TypeError(Exception):
    """
    Exception class for errors encountered while type checking.

    ...

    Attributes
    ----------
    expression: str
    message: str

    """
    def __init__(
        self,
        expression: str,
        additional_message: str=''
    ) -> None:
        self.expression = expression
        self.message = "Invalid type: "
        self.additional_message = additional_message

    def __str__(self) -> str:

        return f'{self.message} {self.expression}. {self.additional_message}'

class BasicType(Enum):

    INT = 'Int'
    BOOL = 'Bool'
    STRING = 'String'
    VOID = 'Void'
    OBJECT = 'Object'

    def __str__(self):
        return str(self.value)

class FunctionType():

    basic_type_list: List[Any]

    def __init__(self, basic_type_list: List[Any]) -> None:
        self.basic_type_list = basic_type_list


TYPE_CONVERSION_DICT: Dict[str, "BasicType"] = {
    'Int': BasicType.INT,
    'Bool': BasicType.BOOL,
    'String': BasicType.STRING,
    'Void': BasicType.VOID,
}


class ASTNode:
    """
    Node instance for a valid expression

    ...

    Attributes
    ----------
    value: str
    type: str
    child: Any
    sibling: Any

    Methods
    -------
    pretty_print():
        Print the current value of the node in syntax format, and its child and sibling recursively.
    add_child(node):
        Set a node as its child. Child is traversed before sibling.
    add_sibling(node):
        Set a node as its sibling. Sibling is traversed after child (and sub-childs).

    """

    value: str
    type: Any
    is_identifier: bool
    child: Any
    sibling: Any

    def __init__(
        self,
        value: str='',
        type: str='',
        is_identifier: bool=False,
        child: Optional[Any]=None,
        sibling: Optional[Any]=None
    ) -> None:
        self.value = value
        self.type = type
        self.is_identifier = is_identifier
        self.child = child
        self.sibling = sibling


    def add_child(self, node: Any) -> None:
        """
        Set a node as child

        :param Any node: Node to set as child
        """
        self.child = node

    def add_sibling(self, node: Any) -> None:
        """
        Set a node as sibling

        :param Any node: Node to set as sibling
        """
        self.sibling = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:
        """
        Helper function to print the node in syntax format recursively.

        :param str delimiter: String to be printed before the next child
        :param str preceding: Whitespace offset to be printed before the current value
        """
        if self.value:

            if self.type == "Int" and self.value[0] == '-':
                sys.stdout.write('(' + self.value + ')')
            else:
                sys.stdout.write(self.value)

        if self.child:
            sys.stdout.write(' ')
            self.child.pretty_print()


        sys.stdout.write(delimiter)
        if self.sibling:

            sys.stdout.write(preceding)
            self.sibling.pretty_print(delimiter, preceding)

    def _assign_declaration_type(
        self,
        env: Any,
        debug: bool=False,
        within_class: str=''
    ) -> None:

        #if debug:
        #    sys.stdout.write("ASTNode - Env received: " + str(env) + "\n")

        if self.type in ['Int', 'String', 'Bool']:
            self.type = TYPE_CONVERSION_DICT[self.type]

            if debug:
                sys.stdout.write("ASTNode - Basic type found for identifier while assigning declaration type: " + str(self.type) + "\n")

        else:

            if debug:
                sys.stdout.write("ASTNode - Env for object type checking: " + str(env) + "\n")

            env_checked = False
            found = False

            # Make a copy of class descriptors
            env_copy = copy.deepcopy(env[0])

            #if debug:
            #    sys.stdout.write("ASTNode - Class descriptor for object type checking: " + str(env_copy) + "\n")

            while not env_checked:

                if len(env_copy) == 0:
                    env_checked = True
                    break

                current_class = env_copy.pop()

                if self.type == current_class[0]:

                    # Check object is of object type
                    self.type = (BasicType.OBJECT, current_class[0])

                    if debug:
                        sys.stdout.write("ASTNode - Class type found for identifier while assigning declaration type: " + \
                        str(current_class[0]) + "\n")

                    env_checked = True
                    found = True
                    break

            if not found and self.value != 'null':
                raise TypeError(self.type, "Unknown type declared.")

    def _assign_identifier_type(
        self,
        env: Any,
        debug: bool=False,
        within_class: str=''
    ) -> None:

        env_checked = False
        found = False

        env_copy = copy.deepcopy(env)

        class_descriptor = env_copy[0]
        local_environment = env_copy[1]

        # Search local environment first
        if len(local_environment) > 0:
            for v in local_environment:
                if self.value == v[0]:
                    self.type = v[1]
                    env_checked = True
                    found = True

        # Seach class descriptors next
        while not env_checked:

            if len(class_descriptor) == 0:
                env_checked = True
                break

            current_class = class_descriptor.pop()

            if debug:
                sys.stdout.write("Assign identifier type - current class: " + str(current_class) + '\n')

            # Checks if class instance is being declared
            if self.value == current_class[0]:

                # Check for declaration of new class object

                self.type = (BasicType.OBJECT, current_class[0])

                if debug:
                    sys.stdout.write("Identifier found in current env without type. Assigning class type: " + \
                    str(current_class[0]) + "\n")

                env_checked = True
                found = True
                break

            # Checks if class method is being called
            elif current_class[0] == within_class and current_class[1][1]:

                for current_env in current_class[1][1]:

                    if debug:
                        sys.stdout.write("Current value: " + self.value + '\n')
                        sys.stdout.write("Checking for current env: " + str(current_env) + '\n')

                    if self.value == current_env[0]:
                        # Identifier is found in environment
                        if debug:
                            sys.stdout.write("Identifier found in current env.\n")

                        if self.type == '':

                            # If type of identifier is not assigned yet, assign accordingly

                            self.type = current_env[1]

                            if debug:
                                sys.stdout.write("Identifier found in current env without type. Assigning type: " + str(current_env[1]) + "\n")

                        elif self.type in ['Int', 'String', 'Bool']:

                            self.type = TYPE_CONVERSION_DICT[self.type]

                            if debug:
                                sys.stdout.write("Identifier found in current env with unprocessed type. Assigning type: " + str(current_env[1]) + "\n")

                        elif self.type != current_env[1]:

                            # If type of identifer is assigned, but does not match what
                            # was declared in the environment stack, throw an error.

                            if debug:
                                sys.stdout.write("Current type: " + self.type + '\n')

                            raise TypeError(self.value, 'Identifier is of the wrong type')

                        # Terminate while loop
                        env_checked = True
                        found = True

                        # Break out of for loop
                        break

        if not found:
            if self.type:
                raise TypeError(str(self.value), "Undeclared type of " + str(self.type))
            else:
                raise TypeError(str(self.value), "Undeclared variable")

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        '''
        # Type checking for Int
        if self.type == 'Int':
            try:
                temp = int(self.value)
            except:
                raise TypeError(self.value)

        # Type checking string to be of boolean type if 'true' or 'false'
        if self.value == 'true' or self.value == 'false':
            if self.type != 'Bool':
                raise TypeError(self.value)
        '''

        if debug:
            sys.stdout.write("Fallback to default ASTNode type checking for: " + self.value + '\n')
            sys.stdout.write("Type checking for: " + self.value + '\n')
            sys.stdout.write("Is identifier: " + str(self.is_identifier) + '\n')

        if self.is_identifier:

            if env:
                if debug:
                    sys.stdout.write("Environment found: " + str(env) + '\n')

                self._assign_identifier_type(env, debug, within_class)

                if debug:
                    sys.stdout.write("Type assigned for identifier [" + self.value + "]: " + str(self.type) + '\n')

        elif isinstance(self.type, str):
            if debug:
                sys.stdout.write("Type of non-identifier: " + str(self.type) + "\n")

            if self.value == 'null':
                # Ignore type check if value is null
                self.type = BasicType.VOID
            else:
                self.type = TYPE_CONVERSION_DICT[self.type]

            if debug:
                sys.stdout.write("Type of non-identifier assigned: " + str(type(self.type)) + "\n")

        if self.child:
            self.child.type_check(env, debug, within_class)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class)


class MainClassNode(ASTNode):

    class_name: str
    main_arguments: Any
    main_variable_declarations: Any
    main_statements: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value = 'class'
        self.type = 'mainClass'

    def set_class_name(self, class_name: str) -> None:
        self.class_name = class_name

    def set_arguments(self, node: Any) -> None:
        self.main_arguments = node

    def set_variable_declarations(self, node: Any) -> None:
        self.main_variable_declarations = node

    def set_statements(self, node: Any) -> None:
        self.main_statements = node

    def _get_args(self) -> List[Any]:

        args: List[Any] = []
        args_processed = False
        current_arg = self.main_arguments

        if current_arg:
            while not args_processed:

                if not current_arg.child and not current_arg.sibling:
                    args_processed = True

                if current_arg.type:
                    if current_arg.type in ['Int', 'Bool', 'String']:
                        args.append((current_arg.value, TYPE_CONVERSION_DICT[current_arg.type]))
                    else:
                        args.append((current_arg.value, (BasicType.OBJECT, current_arg.type)))

                if current_arg.sibling:
                    current_arg = current_arg.sibling

        return args

    def initialise_class_descriptor(self) -> List[Any]:

        context: List[Any] = []

        args = self._get_args()

        method_signature = [(
            'main',
            FunctionType(args),
            BasicType.VOID
        )]

        context.append([self.class_name, [[], method_signature]])

        if self.sibling:
            class_descriptor = self.sibling.initialise_class_descriptor()
            context += class_descriptor

        return context

    def _check_class_declaration_names(self) -> None:

        class_names = [self.class_name]

        class_processed = False

        current_class = self.sibling

        if current_class:
            while not class_processed:

                if not current_class.sibling:
                    class_processed = True

                if current_class:
                    if current_class.class_name in class_names:
                        raise TypeError(current_class.class_name, "Class has the same name as an earlier declared class.")
                    else:
                        class_names.append(current_class.class_name)

                if current_class.sibling:
                    current_class = current_class.sibling

    def _initialise_main_mds(self) -> List[Tuple[str, "FunctionType", "BasicType"]]:

        local_environment = []

        args = self._get_args()

        local_environment.append((
            'main',
            FunctionType(args),
            BasicType.VOID
        ))

        return local_environment

    def _initialise_main_args(self) -> List[Tuple[str, Union["BasicType", Tuple["BasicType", str]]]]:

        local_environment = []

        args_completed = False

        current_args = self.main_arguments

        while not args_completed:

            local_environment.append((current_args.value, current_args.type))

            if not current_args.sibling:
                args_completed = True
                break

            current_args = current_args.sibling

        return local_environment

    def _initialise_main_vars(self) -> List[Tuple[str, Union["BasicType", Tuple["BasicType", str]]]]:

        local_environment = []

        vars_completed = False

        current_vars = self.main_variable_declarations

        while not vars_completed:

            local_environment.append((current_vars.value, current_vars.type))

            if not current_vars.sibling:
                vars_completed = True
                break

            current_vars = current_vars.sibling

        return local_environment

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        context = self.initialise_class_descriptor()

        class_descriptor_stack: Deque[Any] = deque()

        for c in context:
            class_descriptor_stack.append(c)

        local_environment_stack: Deque[Any] = deque()

        mdss = self._initialise_main_mds()
        if debug:
            sys.stdout.write("\nMainClassNode - Initialised local environment methods: " + str(mdss) + "\n")

        for mds in mdss:
            local_environment_stack.append(mds)

        env = [class_descriptor_stack, local_environment_stack]

        if debug:
            sys.stdout.write("MainClassNode - Printing environment stack: \n" + str(env) + '\n')

        self._check_class_declaration_names()

        if debug:
            sys.stdout.write("MainClassNode - No collision in class names.\n")

        if self.main_arguments:
            self.main_arguments.type_check(env, debug, self.class_name)

            local_environment = self._initialise_main_args()

            if debug:
                sys.stdout.write("MainClassNode - Initialised local environment args: " + str(local_environment) + "\n")

            for l in local_environment:
                env[1].append(l)

        if debug:
            sys.stdout.write("MainClassNode - Arguments type check completed.\n")

        if self.main_variable_declarations:
            self.main_variable_declarations.type_check(env, debug, self.class_name)

            local_environment = self._initialise_main_vars()

            if debug:
                sys.stdout.write("MainClassNode - Initialised local environment vars: " + str(local_environment) + "\n")

            for l in local_environment:
                env[1].append(l)

        self.main_statements.type_check(env, debug, self.class_name, BasicType.VOID)

        if self.child:
            self.child.type_check(env, debug, self.class_name)

        if self.sibling:
            env = [class_descriptor_stack, deque()]
            self.sibling.type_check(env, debug)


    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write("class " + self.class_name + "{ \n  Void main")

        sys.stdout.write('(')
        if self.main_arguments:
            self.main_arguments.pretty_print()

        sys.stdout.write(')')

        sys.stdout.write(preceding + '{\n')
        if self.main_variable_declarations:
            self.main_variable_declarations.pretty_print(delimiter=';\n', preceding='    ')

        sys.stdout.write('\n')
        self.main_statements.pretty_print(preceding='    ')

        if self.child:
            self.child.pretty_print(preceding='  ')

        sys.stdout.write('\n' + '  ' +'}')


        if self.child:
            self.child.pretty_print()

        sys.stdout.write("\n}\n")

        if self.sibling:
            self.sibling.pretty_print()

class ClassDeclNode(ASTNode):

    class_name: str
    variable_declarations: Any
    method_declarations: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_class_name(self, class_name: str) -> None:
        self.class_name = class_name

    def set_variable_declarations(self, node: Any) -> None:
        self.variable_declarations = node

    def set_method_declarations(self, node: Any) -> None:
        self.method_declarations = node

    def initialise_class_descriptor(self) -> List[Tuple[str, Tuple[List[Any], List[Any]]]]:

        var_decl: List[Any] = []
        var_decl_processed = False

        if self.variable_declarations:
            current_var_decl = self.variable_declarations

            while not var_decl_processed:

                if not current_var_decl.child and not current_var_decl.sibling:
                    var_decl_processed = True

                if current_var_decl:
                    if current_var_decl.type in ['Int', 'Bool', 'String']:
                        var_decl.append((current_var_decl.value, TYPE_CONVERSION_DICT[current_var_decl.type]))
                    else:
                        var_decl.append((current_var_decl.value, (BasicType.OBJECT, current_var_decl.type)))

                if current_var_decl.sibling:
                    current_var_decl = current_var_decl.sibling

        md_decl = []
        md_decl_processed = False

        if self.method_declarations:
            current_md_decl = self.method_declarations

            while not md_decl_processed:

                if not current_md_decl.child and not current_md_decl.sibling:
                    md_decl_processed = True

                if current_md_decl:
                    md_decl.append((
                        current_md_decl.method_name,
                        current_md_decl.get_arguments(),
                        current_md_decl.get_return_type()
                    ))

                if current_md_decl.sibling:
                    current_md_decl = current_md_decl.sibling

        context: List[Any] = [[self.class_name, [var_decl, md_decl]]]

        if self.sibling:
            context += self.sibling.initialise_class_descriptor()

        return context

    def _initialise_local_environment(self) -> List[Any]:

        local_environment: List[Any] = []

        vars_completed = False

        current_vars = self.variable_declarations

        while not vars_completed:

            local_environment.append((current_vars.value, current_vars.type))

            if not current_vars.sibling:
                vars_completed = True
                break

            current_vars = current_vars.sibling

        mds_completed = False

        current_mds = self.method_declarations

        while not mds_completed:

            local_environment.append((
                current_mds.method_name,
                current_mds.get_arguments(),
                current_mds.get_return_type()
            ))

            if not current_mds.sibling:
                mds_completed = True
                break

            current_mds = current_mds.sibling

        return local_environment

    def _check_variable_declaration_names(self) -> None:

        var_names = []

        var_processed = False

        current_var = self.variable_declarations

        while not var_processed:
            if not current_var.child and not current_var.sibling:
                var_processed = True

            if current_var:
                if current_var.value in var_names:
                    raise TypeError(str(current_var.value), "Field has the same name as an earlier declared field in class: [" + str(self.class_name) + "]\n")
                else:
                    var_names.append(current_var.value)

            if current_var.sibling:
                current_var = current_var.sibling

    def _check_method_names(self) -> None:

        md_names = []

        md_processed = False

        current_md = self.method_declarations

        while not md_processed:
            if not current_md.sibling:
                md_processed = True

            if current_md:
                if current_md.method_name in md_names:
                    raise TypeError(str(current_md.method_name), "Method has the same name as an earlier declared method in class: [" + str(self.class_name) + "]\n")
                else:
                    md_names.append(current_md.method_name)

            if current_md.sibling:
                current_md = current_md.sibling

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if debug:
            sys.stdout.write("ClassDeclNode - Type checking initiated for class " + self.class_name + '\n')

        # Check field names
        self._check_variable_declaration_names()

        if debug:
            sys.stdout.write("ClassDeclNode - No collision in field names.\n")

        self._check_method_names()

        if debug:
            sys.stdout.write("ClassDeclNode - No collision in method names.\n")

        if self.variable_declarations:
            self.variable_declarations.type_check(env, debug, self.class_name)

            local_env = self._initialise_local_environment()

            if debug:
                sys.stdout.write("ClassDeclNode - Initialised local environment: " + str(local_env) + "\n")

            for l in local_env:
                env[1].append(l)

        if debug:
            sys.stdout.write("ClassDeclNode - Type checking completed for variable declarations.\n")

        # Add 'this' to local environment
        env[1].append(('this', (BasicType.OBJECT, self.class_name)))

        if debug:
            sys.stdout.write("ClassDeclNode - Adding 'this' to local environment: " + str(env[1]) + "\n")

        self.method_declarations.type_check(env, debug, self.class_name)

        if self.child:
            self.child.type_check(env, debug, self.class_name)

        if self.sibling:
            self.sibling.type_check(env, debug)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:
        sys.stdout.write("class " + self.class_name + "{ \n")
        self.variable_declarations.pretty_print(delimiter=';\n', preceding='  ')
        self.method_declarations.pretty_print(delimiter=';\n', preceding='  ')

        if self.child:
            self.child.pretty_print(delimiter, preceding='  ')

        sys.stdout.write("\n}\n")

        if self.sibling:
            self.sibling.pretty_print()

class MdDeclNode(ASTNode):

    method_name: str
    return_type: str
    arguments: Any
    variable_declarations: Any
    statements: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_method_name(self, method_name: str) -> None:
        self.method_name = method_name

    def set_return_type(self, return_type: str) -> None:
        self.return_type = return_type

    def set_arguments(self, node: Any) -> None:
        self.arguments = node

    def set_variable_declarations(self, node: Any) -> None:
        self.variable_declarations = node

    def set_statements(self, node: Any) -> None:
        self.statements = node

    def get_arguments(self) -> FunctionType:

        args: List[Any] = []
        args_processed = False

        if self.arguments:
            current_arg = self.arguments

            while not args_processed:

                if not current_arg.child and not current_arg.sibling:
                    args_processed = True

                if current_arg:

                    if current_arg.type in ['Int', 'String', 'Bool']:
                        args.append(TYPE_CONVERSION_DICT[current_arg.type])

                    else:
                        args.append((BasicType.OBJECT, current_arg.type))

                if current_arg.sibling:
                    current_arg = current_arg.sibling

        return FunctionType(args)

    def get_return_type(self) -> Union["BasicType", Tuple["BasicType", str]]:

        if self.return_type in TYPE_CONVERSION_DICT:
            return TYPE_CONVERSION_DICT[self.return_type]

        else:
            return (BasicType.OBJECT, self.return_type)

    def _initialise_local_environment_args(self) -> List[Tuple[str, Union["BasicType", Tuple["BasicType", str]]]]:

        local_environment = []

        args_completed = False

        current_args = self.arguments

        while not args_completed:

            local_environment.append((current_args.value, current_args.type))

            if not current_args.sibling:
                args_completed = True
                break

            current_args = current_args.sibling

        return local_environment

    def _initialise_local_environment_vars(self) -> List[Tuple[str, Union["BasicType", Tuple["BasicType", str]]]]:

        local_environment = []

        vars_completed = False

        current_vars = self.variable_declarations

        while not vars_completed:

            local_environment.append((current_vars.value, current_vars.type))

            if not current_vars.sibling:
                vars_completed = True
                break

            current_vars = current_vars.sibling

        return local_environment

    def _check_argument_names(self) -> None:

        arg_names = []
        args_processed = False

        if self.arguments:
            current_arg = self.arguments

            while not args_processed:

                if not current_arg.sibling:
                    args_processed = True

                if current_arg:

                    if current_arg.value in arg_names:
                        raise TypeError(current_arg.value, "Argument has the same name as an earlier declared argument.")
                    else:
                        arg_names.append(current_arg.value)

                if current_arg.sibling:
                    current_arg = current_arg.sibling


    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self._check_argument_names()

        if debug:
            sys.stdout.write("MdDeclNode - No collision in argument names.\n")

        if self.arguments:
            self.arguments.type_check(env, debug, within_class)

            local_args = self._initialise_local_environment_args()

            if debug:
                sys.stdout.write("MdDeclNode - Adding args to local environment: " + str(local_args) + "\n")

            for a in local_args:
                env[1].append(a)

            # Add arguments to environment

        if debug:
            sys.stdout.write("MdDeclNode - Arguments type check completed.\n")

        if self.variable_declarations:
            self.variable_declarations.type_check(env, debug, within_class)

            local_vars = self._initialise_local_environment_vars()

            if debug:
                sys.stdout.write("MdDeclNode - Adding vars to local environment: " + str(local_vars) + "\n")

            for v in local_vars:
                env[1].append(v)

        if debug:
            sys.stdout.write("MdDeclNode - Variable declarations type check completed.\n")
            sys.stdout.write("MdDeclNode - Passing return type to statements: " + str(self.get_return_type()) + '\n')

        self.statements.type_check(env, debug, within_class, self.get_return_type())

        if self.child:
            self.child.type_check(env, debug, within_class)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + self.return_type + ' ' + self.method_name)

        sys.stdout.write('(')
        if self.arguments:
            self.arguments.pretty_print(delimiter=',')
        sys.stdout.write(')')

        sys.stdout.write(preceding + '{\n')
        if self.variable_declarations:
            self.variable_declarations.pretty_print(delimiter=';\n', preceding=preceding + '  ')

        sys.stdout.write('\n')
        self.statements.pretty_print(preceding=preceding + '  ')

        if self.child:
            self.child.pretty_print(delimiter, preceding + '  ')

        sys.stdout.write('\n' + preceding+'}')


        if self.child:
            self.child.pretty_print(delimiter, preceding=preceding)

        sys.stdout.write('\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)


class DualOperandNode(ASTNode):

    left_operand: Any
    right_operand: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_left_operand(self, node: Any) -> None:
        self.left_operand = node

    def set_right_operand(self, node: Any) -> None:
        self.right_operand = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + '(' + '(')
        self.left_operand.pretty_print()
        sys.stdout.write(')')

        sys.stdout.write(self.value)

        sys.stdout.write(preceding + '(')
        self.right_operand.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write(')')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ArithmeticOpNode(DualOperandNode):

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + '(')
        self.left_operand.pretty_print()
        sys.stdout.write(self.value)
        self.right_operand.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None
    ) -> None:

        self.left_operand.type_check(env, debug, within_class, return_type)
        self.right_operand.type_check(env, debug, within_class, return_type)

        if self.value in ('*/-'):
            if self.left_operand.type != BasicType.INT and self.left_operand.value != 'null':
                raise TypeError(self.left_operand.value)
            elif self.right_operand.type != BasicType.INT and self.right_operand_value != ' null':
                raise TypeError(self.right_operand.value)

            # Set type as Int once operands have been type-checked
            self.type = BasicType.INT

        elif self.value == '+':

            if debug:
                sys.stdout.write("ArithmeticOpNode - '+' operator detected.\n")

            if self.left_operand.type == BasicType.INT:
                if self.right_operand.type == BasicType.INT or self.right_operand.value == 'null':
                    # Set type as Int once operands have been type-checked
                    self.type = BasicType.INT

                else:
                    raise TypeError(self.right_operand.value, "Right operand is not an integer.")

            elif self.left_operand.type == BasicType.STRING:
                if self.right_operand.type == BasicType.STRING or self.right_operand.value == 'null':
                    # Set type as String once operands have been type-checked
                    self.type = BasicType.STRING

                else:
                    raise TypeError(self.right_operand.value, "Right operand is not a string.")

        if debug:
            sys.stdout.write("ArithmeticOpNode - Type check successfully completed with assigned type: " +  \
                str(self.type) + "\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

class BinOpNode(DualOperandNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self.left_operand.type_check(env, debug, within_class, return_type)

        if self.left_operand.type != BasicType.BOOL:
            raise TypeError(self.left_operand.value)

        self.right_operand.type_check(env, debug, within_class, return_type)

        if self.right_operand.type != BasicType.BOOL:
            raise TypeError(self.right_operand.value)

        self.type = BasicType.BOOL

        if debug:
            sys.stdout.write("BinOpNode type check successfully completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

class RelOpNode(DualOperandNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        #sys.stdout.write('checking typing for BinOpNode. left operand: ' + self.left_operand.value)

        if self.left_operand:
            self.left_operand.type_check(env, debug, within_class, return_type)

            if debug:
                sys.stdout.write("RelOpNode - Left operand: " + \
                    str(self.left_operand.value) + " of type " + \
                    str(self.left_operand.type) + '\n')

            if self.value in ['<', '>', '<=', '>=']:

                if self.left_operand.type != BasicType.INT:
                    raise TypeError(self.left_operand.value)

        if self.right_operand:

            if debug:
                sys.stdout.write("RelOpNode - Starting type check for right operand: " + \
                    str(self.right_operand.value) + " of type " + \
                    str(self.right_operand.type) + '\n')

            self.right_operand.type_check(env, debug, within_class, return_type)

            if debug:
                sys.stdout.write("RelOpNode - Right  operand: " + \
                    str(self.right_operand.value) + " of type " + \
                    str(self.right_operand.type) + '\n')

            if self.value in ['<', '>', '<=', '>=']:
                if self.right_operand.type != BasicType.INT:
                    raise TypeError(self.right_operand.value)

        self.type = BasicType.BOOL

        if debug:
            sys.stdout.write("RelOpNode type check successfully completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

class AssignmentNode(ASTNode):

    identifier: Any
    assigned_value: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any) -> None:
        self.identifier = node

    def set_assigned_value(self, node: Any) -> None:
        self.assigned_value = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding)
        self.identifier.pretty_print()
        sys.stdout.write('=')
        self.assigned_value.pretty_print()
        sys.stdout.write(';\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if debug:
            sys.stdout.write("AssignmentNode - Env received: " + str(env) + '\n')

        env_copy = copy.deepcopy(env)

        # Type check for identifier
        self.identifier.type_check(env_copy, debug, within_class, return_type)

        if debug:
            sys.stdout.write("AssignmentNode - Type check for identifier: " + \
            str(self.identifier.value) + " with type " + \
            str(self.identifier.type) + " completed.\n")

        self.assigned_value.type_check(env_copy, debug, within_class, return_type)

        if self.assigned_value.type != self.identifier.type and self.assigned_value.value != 'null':
            raise TypeError(str(self.identifier.value), 'Assigned value type [' + str(self.assigned_value.type) + \
                '] does not match declared identifier type [' + str(self.identifier.type) +']')

        if debug:
            sys.stdout.write("AssignmentNode - Identifier and assigned value types matched.\n")
            sys.stdout.write("AssignmentNode - Env after processing: " + str(env) + '\n')
            sys.stdout.write("AssignmentNode type check successfully completed.\n")

        if self.child:
            if debug:
                sys.stdout.write("AssignmentNode - Env passed to child: " + str(env) + '\n')
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            if debug:
                sys.stdout.write("AssignmentNode - Env passed to sibling: " + str(env) + '\n')
            self.sibling.type_check(env, debug, within_class, return_type)

class InstanceNode(ASTNode):

    atom: Any
    identifier: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_atom(self, node: Any) -> None:
        self.atom = node

    def set_identifier(self, node: Any) -> None:
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        self.atom.pretty_print()
        sys.stdout.write('.')
        self.identifier.pretty_print()

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

    def _get_arg_type(self, current_arg, env, debug=False):

        if debug:
            sys.stdout.write("InstanceNode - Retrieving argument type for: " + current_arg + '\n')

        env_checked = False

        derived_type = None

        while not env_checked:

            if len(env) == 0:
                env_checked = True

            current_class = env[0].pop()

            if current_class[1]:

                for current_env in current_class[1]:

                    if debug:
                        sys.stdout.write("Current value: " + current_arg + '\n')
                        sys.stdout.write("Checking for current env: " + str(current_env) + '\n')

                    if current_arg == current_env[0]:

                        derived_type = current_env[1]
                        # Terminate while loop
                        env_checked = True

                        # Break out of for loop
                        break

        return derived_type

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if debug:
            sys.stdout.write("InstanceNode with atom: " + self.atom.value + \
            ", and identifier " + self.identifier.value + '\n')

        self.atom.type_check(env, debug, within_class, return_type)

        class_for_identifier_type_check = self.atom.type[1]

        if debug:
            sys.stdout.write("InstanceNode - Type check completed for atom with type ." + str(self.atom.type) + '\n')

        self.identifier.type_check(env, debug, class_for_identifier_type_check, return_type)

        if debug:
            sys.stdout.write("InstanceNode - Type check completed for identifier with type ." + str(self.identifier.type) + '\n')

        # Boolean for while loop
        env_checked = False

        # Booleans to track result of type checking class for method
        class_found = False

        env_copy: Any = copy.deepcopy(env)

        while not env_checked:

            if len(env_copy) == 0:
                env_checked = True
                break

            current_class = env_copy[0].pop()
            if debug:
                sys.stdout.write("InstanceNode - Current env: " + str(current_class) + "\n")

            # Check for class of atom in environment
            if class_for_identifier_type_check == current_class[0]:

                class_found = True

                if debug:
                    sys.stdout.write("InstanceNode - Atom found in environment.\n")

                # If there is an expression list, check for methods

                if isinstance(self.type, FunctionType):

                    method_found = False

                    # Iterate through method in current class0
                    for md in current_class[1][1]:

                        # Checks if identifier name matches
                        if self.identifier.value == md[0]:

                            if debug:
                                sys.stdout.write("InstanceNode - Atom and identifier found in environment.\n")
                                sys.stdout.write("InstanceNode - Identifier found in environment.\n")

                            # Assign return type as type of current InstanceNode
                            self.type = md[2]

                            if debug:
                                sys.stdout.write("InstanceNode - Assigned type: " + str(self.type) + "\n")

                            method_found = True

                            # Type check expression list if it exists
                            if isinstance(self.child, ExpListNode):

                                self.child.type_check(env, debug, within_class, return_type)

                                current_args = self.child.get_arguments(debug)
                                current_args_count = len(current_args)

                                if debug:
                                    sys.stdout.write("InstanceNode - Arguments list retrieved: " + str(current_args) + "\n")

                                expected_args = md[1].basic_type_list
                                expected_args_count = len(expected_args)

                                # Simple check for number of arguments
                                if current_args_count != expected_args_count:
                                    raise TypeError(
                                        str(self.atom.value)+'.'+str(self.identifier.value)+ '()',
                                        'Function expected ' + str(expected_args_count) + \
                                        ' arguments but got ' + str(current_args_count)
                                    )

                                # Detailed type check of argument type

                                for i in range(len(current_args)):

                                    current_arg = current_args[i]

                                    if debug:
                                        sys.stdout.write(
                                            "InstanceNode - Checking for type of argument: " + current_arg + '\n'
                                        )

                                    current_arg_type = self._get_arg_type(current_arg, env, debug)

                                    # Checks if argument has been declared
                                    if not current_arg_type:
                                        raise TypeError(
                                            str(self.atom.value)+'.'+str(self.identifier.value)+ '()',
                                            'Undeclared argument.'
                                        )

                                    # Checks if argument matches expected type
                                    if current_arg_type != expected_args[i]:
                                        raise TypeError(
                                            str(self.atom.value)+'.'+str(self.identifier.value)+ '()',
                                            'Function expected ' + str(expected_args[i]) + ' but got ' + str(current_arg_type) + ' instead.\n'
                                        )

                                    if debug:
                                        sys.stdout.write(
                                            "InstanceNode - Argument of " + str(self.atom.value)+'.' + \
                                            str(self.identifier.value) + '() type checked: ' + current_arg + '\n'
                                        )

                            if not method_found:
                                raise TypeError(str(self.atom.value)+'.'+str(self.identifier.value), 'Unable to locate function in given class')

                    env_checked = True
                    break
                # Otherwise, check for variables
                else:

                    identifier_found = False

                    for var in current_class[1][0]:
                        if debug:
                            sys.stdout.write("InstanceNode - Atom and identifier found in environment.\n")
                            sys.stdout.write("InstanceNode - Identifier found in environment.\n")

                        # Assign variable type as type of current InstanceNode
                        self.type = var[1]

                        identifier_found = True

                    if not identifier_found:
                        raise TypeError(str(self.atom.value), "Variable is not defined in class.")

                    env_checked = True
                    break

                # Check for declaration in matched class
                env_checked = True

        if not class_found:
            raise TypeError(str(self.atom.value), 'Unable to locate given class')

        if debug:
            sys.stdout.write("InstanceNode type check successfully completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

class ClassInstanceNode(ASTNode):

    target_class: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_target_class(self, node: Any) -> None:
        self.target_class = node

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self.target_class.type_check(env, debug, within_class, return_type)

        if self.target_class.type:
            self.type = self.target_class.type

        if debug:
            sys.stdout.write("ClassInstanceNode type check successfully completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('new ')
        self.target_class.pretty_print()
        sys.stdout.write('()')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ReturnNode(ASTNode):

    return_value: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.return_value = None

    def set_return_value(self, node: Any) -> None:
        self.return_value = node

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if debug:
            sys.stdout.write("ReturnNode - Successfully received return type: " + str(return_type) + '\n')

        # Check for
        if self.return_value:
            self.return_value.type_check(env, debug, within_class)
            self.type = self.return_value.type
        else:
            # Set type to Void if its return value is None
            self.type = BasicType.VOID

        if self.type != return_type:
            raise TypeError(self.return_value, "Return type " + str(self.return_value.type) + \
                " is different from declared: " + str(return_type))

        if debug:
            sys.stdout.write("ReturnNode - Successfully type checked return value: " + str(return_type) + '\n')

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + self.value)
        if self.return_value:
            sys.stdout.write(' ')
            self.return_value.pretty_print()
        sys.stdout.write(';\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class IfElseNode(ASTNode):

    condition: Any
    if_expression: Any
    else_expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_condition(self, node: Any) -> None:
        self.condition = node

    def set_if_expression(self, node: Any) -> None:
        self.if_expression = node

    def set_else_expression(self, node: Any) -> None:
        self.else_expression = node

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self.condition.type_check(env, debug, within_class)

        if debug:
            sys.stdout.write("IfElseNode - Condition type check completed.\n")

        self.if_expression.type_check(env, debug, within_class, return_type)

        if debug:
            sys.stdout.write("IfElseNode - If expression type check completed.\n")

        self.else_expression.type_check(env, debug, within_class, return_type)

        if debug:
            sys.stdout.write("IfElseNode - Else expression type check completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + 'if (')
        self.condition.pretty_print()
        sys.stdout.write(') {\n')

        self.if_expression.pretty_print(preceding=preceding+'  ')
        sys.stdout.write(preceding + '}' + ' else {\n')
        self.else_expression.pretty_print(preceding=preceding+'  ')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write(preceding + '}' + '\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class WhileNode(ASTNode):

    condition: Any
    while_expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_condition(self, node: Any) -> None:
        self.condition = node

    def set_while_expression(self, node: Any) -> None:
        self.while_expression = node

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self.condition.type_check(env, debug, within_class)

        if self.while_expression:
            self.while_expression.type_check(env, debug, within_class, return_type)

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter:str='', preceding:str ='') -> None:
        sys.stdout.write(preceding + 'while (')
        self.condition.pretty_print()
        sys.stdout.write(') {\n')
        self.while_expression.pretty_print(delimiter, preceding+'  ')


        if self.child:
            self.child.pretty_print(delimiter, preceding)

        sys.stdout.write('\n' + preceding + '}' + '\n')

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ReadLnNode(ASTNode):

    identifier: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_identifier(self, node: Any) -> None:
        self.identifier = node

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + 'readln(')
        self.identifier.pretty_print()
        sys.stdout.write(');\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if debug:
            sys.stdout.write("Env for ReadLn type check: " + str(env) + "\n")
            sys.stdout.write("ReadLnNode - Successfully receive return type: " + str(return_type) + '\n')

        self.identifier.type_check(env, debug, within_class)

        if debug:
            sys.stdout.write("ReadLnNode - identifier " + self.identifier.value + " with type: " + str(self.identifier.type) + '\n')

        if self.identifier.type not in [BasicType.INT, BasicType.STRING, BasicType.BOOL]:
            raise TypeError(self.identifier.value, 'Invalid readln type')

        if debug:
            sys.stdout.write("ReadLnNode type check successfully completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

class PrintLnNode(ASTNode):

    expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_expression(self, node: Any) -> None:
        self.expression = node

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if debug:
            sys.stdout.write("PrintLnNode - Env received: " + str(env) + '\n')

        self.expression.type_check(env, debug, within_class)

        if debug:
            sys.stdout.write("PrintLnNode - Type check for expression: [" + self.expression.value + '] completed.\n')
            sys.stdout.write("PrintLnNode - Type assigned to expression: " + str(self.expression.type) + '\n')

        if self.expression.type not in [BasicType.INT, BasicType.STRING, BasicType.BOOL]:
            raise TypeError(self.expression.value, 'Invalid println type')

        if debug:
            sys.stdout.write("PrintLnNode type check successfully completed.\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str=''):

        if self.expression:
            sys.stdout.write(preceding + 'println(')
            self.expression.pretty_print()
            sys.stdout.write(');\n')

        if self.child:
            self.child.pretty_print(delimiter, preceding)

        if self.sibling:
            self.sibling.pretty_print(delimiter, preceding)

class ArgumentNode(ASTNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.is_identifier = True

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        super()._assign_declaration_type(env, debug, within_class)

        if debug:
            sys.stdout.write("ArgumentNode - Type check successfully completed.\n")
            sys.stdout.write("ArgumentNode - Assigned with type: " + str(self.type) + "\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(self.type + ' ' + self.value)

        if self.sibling:
            sys.stdout.write(', ')
            self.sibling.pretty_print()

class VarDeclNode(ASTNode):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.is_identifier = True

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        super()._assign_declaration_type(env, debug, within_class)

        if debug:
            sys.stdout.write("VarDeclNode - Type check successfully completed for: " + str(self.value) + "\n")

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write(preceding + self.type + ' ' + self.value + delimiter)

        if self.sibling:
            #sys.stdout.write('\n')
            self.sibling.pretty_print(delimiter, preceding)

class ExpListNode(ASTNode):

    expression: Any

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.expression = None

    def set_expression(self, node: Any) -> None:
        self.expression = node

    def get_arguments(self, debug=False):

        completed = False

        current_node = self.expression

        exp_list = []

        while not completed:

            if not current_node:
                completed = True
                break

            exp_list.append(current_node.value)

            current_node = current_node.child

        if debug:
            sys.stdout.write("ExpListNode - Expression list retrieved: " + str(exp_list) + '\n')

        return exp_list

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self.expression.type_check(env, debug, within_class)

        if self.child:
            self.child.type_check(env, debug, within_class)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('(')

        if self.expression:
            self.expression.pretty_print(',', preceding)

        sys.stdout.write(')')

class NegationNode(ASTNode):

    negated_expression: Any

    def __init__(self, negated_expression: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.negated_expression = negated_expression

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        if self.negated_expression.type != 'Int':
            raise TypeError(self.negated_expression.value)

        self.negated_expression.type_check(env, debug, within_class)

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('(-')
        self.negated_expression.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print()

        if self.sibling:
            self.sibling.pretty_print()

class ComplementNode(ASTNode):

    complement_expression: Any

    def __init__(self, complement_expression: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.complement_expression = complement_expression

    def type_check(
        self,
        env: List[Deque[Any]]=None,
        debug: bool=False,
        within_class: str='',
        return_type: Any=None,
    ) -> None:

        self.complement_expression.type_check(env, debug, within_class)

        if self.complement_expression.type != BasicType.BOOL:
            raise TypeError(self.complement_expression.value, "Complement expression is not of boolean type.")

        else:
            self.type = BasicType.BOOL

        if debug:
            sys.stdout.write('Type checking complement expression: ' + str(self.complement_expression.type) + '\n')

        if self.child:
            self.child.type_check(env, debug, within_class, return_type)

        if self.sibling:
            self.sibling.type_check(env, debug, within_class, return_type)

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        sys.stdout.write('(!)(')

        self.complement_expression.pretty_print()
        sys.stdout.write(')')

        if self.child:
            self.child.pretty_print()

        if self.sibling:
            self.sibling.pretty_print()

class AbstractSyntaxTree:

    head: Any
    initial_env: Any

    def __init__(self, head: Any) -> None:

        self.head = head

    def pretty_print(self, delimiter: str='', preceding: str='') -> None:

        if self.head:
            self.head.pretty_print()

    def type_check(self, debug: bool=False) -> None:

        self.head.type_check(debug=debug)

    def initialise_env(self) -> None:
        self.initial_env = self.head.initialise_class_descriptor()
