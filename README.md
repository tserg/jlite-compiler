# CS4212 Project Assignment 1 [AY2021/2022 Semester 2]

- Name: Tse Rong Gary
- Student ID: A0110500L

## Introduction

The directory comprises the following files:
```
jlite-compiler
 ├── lib/                     # Other files
     └── Grammar.pdf          # File containing rewritten grammar
 ├── test/                    # Test cases
 ├── ast.py                   # Parse tree class
 ├── lex_dfa.py               # DFA for lexer
 ├── lex.py                   # Lexer class
 ├── parse.py                 # Parser class
 └── TseRongGary_pa1_readme.md
```

Notes
- The rewritten grammar is set out in `lib/Grammar.pdf`.
- Test cases are in `test\`
- The remaining files are further described in the Lexer and Parser sections of this readme.

## Dependencies

- Python 3.8.10

## Running on local environment

1. To lex a file, run `python lex.py [FILE_NAME].j`
2. To parse a file, run `python parse.py [FILE_NAME].j`

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
- `AssignmentNode`: Assignment operation
- `InstanceNode`: Reference to an instance
- `ClassInstanceNode`: Declaration of a new object of a class
- `ReturnNode`: Return statement
- `IfElseNode`: If/else expression
- `WhileNode`: While expression
- `ReadLnNode`: Read line operation
- `PrintLnNode`: Print line operation
- `ExpListNode`: Expression list
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

## Additional information

- For debugging purposes, both the `Lexer` and `Parser` classes contain a `debug` mode for verbose logging.

## Known Gaps
- Errors in Kleene's closure are not raised, and are discarded.

## Areas for improvement

- Use a stack to store consumed tokens for backtracking instead of creating a deep copy to reduce memory usage.

## References
- http://www1.cs.columbia.edu/~sedwards/classes/2003/w4115/ast.pdf
- https://www.clear.rice.edu/comp212/02-fall/labs/11/
