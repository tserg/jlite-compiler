import sys
import os

from collections import deque

from typing import (
    Any,
    Deque,
    List,
    Optional,
    Iterable
)

from lex_dfa import (
    DFA,
    FINAL_STATES,
    COMMENT_INTERMEDIATE_STATES,
    COMMENT_FINAL_STATES,
)

KEYWORDS = {
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
}

class Token:

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

    def __str__(self):

        return str((self.token_name, self.value))

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
        Returns the DFA classification of the current char
    add_token_to_queue(token)
        Add a token to the token queue
    get_next_token_from_queue()
        Removes the token at the start of the queue and returns it
    peek()
        Retrieve the token at the start of the queue without removing

    """

    token_queue: Deque[Token]

    def __init__(self) -> None:
        self.token_queue = deque()

    def _scan_next_char(
        self,
        current_state: str,
        new_char: str
    ) -> Optional[str]:
        # Checks if adding new_char results in a valid lexeme
        # Returns the new state if valid, otherwise None
        new_char_class = self._get_current_char_class(new_char)
        #print("Current char class: " + str(new_char_class))
        try:
            new_state = DFA[current_state][new_char_class]
            return new_state
        except:
            return None

    def _get_current_char_class(
        self,
        char: str
    ) -> Optional[str]:
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

        elif char in '-+/*=;&| .,"':
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

    def _analyse_lexeme(
        self,
        lexeme: str,
        lexeme_state: str,
        lexeme_start_index: int,
        lexeme_start_line: int
    ) -> Optional[Token]:
        # Checks if the given lexeme is a valid token
        # If yes, instantiate a new Token instance
        #print(lexeme)
        new_token = None

        if lexeme_state in ['1']:
            # Identifiers
            if lexeme in KEYWORDS:
                new_token = Token(lexeme, lexeme, lexeme_start_index, lexeme_start_line)
            else:
                new_token = Token('IDENTIFIER', lexeme, lexeme_start_index, lexeme_start_line)

        elif lexeme_state in ['2']:
            # Class names
            if lexeme in KEYWORDS:
                new_token = Token(lexeme, lexeme, lexeme_start_index, lexeme_start_line)
            else:
                new_token = Token('CLASS_NAME', lexeme, lexeme_start_index, lexeme_start_line)

        elif lexeme_state in ['5']:
            new_token = Token('INTEGER_LITERAL', lexeme, lexeme_start_index, lexeme_start_line)

        elif lexeme_state in ['11']:
            new_token = Token('STRING_LITERAL', lexeme, lexeme_start_index, lexeme_start_line)

        elif lexeme_state in ['3', '18', '19', '21', '23', '24', '35',]:
            # Operators
            new_token = Token(lexeme, lexeme, lexeme_start_index, lexeme_start_line)

        elif lexeme_state in ['13', '14', '15', '16', '17']:
            # Punctuation
            new_token = Token(lexeme, lexeme, lexeme_start_index, lexeme_start_line)

        return new_token

    def lex_content(self, f) -> None:

        index = 0
        line = 0

        # Store all lexemes
        lexemes = []

        # Current lexeme
        current_lexeme = ''
        current_lexeme_state = '0'
        current_lexeme_start_index = 0
        current_lexeme_start_line = 0
        previous_lexeme_state = None

        # Keep track of number of open multiline comment openings
        multiline_comment_count = 0

        token_list = []

        while True:
            current_char = f.read(1)
            #print("Current line: {}, Current index: {}".format(line, index))
            #print("Current lexeme start line: {}, Current lexeme start index: {}".format(current_lexeme_start_line, current_lexeme_start_index))
            if current_char == "\n":
                index = 0
                line += 1
            else:
                index += 1

            # Checks if there is any input
            if not current_char:

                # Add current lexeme to list if it is not empty and previous state is not a comment
                if current_lexeme != '':

                    if current_lexeme_state not in (COMMENT_INTERMEDIATE_STATES + COMMENT_FINAL_STATES):
                        lexemes.append(current_lexeme)
                        token = self._analyse_lexeme(current_lexeme, current_lexeme_state, current_lexeme_start_index, current_lexeme_start_line)
                        if token:
                            token_list.append(token)
                            self.add_token_to_queue(token)

                    elif current_lexeme_state in COMMENT_INTERMEDIATE_STATES:
                        sys.stdout.write("Error while lexing. Improperly paired multi-line comment found at index {} of line {}.\n" \
                        .format(current_lexeme_start_index, current_lexeme_start_line))

                lexemes.append('EOF')
                token_list.append(Token('KEYWORD', 'EOF', current_lexeme_start_index, current_lexeme_start_line))
                self.add_token_to_queue(Token('KEYWORD', 'EOF', current_lexeme_start_index, current_lexeme_start_line))
                break
            else:
                #print("Checking for char: " + current_char + " with current state " + current_lexeme_state)
                new_lexeme_state = self._scan_next_char(current_lexeme_state, current_char)
                #print("New lexeme state: " + str(new_lexeme_state))

                # Checks if adding new character results in a valid lexeme
                if new_lexeme_state:
                    current_lexeme += current_char
                    previous_lexeme_state = current_lexeme_state
                    current_lexeme_state = new_lexeme_state


                    # Check for nested multi-line comments and increment loop count
                    if current_lexeme_state == '27' and previous_lexeme_state == '26a' \
                        or current_lexeme_state == '26' and previous_lexeme_state == '24':
                        #print("Nested multiline detected")
                        #print("Previous state: " + previous_lexeme_state)
                        #print("Current state: " + current_lexeme_state)
                        multiline_comment_count += 1
                        #print("Nested multiline entered: " + str(multiline_comment_count))

                    # When multi-line comment is closed, decrement loop count
                    elif current_lexeme_state == '28' and previous_lexeme_state == '27':

                        #print("Nested multiline exited: " + str(multiline_comment_count))
                        multiline_comment_count -= 1
                        #print("Current nested comment loop count: " + str(multiline_comment_count))

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
                    if current_lexeme_state in FINAL_STATES and \
                        current_lexeme_state not in (COMMENT_FINAL_STATES + COMMENT_INTERMEDIATE_STATES):
                        # Add existing lexeme if it is a final state and not a comment
                        lexemes.append(current_lexeme)
                        token = self._analyse_lexeme(current_lexeme, current_lexeme_state, current_lexeme_start_index, current_lexeme_start_line)
                        if token:
                            token_list.append(token)
                            self.add_token_to_queue(token)
                        #print("Lexeme added: " + current_lexeme)

                    if previous_lexeme_state in COMMENT_INTERMEDIATE_STATES and current_lexeme_state not in COMMENT_FINAL_STATES:
                        #print(current_lexeme_start_line, current_lexeme_start_index)
                        sys.stdout.write("Error while lexing. Improperly paired multi-line comment found at index {} of line {}.\n" \
                        .format(current_lexeme_start_index, current_lexeme_start_line))
                    # Reset current lexeme state to 0
                    current_lexeme = current_char
                    current_lexeme_start_index = index
                    current_lexeme_start_line = line
                    previous_lexeme_state = None
                    current_lexeme_state = self._scan_next_char('0', current_char)

                    if current_lexeme_state == None:
                        # Reset current lexeme if it is invalid move from start state
                        current_lexeme = ''
                        current_lexeme_state = '0'

                        current_lexeme_start_index = index + 1

                #sys.stdout.write("Line " + str(line) + " index " + str(index) + " " + c + "\n")

        #print(lexemes)
    def add_token_to_queue(self, token: Token) -> None:
        self.token_queue.append(token)

    def get_next_token_from_queue(self) -> Token:
        return self.token_queue.popleft()

    def peek(self, count: int=0) -> Token:
        return self.token_queue[count]

    def is_empty(self) -> bool:
        return len(self.token_queue) == 0

def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        lex = Lexer()
        lex.lex_content(f)
        #token_list, lexemes = lex.lex_content(f)
        #sys.stdout.write(content)
        sys.stdout.write(str([token.__str__() for token in lex.token_queue]) + "\n")
        #sys.stdout.write(str(lexemes) + "\n")
        #sys.stdout.write(str(lex.token_queue))
        #sys.stdout.write("\n")
        #sys.stdout.write("\n")
        #sys.stdout.write(str(lex.token_queue.get()))
        sys.stdout.write(str(lex.is_empty()))

if __name__ == "__main__":

    __main__()
