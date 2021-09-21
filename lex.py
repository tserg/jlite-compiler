import sys
import os

from collections import (
    deque,
)

from typing import (
    Any,
    Deque,
    List,
    Optional,
    Iterable,
    TextIO,
    Tuple,
)

from lex_dfa import (
    DFA,
    FINAL_STATES,
    FINAL_STATE_TO_TOKEN_NAME,
    COMMENT_INTERMEDIATE_STATES,
    COMMENT_FINAL_STATES,
)

KEYWORDS: List[str] = [
    'if',
    'else',
    'while',
    'main',
    'true',
    'false',
    'this',
    'return',
    'readln',
    'println',
    'Void',
    'String',
    'Bool',
    'Int',
    'null',
    'new',
    'class',
    'EOF'
]

class LexError(Exception):
    """
    Exception class for errors encountered while lexing

    ...

    Attributes
    ----------
    expression: str
    message: str

    """

    expression: str
    message: str

    def __init__(self, expression: str='') -> None:
        self.expression = expression
        self.message = "Unable to lex expression: "

    def __str__(self) -> str:

        return f'{self.message} {self.expression}'

class Token:
    """
    Token class for lexemes derived

    ...

    Attributes
    ----------
    token_name: str
    value: str
    start_index: int
    start_line: int

    """

    token_name: str
    value: str
    start_index: int
    start_line: int

    def __init__(
        self,
        token_name: str,
        value: str,
        start_index: int,
        start_line: int
    ) -> None:
        self.token_name = token_name
        self.value = value
        self.start_index = start_index
        self.start_line = start_line

    def __str__(self) -> str:

        return str(
            (
                self.token_name,
                self.value,
                self.start_line,
                self.start_index
            )
        )

class Lexer:
    """
    Lexer instance to read code from file and convert into tokens

    ...

    Attributes
    ----------
    token_queue : Deque[Token]

    Methods
    -------
    _get_current_char_class(char)
        Returns the DFA classification of the current character
    _get_next_state(current_state, new_char)
        Returns the next state to traverse to based on the input character and the
        current state in the DFA
    _tokenise_lexeme(lexeme, lexeme_state, lexeme_start_index, lexeme_start_line)
        Tokenises a lexeme if it is in a final state in the DFA
    lex_content(f)
        Lexes the input file
    _add_token_to_queue(token)
        Add a token to the token queue
    get_next_token_from_queue()
        Removes the token at the start of the queue and returns it
    get_last_consumed_token()
        Returns the last token that was removed from the queue
    peek()
        Retrieve the token at the start of the queue without removing
    is_empty()
        Checks if the token queue is empty
    get_tokens()
        Returns a string of tokens derived from the lexer in chronological order
        and separated by line breaks
    """

    token_queue: Deque[Token]
    last_consumed: Token
    debug: bool

    def __init__(self, debug: bool=False) -> None:
        self.token_queue = deque()
        self.debug = debug

    def _get_current_char_class(
        self,
        char: str
    ) -> Optional[str]:
        """
        Helper function to read a character and determine the key to traverse on
        for the DFA from the current state

        :param str char: the character to read
        :return: the key to traverse to based on the current state in the DFA
        """
        # Returns class of current char

        if char in 'abcdefnrtx':
            return char

        if char in 'ABCDEF':
            return char

        if char in 'ghijklmopqsuvwyz':
            return 'g-z_nrtx'

        elif char in 'GHIJKLMNOPQRSTUVWXYZ':
            return 'G-Z'

        elif char in '0123456789':
            return '0-9'

        elif char in '-+/*=;&| .,"_':
            return char

        elif char == '\\':
            return char

        elif char in '<>!':
            return '<>!'

        elif char == '\n':
            return '\n'

        elif char in '()':
            return '()'

        elif char in '{}':
            return '{}'

        elif char == "'":
            return char

        elif char == "	":
            return char

        return None

    def _get_next_state(
        self,
        current_state: str,
        new_char: str
    ) -> Any:
        """
        Helper function to read a character and determine the new state to
        go to from the current state in the DFA

        :param str current_state: the current state in the DFA
        :param str new_char: the character to read
        :return: the key to traverse to based on the current state in the DFA
        """
        # Checks if adding new_char results in a valid lexeme
        # Returns the new state if valid, otherwise None
        new_char_class = self._get_current_char_class(new_char)

        if self.debug:
            sys.stdout.write("Current char class: " + str(new_char_class) + "\n")
        try:
            new_state = DFA[current_state][new_char_class]
            return new_state

        except:
            return None

    def _tokenise_lexeme(
        self,
        lexeme: str,
        lexeme_state: str,
        lexeme_start_index: int,
        lexeme_start_line: int
    ) -> Optional[Token]:
        """
        Helper function to tokenise a lexeme

        :param str lexeme: the current lexeme
        :param str lexeme_state: the current state in the DFA
        :param int lexeme_start_index: the start index of the lexeme
        :param int lexeme_start_line: the start line of the lexeme
        :return: a Token instance of the lexeme
        """
        # Checks if the given lexeme is a valid token
        # If yes, create a new Token instance
        #print(lexeme)
        new_token = None

        if lexeme_state in ['1']:
            # Identifiers
            if lexeme in KEYWORDS:
                new_token = Token(
                    lexeme,
                    lexeme,
                    lexeme_start_index,
                    lexeme_start_line
                )

            else:
                new_token = Token(
                    'IDENTIFIER',
                    lexeme,
                    lexeme_start_index,
                    lexeme_start_line
                )

        elif lexeme_state in ['2']:
            # Class names
            if lexeme in KEYWORDS:
                new_token = Token(
                    lexeme,
                    lexeme,
                    lexeme_start_index,
                    lexeme_start_line
                )

            else:
                new_token = Token(
                    'CLASS_NAME',
                    lexeme,
                    lexeme_start_index,
                    lexeme_start_line
                )

        elif lexeme_state in ['5']:
            # Integer literals
            new_token = Token(
                'INTEGER_LITERAL',
                lexeme,
                lexeme_start_index,
                lexeme_start_line
            )

        elif lexeme_state in ['11']:
            # String literals
            new_token = Token(
                'STRING_LITERAL',
                lexeme,
                lexeme_start_index,
                lexeme_start_line
            )

        elif lexeme_state in [
            '3', '13', '14', '16', '17', '18', '19', '21', '23', '24', '35',
        ]:
            # Operators
            #token_name = FINAL_STATE_TO_TOKEN_NAME[lexeme_state][lexeme]
            new_token = Token(
                lexeme,
                lexeme,
                lexeme_start_index,
                lexeme_start_line
            )

        elif lexeme_state in ['13', '14', '16', '17']:
            # Punctuation

            new_token = Token(
                lexeme,
                lexeme,
                lexeme_start_index,
                lexeme_start_line
            )

        return new_token

    def _add_token_to_queue(self, token: Token) -> None:
        """
        Add a token to the Lexer's queue

        :param Token token: the token to be added to the queue
        """
        self.token_queue.append(token)

    def lex_content(self, f: TextIO) -> None:
        """
        Lexes the input file

        :param TextIO f: the input file
        """

        completed = False

        index = 1
        line = 1

        # Current lexeme
        current_lexeme = ''
        current_lexeme_state = '0'
        current_lexeme_start_index = 1
        current_lexeme_start_line = 1
        previous_lexeme = ''
        previous_lexeme_state = None

        # Keep track of number of open multiline comment openings
        multiline_comment_count = 0


        while not completed:

            # While file still has input, read the next character
            current_char = f.read(1)

            if self.debug:
                sys.stdout.write("Previous lexeme: " + previous_lexeme + "\n")
                sys.stdout.write("Previous lexeme state: " + str(previous_lexeme_state) + "\n")
                sys.stdout.write("Current line: {}, Current index: {}"
                    .format(line, index) + "\n")

                sys.stdout.write(
                    ("Current lexeme start line: {}, "
                    "Current lexeme start index: {}")
                    .format(
                        current_lexeme_start_line,
                        current_lexeme_start_index
                    )  + "\n"
                )

            # Update current position of lexer
            if current_char == "\n":

                if self.debug:
                    sys.stdout.write("New line detected. Previous lexeme: " + previous_lexeme + "\n")

                index = 1
                line += 1
            else:
                index += 1

            # Checks if there is any input
            if not current_char:

                # Add current lexeme to list if it is not empty and
                # previous state is not a comment

                if current_lexeme_state not in (
                    COMMENT_INTERMEDIATE_STATES + \
                    COMMENT_FINAL_STATES
                ):

                    token = self._tokenise_lexeme(
                        current_lexeme,
                        current_lexeme_state,
                        current_lexeme_start_index,
                        current_lexeme_start_line
                    )

                    if token:
                        self._add_token_to_queue(token)

                elif current_lexeme_state in COMMENT_INTERMEDIATE_STATES:

                    raise LexError(
                        ("Improperly paired multi-line comment found at "
                        "index {} of line {}.\n"
                        ).format(
                            current_lexeme_start_index,
                            current_lexeme_start_line
                        )
                    )

                self._add_token_to_queue(Token(
                    'KEYWORD',
                    'EOF',
                    current_lexeme_start_index,
                    current_lexeme_start_line
                ))

                # Exit while loop on end of file
                completed = True

            else:
                if self.debug:
                    sys.stdout.write("Checking for char: " + current_char + \
                        " with current state " + current_lexeme_state + "\n")

                new_lexeme_state = self._get_next_state(
                    current_lexeme_state,
                    current_char
                )

                if self.debug:
                    sys.stdout.write("New lexeme state: " + \
                        str(new_lexeme_state) + "\n")

                # Checks if adding new character results in a valid lexeme
                if new_lexeme_state:
                    current_lexeme += current_char
                    previous_lexeme_state = current_lexeme_state
                    current_lexeme_state = new_lexeme_state


                    # Check for nested multi-line comments and
                    # increment loop count
                    if (current_lexeme_state == '27' and \
                        previous_lexeme_state == '26a') or \
                        (current_lexeme_state == '26' and \
                        previous_lexeme_state == '24'):

                        if self.debug:
                            sys.stdout.write("Nested multiline detected" + "\n")
                            sys.stdout.write("Previous state: " + \
                                previous_lexeme_state + "\n")
                            sys.stdout.write("Current state: " + \
                                current_lexeme_state + "\n")
                        multiline_comment_count += 1

                        if self.debug:
                            sys.stdout.write("Nested multiline entered: " + \
                                str(multiline_comment_count) + "\n")

                    # When multi-line comment is closed, decrement loop count
                    elif current_lexeme_state == '28' and \
                        previous_lexeme_state == '27':

                        if self.debug:
                            sys.stdout.write("Nested multiline exited: " + \
                                str(multiline_comment_count) + "\n")

                        multiline_comment_count -= 1

                        if self.debug:
                            sys.stdout.write(
                                "Current nested comment loop count: " + \
                                str(multiline_comment_count) + "\n"
                            )

                        # Checks if closed multi-line comment was nested
                        if multiline_comment_count > 0:
                            # Reset current and previous lexeme states
                            # to multi-line comment start state
                            current_lexeme_state = '26'
                            previous_lexeme_state = '26'


                # Otherwise, add current lexeme if it is in a final state
                # and set current lexeme to current character.

                # If adding new character results in invalid lexeme
                else:

                    if current_lexeme_state in COMMENT_FINAL_STATES:
                        # Set previous lexeme to current lexeme if
                        # current lexeme is a comment and update previous
                        # lexeme state
                        previous_lexeme = current_lexeme
                        previous_lexeme_state = current_lexeme_state

                    if current_lexeme_state in FINAL_STATES and \
                        current_lexeme_state not in (COMMENT_FINAL_STATES + \
                            COMMENT_INTERMEDIATE_STATES):
                        # Add existing lexeme if it is a final state and
                        # not a comment

                        token = self._tokenise_lexeme(
                            current_lexeme,
                            current_lexeme_state,
                            current_lexeme_start_index,
                            current_lexeme_start_line
                        )

                        if token:
                            self._add_token_to_queue(token)

                            # Set previous lexeme to current lexeme and
                            # update previous lexeme state
                            previous_lexeme = current_lexeme
                            previous_lexeme_state = current_lexeme_state

                        if self.debug:
                            sys.stdout.write("Lexeme added: " + current_lexeme + "\n")

                    if previous_lexeme_state in COMMENT_INTERMEDIATE_STATES and \
                        current_lexeme_state not in COMMENT_FINAL_STATES:
                        # Raise error if current lexeme is a multiline comment
                        # improperly closed

                        raise LexError(
                            ("Improperly paired multi-line comment found at "
                            "index {} of line {}.\n"
                            ).format(
                                current_lexeme_start_index,
                                current_lexeme_start_line
                            )
                        )

                    # Reset current lexeme trackers only
                    # Previous lexeme should not be updated because current
                    # char/lexeme is invalid
                    current_lexeme = current_char
                    current_lexeme_start_index = index
                    current_lexeme_start_line = line

                    current_lexeme_state = self._get_next_state('0', current_char)

                    if not current_lexeme_state:
                        # Reset current lexeme if it is invalid move
                        #from start state
                        current_lexeme = ''
                        current_lexeme_state = '0'

                        current_lexeme_start_index = index

                    if current_char == "\n" and \
                        (previous_lexeme not in [';', '{', '}'] and \
                        previous_lexeme_state not in COMMENT_FINAL_STATES):
                        # Raise an error if a statement is missing a semicolon

                        raise LexError(
                            "Missing semicolon for statement at line {}.\n"
                            .format(current_lexeme_start_line-1)
                        )

    def get_next_token_from_queue(self) -> Token:
        """
        Pops the next token from the Lexer's queue and return the value.
        The last consumed token is updated to the popped token.

        :return The token on the left of the Lexer's queue
        """
        next_token = self.token_queue.popleft()
        self.last_consumed = next_token
        return next_token

    def get_last_consumed_token(self) -> Token:
        """
        Returns the last consumed token.

        :return The token that was last removed from the left of the Lexer's queue
        """
        return self.last_consumed

    def peek(self, count: int=0) -> Token:
        """
        Reads the next token from the Lexer's queue and return the value without popping.

        :return The token on the left of the Lexer's queue
        """
        return self.token_queue[count]

    def is_empty(self) -> bool:
        """
        Checks if the Lexer's queue is empty

        :return Boolean value for whether Lexer's queue is empty
        """
        return len(self.token_queue) == 0

    def get_tokens(self) -> str:
        """
        Returns all tokens in the Lexer's queue as a string, with each token
        separated by a line break.

        :return A string of token values
        """
        tokens = "".join([token.__str__() + "\n" for token in self.token_queue])
        return tokens

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. \
            Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        lex = Lexer(debug=False)
        lex.lex_content(f)

        sys.stdout.write(lex.get_tokens())

if __name__ == "__main__":

    __main__()
