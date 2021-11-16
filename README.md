# CS4212 Project Report [AY2021/2022 Semester 2]

- Name: Tse Rong Gary
- Student ID: A0110500L

## Introduction

The directory comprises the following files:
```
jlite-compiler
 ├── lib/                       # Other files
     └── Grammar.pdf            # File containing rewritten grammar
 ├── test/                      # Test cases
     └── ir3/                   # Test cases for parser with type checking and IR3 code generation
     └── parse/                 # Test cases for lexer and parser without type check
 ├── ast.py                     # AST tree and node classes
 ├── compile.py                 # Compiler class
 ├── control_flow.py            # ControlFlowGenerator class
 ├── gen.py                     # IR3Generator class
 ├── ir3.py                     # IR3 tree and node classes
 ├── instruction.py             # Instruction class
 ├── jlite_type.py              # Type classes
 ├── lex_dfa.py                 # DFA for lexer
 ├── lex.py                     # Lexer class
 ├── parse.py                   # Parser class
 ├── peephole_optimization.py   # PeepholeOptimizer class
 ├── symbol_table.py            # SymbolTable class
 └── TseRongGary_pa1_readme.md
 └── TseRongGary_pa2_readme.md
```

Notes
- The rewritten grammar is set out in `lib/Grammar.pdf`.
- Test cases are in `test/`

## Dependencies

- Python 3.8.10
- arm-linux-gnueabi-gcc-10
- qemu-arm

## Running on local environment

1. To lex a file, run `python lex.py [FILE_NAME].j`
2. To parse and type check a file, run `python parse.py [FILE_NAME].j`
3. To generate the IR3 code for a file, run `python gen.py [FILE_NAME].j`
4. To generate the assembly code for a file, run `python compile.py [FILE_NAME].j`. This will generate a `program.s` file in the root folder.
  - To enable debugging, insert `--debug` to the command.
  ```
  python compile.py [FILE_NAME].j --debug
  ```

  - To enable optimization, insert `--optimize` to the command.
  ```
  python compile.py [FILE_NAME].j --optimize
  ```
5. To generate the bytecode, run `arm-linux-gnueabi-gcc-10 program.s --static`. This will generate a `a.out` file to the root folder.
6. To run the program, run `qemu-arm a.out`.

## Lexer

The `lex_dfa.py` file contains the following constants that are used in `lex.py`:
- `DFA`: The deterministic finite automaton (DFA) for the lexer is defined as a dictionary. It provides for the valid state transitions for a lexeme from the current character.
- `FINAL_STATES`: A set of states in the DFA that is an accepted final state, excluding `COMMENT_FINAL_STATES`, and therefore qualifies the lexeme to be read as a token.
- `COMMENT_INTERMEDIATE_STATES`: A set of states in the DFA that is an intermediate state for comments. This is used to catch nested comments.
- `COMMENT_FINAL_STATES`: A set of states in the DFA that is an accepted final state for comments.

The `lex.py` file contains the following classes of objects:
- `LexError`: Exception class for errors encountered while lexing.
- `Token`: Token class to store lexemes in an accepted final state of the DFA.
- `Lexer`: Lexer class containing the main logic for reading an input file and converting it into a stream of tokens.

### Design of `Lexer`

The `Lexer` contains the following helper functions:
- `_get_current_char_class()`: Takes a character and returns the classification of the current character in the DFA. This function is called in `_scan_next_char()`.
- `_scan_next_char()`: Takes a character and the current DFA state, and returns the next state of the DFA to traverse to based on the character.
- `_analyse_lexeme()`: Takes a lexeme and its related information, and tokenises it if it is in a final state of the DFA.

The `lex_content()` function contains the main logic for the `Lexer`.
1. The `while` loop reads in one character at a time until the boolean variable `completed` (initialised to `False`) is set to `True`. The current lexeme and the DFA state of the current lexeme are initialised to the empty string `''` and `'0'` respectively.
2. If the character is not an empty string, the `_scan_next_char()` function is called to determine the new DFA state to traverse to.
3. If the new DFA state exists, the character is appended to the current lexeme.
4. Otherwise, the character is an invalid state transition from the current lexeme. The current lexeme is added as a token if it is in a final state. The current lexeme is then reset. If the current character is a valid transition from the start state of the DFA, it is appended to the current lexeme. The function then returns to the start of the while loop in step 1.
5. If the character is an empty string, the current lexeme is added as a token if it is in a final state. The EOF token is then added, and `completed` is set to `True` to exit the `while` loop.

### Error handling

The following errors will be reported to the user by the lexer:
- Multi-line comments that are improperly paired

  Example:
  ```
  __main__.LexError: Unable to lex expression:  Improperly paired multi-line comment found at index 1 of line 1.
  ```
- Missing semi-colon at the end of a statement

  Example:
  ```
  __main__.LexError: Unable to lex expression:  Missing semicolon for statement at line 13.
  ```

## Parser

The `ast.py` file contains the following generic classes:
- `ASTNode`: Node class to construct the abstract syntax tree. This is used to construct various heterogenous abstract syntax trees as further elaborated on in the next sub-section.
- `AbstractParseTree`: Parse tree class to point to the root node.

The `parse.py` file contains the following classes of objects:
- `ParseError`: Exception class for errors encountered while parsing.
- `InvalidExpressionError`: Exception class for errors encountered while consuming a token during parsing.
- `Parser`: Parser class containing the main logic for parsing a stream of tokens from the Lexer.

### Design of Abstract Syntax Tree

The abstract syntax tree is composed from the `ASTNode` class, which has a value and type, and points to a child and a sibling.

The `ASTNode` class is inherited by the following classes for specific statements and declarations:
- `MainClassNode`: The main class declaration of a program
- `ClassDeclNode`: Subsequent class declarations of a program
- `MdDeclNode`: Declaration of a method
- `ArithmeticOpNode`: Arithmetic operations with a left operand and a right operand
- `BinOpNode`: Binary operations with a left operand and a right operand
- `RelOpNode`: Relational operators with a left operand and a right operand. Inherits from `BinOpNode`.
- `AssignmentNode`: Assignment operation
- `InstanceNode`: Reference to an instance
- `ClassInstanceNode`: Declaration of a new object of a class
- `ReturnNode`: Return statement
- `IfElseNode`: If/else expression
- `WhileNode`: While expression
- `ReadLnNode`: Read line operation
- `PrintLnNode`: Print line operation
- `ExpListNode`: Expression list
- `ComplementNode`: Complement operation
- `NegationNode`: Negation operation

The `pretty_print()` function prints the abstract syntax tree in a recursive manner by traversing from the root node. The generic `ASTNode` class will traverse its child (and sub-childs) before its sibling.

### Design of `Parser`

The `Parser` contains the following helper functions:
- `_lex_content()`: Lexes the input file.
- `_eat()`: Consumes the current token if it matches the expected token, and returns a `Node` instance of the token.
- `_kleene_closure_loop()`: Helper function to execute the Kleene's closure on a given expression, and returns the root `Node` and the resulting `Lexer`.
- `_positive_closure_loop()`: Helper function to execute the positive closure on a given expression, and returns the root `Node` and the resulting `Lexer`.

The `parse()` function contains the main logic to parse the stream of tokens from the `Lexer` using recursive descent parsing. Each expression set out in the `Grammar.pdf` file in the `lib` folder has an equivalent internal function in `parse.py`. Backtracking is implemented using try and except control structures by raising an `InvalidExpressionError` or a `ParseError`.
- Where backtracking is required, a deep copy of the `Lexer` is created, updated as and when a valid expression is valid, and then returned. To backtrack, the original lexer is returned instead of the deep copy.

### Error handling

The following errors will be reported to the user by the lexer:
- Internal error used to backtrack when the token consumed does not match the expected token.

  Example:
  ```
  __main__.InvalidExpressionError: Unable to derive expression.
  ```
- Error thrown when the current expression cannot be derived. It is also used for backtracking, and will be propagated upwards (i.e. a parsing error may result in multiple errors of different depths).

  Example:
  ```
  __main__.ParseError: Invalid expression at:  _type_expression. Unable to parse token = at index 20 of line 15.
  ```

## Abstract Syntax Tree (AST)

The `ast.py` file contains the following generic classes:
- `ASTNode`: Node class to construct the abstract syntax tree. This is used to construct various heterogenous abstract syntax trees as further elaborated on in the next sub-section.
- `AbstractSyntaxTree`: AST class to point to the root node.

The`jlite_type.py` file contains the following:
- Type information
  - `BasicType`: Enum type for basic JLITE types.
  - `FunctionType`: Function type for methods.
- `TypeCheckError`: Exception class for type checking errors.

### Design of AST

The abstract syntax tree is composed of the base `ASTNode` class (which has a value and type, and points to a child and a sibling) and its derived classes.

The following classes are derived from the `ASTNode` base class for specific statements and declarations:
- `MainClassNode`: The main class declaration of a program
- `ClassDeclNode`: Subsequent class declarations of a program
- `MdDeclNode`: Declaration of a method
- `DualOperandNode`: Base class for nodes with dual operands
    - `ArithmeticOpNode`: Arithmetic operations with a left operand and a right operand
    - `BinOpNode`: Binary operations with a left operand and a right operand
    - `RelOpNode`: Relational operators with a left operand and a right operand.
- `AssignmentNode`: Assignment operation
- `InstanceNode`: Reference to an instance
- `ClassInstanceNode`: Declaration of a new object of a class
- `ReturnNode`: Return statement
- `IfElseNode`: If/else expression
- `WhileNode`: While expression
- `ReadLnNode`: Read line operation
- `PrintLnNode`: Print line operation
- `ArgumentNode`: Arguments
- `VarDeclNode`: Variable declarations
- `ExpListNode`: Expression list
- `ComplementNode`: Complement operation
- `NegationNode`: Negation operation

The `pretty_print()` function prints the abstract syntax tree in a recursive manner by traversing from the root node. The generic `ASTNode` class will traverse its child (and sub-childs) before its sibling. For the derived classes, the `pretty_print()` function is modified to print the additional attributes attached to those classes.

### Construction of AST

The `Parser` contains the following helper functions:
- `_lex_content()`: Lexes the input file.
- `_eat()`: Consumes the current token if it matches the expected token, and returns a `Node` instance of the token.
- `_kleene_closure_loop()`: Helper function to execute the Kleene's closure on a given expression, and returns the root `Node` and the resulting `Lexer`.
- `_positive_closure_loop()`: Helper function to execute the positive closure on a given expression, and returns the root `Node` and the resulting `Lexer`.

The `parse()` function contains the main logic to parse the stream of tokens from the `Lexer` using recursive descent parsing and to construct the AST. Each expression set out in the `Grammar.pdf` file in the `lib` folder has an equivalent internal function in `parse.py`.

### Static Checker

The Parser will only be able to type check if the AST has been successfully created after parsing.

The type checking is done by traversing the AST using the `type_check` function of ASTNode, and overloaded as applicable in the derived nodes. The `type_check` function does both distinct-name checking and type checking.

#### Distinct-Name Checking

Distinct name checking is carried out by the `type_check` function calling the following helper functions in the respective nodes as follows:
- `MainClassNode`:
  - `_check_class_declaration_names`: Ensures that no two classes can be declared in a program with the same class name
- `ClassDeclNode`:
  - `_check_variable_declaration_names`: Ensures that no two fields in a class have the same name.
  - `_check_method_names`: Ensures that no two methods within a class declaration can have the same name. Overloaded methods are not supported.
- `MdDeclNode`:
  - `_check_argument_names`: Ensures that no two parameters in a method declaration can have the same name.

#### Overloaded Methods
- The following types of overloaded methods are supported:
  - Multiple methods with the same return types, but different number of arguments.
  - Multiple methods with the same return type, same number of arguments, but different argument types and ordering.
- The following types of overloaded methods are not supported:
  - Multiple methods with different return types, but same number of arguments.
- Type checking of overloaded methods is executed using the `_type_check_methods()` function in the `ClassDeclNode` class. For each method, the function will loop through the remaining methods in the same class with the same name, and check if the list of arguments are identical. This checks the ordering of the argument types since both are lists.
- The logic for the assignment of the type information for method calls resides in the `type_check` function of the `InstanceNode` class. If the node type is of `FunctionType` class, the Parser will first iterate through the class descriptor in the local environment stack. If the class descriptor is found, the Parser will then check if there are no matches (the method does not exist), exactly one match (only one possible method call) or multiple matches (multiple possible method calls as it is an overloaded method) for the given method name.
- If it is an overloaded method, the Parser will check the current method call against each possible match in two steps:
  - Check if the number of arguments match what is expected
  - Check if the list of argument types match what is expected in the `basic_type_list` attribute of the `FunctionType` retrieved from the local environment stack. This implicitly checks the ordering of the argument types since both are lists.
- If the method is not found, a `TypeCheckError` is raised to indicate that the method call cannot be located.

#### Type Checking

Type checking is conducted in the following steps:
- First, the following helper functions are called to initialise the type checking environment into an environment stack for the `MainClassNode` and `ClassDeclNode`, which is then propagated downwards to the child nodes:
  - `MainClassNode`:
    - `initialise_class_descriptor`: Initialises the class descriptor object for the main class
    - `_initialise_main_mds`: Initialise the `main` method signature
    - `_initialise_main_args`: Initialise the arguments for `main` method
    - `_initialise_main_vars`: Initialise the variable declarations for `main` method
  - `ClassDeclNode`:
    - `_initialise_local_environment`: Initialise the local environment for the class
- The `type_check` function is then called for the additional attributes of each derived nodes, before the child and sibling.
- The type information for a `ASTNode` is assigned using the helper function `_assign_identifier_type`. The initial type information associated during parsing is converted into the `BasicType` or `FunctionType` class. This is done by either traversing the environment stack for identifiers, or by converting the initial type information in string format.
  - For arguments and variable declarations, their type information are assigned using the helper function `_assign_declaration_type`.
- Once the type information has been assigned for the leaf nodes, the type checks are then executed. When a type check succeeds for a node, the corresponding type information is assigned. Otherwise, a `TypeCheckError` is raised.
- The check for return type is implemented by propagating the return type information as a parameter to the `type_check` function, and executing the check at a `ReturnNode`. If the return types do not match, a `TypeCheckError` is raised.

### Error handling

The following type checking errors will be raised:
- Two clases declared in a program have the same class name. The class name is identified in the error message.

  Example:
  ```
  jlite_type.TypeCheckError: Invalid type:  MainC. Class has the same name as an earlier declared class.
  ```
- Two methods declared in a class have the same name. The class with the error is identified in the error message.

  Example:
  ```
  jlite_type.TypeCheckError: Invalid type:  f. Method has the same name as an earlier declared method in class: [Functional]
  ```
- Two parameters in a method declarations have the same name. The parameter name, and the method and class which it is in, are identified in the error message.

  Example:
  ```
  jlite_type.TypeCheckError: Invalid type:  a. Argument has the same name as an earlier declared argument in method [orders] in class [OrderMacs]
  ```
- Two fields in a class have the same name. The class with the error is identified in the error message.

  Example:
  ```
  jlite_type.TypeCheckError: Invalid type:  a. Field has the same name as an earlier declared field in class: [Functional]
  ```
- Value assigned to a variable does not match the type declared. The variable name and the class declaration it is in are identified in the error message.

  Example:
  ```
  jlite_type.TypeCheckError: Invalid type:  j. Assigned value type [Bool] does not match declared identifier type [Int] in class [OrderMacs]
  ```
- Return type does not match that specified for the method. The class in which the method resides is identified in the error message, as well as the expected return type.

  Example:
  ```
  jlite_type.TypeCheckError: Invalid type:  true. Return type Bool is different from that declared for function in class [OrderMacs]: Int
  ```
- Arguments for an overloaded method call does not match the possible permutations. The method name and the class in which the method resides is identified in the error message.

  Example:
  ```
  jlite_type.TypeCheckError: Type check error:  fo.f. Unable to locate function in class [Functional] with parameter types: [<BasicType.INT: 'Int'>, <BasicType.BOOL: 'Bool'>]
  ```
- An overloaded method call with a different return type takes in the same argument types as an earlier declared method.

  Example:
  ```
  jlite_type.TypeCheckError: Type check error:  deliverOrder. Declared method in [Driver] with parameters [<BasicType.INT: 'Int'>] and return type String takes in the same parameter types as earlier method with the same name.
  ```

## IR3 Generator

The `ir3.py` file contains the following generic classes:
- `IR3Node`: Base node class to construct the IR3 tree. This is used to construct various heterogenous IR3 trees as further elaborated on in the next sub-section.
  - Unlike the `ASTNode` class, there is no `sibling` attribute to ensure correctness in the sequential chaining of instructions.
- `IR3Tree`: Custom IR3 tree class to point to the root node.

The `gen.py` file contains the following classes of objects:
- `IR3Generator`: IR3 generator class containing the main logic for converting the AST from the Parser into an IR3 tree.

The `symbol_table.py` file contains the following class:
- `SymbolTableStack`: A custom stack to manage symbol tables with the following functions -
  - `add_empty_st()`: Append an empty symbol table (a Dictionary) to the top of the stack
  - `pop_st()`: Pops the latest symbol table off the stack
  - `insert(value, type, temp_id, state)`: Insert a symbol into the symbol table currently at the top of the stack. The identifier (or value) is used as the key, and the value is a dictionary containing the type, current state, scope and the temporary identifier.
  - `lookup(value)`: Searches the entire symbol table stack, and returns a list containing the type, current state, scope and the temporary identifier if the identifier (or value) is found in the lookup table. Otherwise, return None.

### Design of IR3 Tree

The IR3 tree is composed of the base `IR3Node` class (which has a value and type, and points to a child) and its derived classes.

The following classes are derived from the `IR3Node` base class for specific statements and declarations:
- `Program3Node`: The declaration of a program
- `CData3Node`: The data for a class
- `CMtd3Node`: The method for a class
- `VarDecl3Node`: Variable declaration
- `Arg3Node`: Argument/parameter declaration
- `Label3Node`: Label instruction
- `IfGoTo3Node`: Compare and branch instruction
- `GoTo3Node`: Branch instruction
- `ReadLn3Node`: Read line operation
- `PrintLn3Node`: Print line operation
- `ClassInstance3Node`: Class instance
- `ClassAttribute3Node`: Class attribute
- `Assignment3Node`: Assignment operation
- `MethodCall3Node`: Method call
- `Return3Node`: Return statement
- `RelOp3Node`: Relational operator statement
- `BinOp3Node`: Binary operator statement
- `UnaryOp3Node`: Unary operator statement

The `pretty_print()` function prints the IR3 tree in a recursive manner by traversing from the root node. The generic `IR3Node` class will traverse its child (and sub-childs). For the derived classes, the `pretty_print()` function is modified to print the additional attributes attached to those classes.

### Construction of IR3 Tree

The `IR3Generator` contains the following helper functions:
- `_parse_content()`: Lexes and parses the input file.
- `_get_temp_var_count()`: Returns the count of temporary variables that have been created for the current program.
- `_create_new_label()`: Returns the count of labels that have been created for the current program.
- `_initialise_symbol_table()`: Helper function to set up the initialise the symbol table that will be passed down the AST.
- `_get_last_child(IR3Node)`: Helper function to get the last child of an `IR3Node`.
- `_compute_arithmetic_node_with_constants(ASTNode)`: Helper function to optimise the IR3 code by performing arithmetic operations with two constants directly. See the Built-in IR3 optimizations section below.
- `_compute_binop_node_with_constants(ASTNode)`: Helper function to optimise the IR3 code by performing binary operations with two constants directly. See the Built-in IR3 optimizations section below.
- `_compute_relop_node_with_constants(ASTNode)`: Helper function to optimise the IR3 code by performing relational operations with two constants directly. See the Built-in IR3 optimizations section below.
- `_derive_ifgoto_condition`: Helper function to derive the relational operator expression in the condition directly (where the operands are constants or identifiers), or the series of instructions, for 'if-else' and 'while' control structures.
- `_generate_ir3()`: Helper function to traverse the AST from the Parser and generate the IR3 tree.

The `generate_ir3()` function contains the main logic to construct the IR3 tree by traversing the AST generated by the Parser. The remaining helper functions correspond to expression set out in the IR3 grammer specified in Assignment 2.

The `_get_last_child` function is used to connect statements in the correct order where a subroutine is called. Where the destination of a `goto` statement is not known at the time of processing an expression, the label is first created and appended as a child to the last statement of the returned expression using this helper function.

The symbol table is initialised at the beginning of the program, and passed as a variable to each helper function to generate the IR3 nodes. Where appropriate, the addition and removal of the symbol table at the top of the stack is handled in the relevant helper functions for those IR3 nodes (e.g. if-else statement, while statement).

As the instructions generated by the IR3 generator are sequential, the helper functions that traverse AST nodes with Kleene's and positive closures has an optional parameter to include the top-level node for the current expression. Since the `Parser` generated statements in Kleene's and positive closures as siblings, these helper functions checks if the current AST node has a sibling. If yes, a recursive call is made to the current helper function to link the IR3 nodes for subsequent expressions to the latest IR3 node generated. When the recursive call is completed, the top IR3 node is returned.

### Built-in IR3 optimizations

1. Compute arithmetic, binary and relational operations with two constants directly

Where any of the above operations consists of two constants for both operands, the resulting value is computed by the code generator first. This reduces the number of temporary variables required, and the number of assembly code instructions.

For example, the statement `a = 3 + 5;` will compile to the following IR3 code without optimization:
```
Int _t1;
_t1 = 3;
Int _t2;
_t2 = 5;
Int _t3;
_t3 = _t1 + _t2;
```

With this optimization, the same statement will compile to the following IR3 code instead:
```
Int _t1;
_t1 = 8;
a = _t1;
```

## Compiler

The `compile.py` file contains the following generic classes:
- `Compiler`: Compiler object to generate assembly code from an input file by running the code through the Lexer, the Parser, the IR3Generator and the ControlFlowGenerator, and contains the main logic to convert the IR3 nodes into ARM assembly. If the optimization flag is present, the generated ARM assembly code is additionally run through the PeepholeOptimizer class.
- Code generation takes place in four main steps:
  - First, the IR3 tree is generated. The details of IR3 code generation is covered under the IR3 Generator section.
  - Next, the data flow for the IR3 tree is generated.
  - ARM assembly code is then generated from the IR3 code. If optimizations are enabled, the optimization passes will be additionally executed prior to assembly code generation (if they operate on IR3) or after (if they operate on assembly).
  - Lastly, the generated instructions are written to an output file.

The `instruction.py` file contains the base `Instruction` class for generating assembly code. For each line of instruction, a new `Instruction` object is instantiated and the instruction is stored as a string in the class attribute `assembly_code`.

The `control_flow.py` file contains the ControlFlowGenerator class, which helps to annotate the `IR3Node` class with additional information such as line number and basic block number. It also contains optimizations that operate on the IR3 format.

The `peephole_optimization.py` file contains the PeepholeOptimizer class, which performs peephole optimization on either IR3 or the generated ARM assembly code.

### Code Generation

Code generation is initiated on individual class methods represented as `CMtd3Node`, a class of `IR3Node` in the `_convert_cmtd3_to_assembly` helper function.
- Instructions for the method start and end labels are created.
- Instructions to push and restore the callee-saved registers to and from the stack at the start and end of the method respectively are created.
- The total space required on the stack to store all variable declarations are calculated, and the instruction to decrement the stack pointer by the required offset is generated.
- Statements are generated using the `_convert_stmt_to_assembly` helper function. Liveness data is retrieved and passed to this helper function for the purpose of subsequent register allocation.

As instructions may be inserted into the `.data` section of the assembly code, the `Compiler` class maintains a pointer to the tail of this section to enable instructions to be inserted while during code generation for statements.

### Converting IR3 nodes to assembly

Code generation is handled either directly or through the helper functions for the following IR3 nodes:
- `ReadLn3Node`: `_convert_readln_to_assembly()`
  - Only integers can be read in the current implementation. To initialise the reading of integers, two labels are created in the `.data` section to enable reading in the user input as a string and then storing it as an integer.
  - The value is then stored to the variable.
- `PrintLn3Node`: `_convert_println_to_assembly()`
  - The labels for the print statements are created in the `.data` section and read into a register at runtime.
  - To enable printing of boolean values, both `true` and `false` are pre-generated in the `.data` section as well.
- `Assignment3Node`: `_convert_assignment_to_assembly()`
  - Assignment statements are handled based on whether the assigned value is a raw value, a `ClassInstance3Node`, an `UnaryOp3Node`, a `BinOp3Node`, a `RelOp3Node`, a `MethodCall3Node` or a variable identifier.
  - Where the assignment is in the format of `x = y op z`, code generation will additionally depend on whether either `y` or `z` are raw values.
- `Return3Node`: `_convert_return_to_assembly()`
  - To enable early termination, the exit label of the method is passed as an argument to this helper function to enable the branch instruction to be created.
- `IfGoTo3Node`: `_convert_if_goto_statement_to_assembly()`
  - Code generation depends on whether the expression for the condition is an identifier, a base `IR3Node` or a `RelOp3Node`.
- `Label3Node:`: Instruction for labels are generated directly as they are trivial.
- `GoTo3Node`: Instruction for goto statements are generated directly as they are trivial.

`VarDecl3Node` are skipped as no instructions need to be generated from them directly.

### Get registers function

The `_get_registers()` helper function is called to retrieve which registers should be used for each variable in the current statement.
- Liveness data is initialised at the top level method using the    `_get_md_liveness_data` helper function. This helper function retrieves the live ranges of identifiers in the current method, which is subsequently used for the linear scan register allocation and to determine the spilling cost.

The `get_registers()` first makes a call to the `_get_required_registers()` function to determine the position of the operands and their associated identifiers. This returns a dictionary that maps from `x`, `y` and `z` to the respective identifiers. Implicitly, this determines how many registers are required for the current statement.

The function then loops through the dictionary obtained from `_get_required_registers()` function, and iterates through the key-value pairs to perform the following checks in sequence. If a register is obtained from any of them, the current iteration is terminated early.
- Check if the identifier is already in a register.
- Check if there is an empty register.
- Check if there is a register with a replaceable value.
- For each register, check if value in register is `y` in `x = y + z`, `y != z`, and it can be replaced.
- For each register, check if the value is not used subsequently.
- If a register is not obtained yet, spill a register. Spilling cost is determined based on the number of subsequent uses as calculated from the live range.

## Code optimization

All optimizations in this section are turned off by default. To enable these optimizations, use the `--optimize` flag.

Code optimization is executed in various passes:
- The `ControlFlowGenerator` class executes a pass on IR3 nodes when generating basic blocks.
- The `PeepholeOptimizer` class executes a pass on the generated ARM assembly code.

### IR3 Code Optimizations

The `ControlFlowGenerator` contains the following optimizations:
- During generation of control flow for IR3 nodes, integer constants are propagated and replaced. This is executed by the `_annotate_int_constants_and_propagate()` funtion in the `ControlFlowGenerator` class.

  Example:
  ```
  i = 12;
  ...
  println(i);
  ```

  Unoptimized:
  ```
  ldr a1,=d0
  ldr a2,[fp,#-28]
  bl printf
  ```

  Optimized:
  ```
  ldr a1,=d0
  mov a2,#12
  bl printf
  ```

- Algebraic identities are reduced by the `_optimize_algebraic_identities()` function.

  The following algebraic statements will evaluate to x:
  ```
  x + 0 = 0 + x = x
  x * 1 = 1 * x = x
  x - 0 = x
  ```

  Example:
  ```
  k = 3 + 5;
  j = k + 0;
  ```

  Unoptimized:
  ```
  add v4,v3,#0         // v3 = k, v4 = temporary variable
  ...
  mov v5,v4
  str v5,[fp,#-32]
  ```

  Optimized:
  ```
  mov v4,v3            // v3 = k, v4 = temporary variable
  mov v5,v4
  str v5,[fp,#-32]
  ```

### ARM Assembly Code Optimizations

- Peephole optimization of assembly code is executed by various helper functions in the `_peephole_optimize_assembly_pass` function of the `PeepholeOptimizer` class.
  - Redundant load instructions are removed by the `_eliminate_redundant_ldr_str()` function. This includes load instructions immediately after a store and load instructions separated by one instruction.

    Examples of redundant load instruction immediately after a store:
    ```
    str v1,[fp,#-12]
    ldr v1,[fp,#-12] // this instruction will be removed
    ```
    Example of a redundant load instruction separated by one instruction
    ```
    str v1,[fp,#-12]
    ldr v2,[fp,#-16]
    ldr v1,[fp,#-12] // this instruction will be removed
    ```

    Redundant load store instructions of argument registers are also removed.
    Example:
    ```
    bl printf
    ldmfd sp!,{a1,a2,a3,a4} // this instruction will be removed
    stmfd sp!,{a1,a2,a3,a4} // this instruction will be removed
    ldr a1,=d8
    mov a2,#0
    bl printf
    ```

  - Redundant move instructions are removed by the `_eliminate_redundant_mov()` function.

    Example of a redundant move instruction:
    ```
    mov v1,v1 // this instruction will be removed
    ```
  - Unreachable instructions after an unconditional branch are removed by the `_eliminate_unreachable_post_branch()` function.

    Example:
    ```
    b .L1Exit
    b .L1Start // this instruction will be removed
    ```
  - Redundant jump instructions to a label immediately following it are removed by the `_eliminate_jump_to_next_instruction()` function.

    Example:
    ```
    b .L1Exit // this instruction will be removed
    .L1Exit:
    ```

## Additional information

- For debugging purposes, the `Lexer`, `Parser`, `IR3Generator`, and `Compiler` classes contain a `debug` mode for verbose logging.

## Known Gaps
- Errors in Kleene's closure are not raised, and are discarded.

## Areas for improvement

- Use a stack to store consumed tokens for backtracking instead of creating a deep copy to reduce memory usage.
- Restore the environment stack at the end of a function instead of creating a deep copy to reduce memory usage.

## References
- [1] http://www1.cs.columbia.edu/~sedwards/classes/2003/w4115/ast.pdf
- [2] https://www.clear.rice.edu/comp212/02-fall/labs/11/
- [3] https://www.tutorialspoint.com/compiler_design/compiler_design_symbol_table.htm#:~:text=Among%20all%2C%20symbol%20tables%20are,the%20information%20about%20the%20symbol.
- [4] https://people.cs.umass.edu/~moss/610-slides/20.pdf
- [5] https://nptel.ac.in/content/storage2/courses/106108113/module5/Lecture17.pdf
- [6] https://runestone.academy/runestone/books/published/armTutorial/Functions/NestedCalls.html
