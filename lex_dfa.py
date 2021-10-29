from typing import (
    Any,
    Dict,
    List,
)

DFA: Dict[str, Any] = {
    '0': {
    # Start state
        'g-z_nrtx': '1',
        'G-Z': '2',
        'a': '1',
        'b': '1',
        'c': '1',
        'd': '1',
        'e': '1',
        'f': '1',
        'n': '1',
        'r': '1',
        't': '1',
        'x': '1',
        'A': '2',
        'B': '2',
        'C': '2',
        'D': '2',
        'E': '2',
        'F': '2',
        '-': '3',
        '+': '35',
        '*': '35',
        '"': '4',
        '0-9': '5',
        ';': '13',
        ',': '14',
        '.': '14',
        'newline': '15',
        '{}': '16',
        '()': '17',
        '<>!': '18',
        '=': '18',
        '&': '20',
        '|': '22',
        '/': '24',
    },
    '1': {
    # Identifier start state
        'g-z_nrtx': '1',
        'G-Z': '1',
        'a': '1',
        'b': '1',
        'c': '1',
        'd': '1',
        'e': '1',
        'f': '1',
        'n': '1',
        'r': '1',
        't': '1',
        'x': '1',
        'A': '1',
        'B': '1',
        'C': '1',
        'D': '1',
        'E': '1',
        'F': '1',
        '0-9': '1',
        '_': '1'
    },
    '2': {
    # Class name start state
        'g-z_nrtx': '2',
        'G-Z': '2',
        'a': '2',
        'b': '2',
        'c': '2',
        'd': '2',
        'e': '2',
        'f': '2',
        'n': '2',
        'r': '2',
        't': '2',
        'x': '2',
        'A': '2',
        'B': '2',
        'C': '2',
        'D': '2',
        'E': '2',
        'F': '2',
        '0-9': '2',
        '_': '2'
    },
    # Negative integer start state
    '3': {},
    '4': {
    # String start state
        '"': '11',
        '\\': '6',
        'g-z_nrtx': '8',
        'G-Z': '8',
        'a': '8',
        'b': '8',
        'c': '8',
        'd': '8',
        'e': '8',
        'f': '8',
        'n': '8',
        'r': '8',
        't': '8',
        'x': '8',
        'A': '8',
        'B': '8',
        'C': '8',
        'D': '8',
        'E': '8',
        'F': '8',
        '0-9': '8',
        '-': '8',
        '+': '8',
        '*': '8',
        '/': '8',
        '=': '8',
        '_': '8',
        ' ': '8',
        '	': '8',
        '<>!': '8',
        '()': '8',
        '{}': '8',
        ';': '8',
        '&': '8',
        '|': '8',
        '.': '8',
        ',': '8',
        '"': '8',
        "'": '8',
    },
    '5': {
    # Integer start state
        '0-9': '5'
    },
    '6': {
    # Escaped string start state
        '\\': '7',
        'n': '8',
        'r': '7',
        't': '7',
        'b': '7',
        'x': '12',
        '0-9': '9',
        '"': '7'
    },
    '7': {
        " ": '4',
        '\\': '6' ,
        '"': '11',
    },
    '8': {
    # Normal string start state
        '"': '11',
        '\\': '6',
        'g-z_nrtx': '8',
        'G-Z': '8',
        'a': '8',
        'b': '8',
        'c': '8',
        'd': '8',
        'e': '8',
        'f': '8',
        'n': '8',
        'r': '8',
        't': '8',
        'x': '8',
        'A': '8',
        'B': '8',
        'C': '8',
        'D': '8',
        'E': '8',
        'F': '8',
        '0-9': '8',
        '-': '8',
        '+': '8',
        '*': '8',
        '/': '8',
        '=': '8',
        '_': '8',
        ' ': '8',
        '	': '8',
        '<>!': '8',
        '()': '8',
        '{}': '8',
        ';': '8',
        '&': '8',
        '|': '8',
        '.': '8',
        ',': '8',
        "'": '8',
        ":": '8',
    },
    '9': {
        '0-9': '29',
    },
    '10': {
        '0-9': '10',
        ' ': '4',
        '	': '4',
    },
    '11': {},
    '12': {
        '0-9': '32',
        'a': '32',
        'b': '32',
        'c': '32',
        'd': '32',
        'e': '32',
        'f': '32',
        'A': '32',
        'B': '32',
        'C': '32',
        'D': '32',
        'E': '32',
        'F': '32',
    },
    '13': {},
    '14': {},
    '15': {},
    '16': {},
    '17': {},
    '18': {
        '=': '19'
    },
    '19': {},
    '20': {
        '&': '21'
    },
    '21': {},
    '22': {
        '|': '23'
    },
    '23': {},
    '24': {
        '/': '25',
        '*': '26'
    },
    '25': {
    # Single-line comment
        'g-z_nrtx': '25',
        'G-Z': '25',
        'a': '25',
        'b': '25',
        'c': '25',
        'd': '25',
        'e': '25',
        'f': '25',
        'n': '25',
        'r': '25',
        't': '25',
        'x': '25',
        'A': '25',
        'B': '25',
        'C': '25',
        'D': '25',
        'E': '25',
        'F': '25',
        '0-9': '25',
        '-': '25',
        '+': '25',
        '*': '25',
        '/': '25',
        '\\': '25',
        '=': '25',
        '_': '25',
        ' ': '25',
        '	': '25',
        '<>!': '25',
        '()': '25',
        '{}': '25',
        ';': '25',
        '&': '25',
        '|': '25',
        '.': '25',
        ',': '25',
        '"': '25',
        "'": '25',
        ":": '25',
    },
    '26': {
    # Multi-line comment
        'g-z_nrtx': '26',
        'G-Z': '26',
        'a': '26',
        'b': '26',
        'c': '26',
        'd': '26',
        'e': '26',
        'f': '26',
        'n': '26',
        'r': '26',
        't': '26',
        'x': '26',
        'A': '26',
        'B': '26',
        'C': '26',
        'D': '26',
        'E': '26',
        'F': '26',
        '0-9': '26',
        '-': '26',
        '+': '26',
        '*': '27',
        '/': '26a',
        '\\': '26',
        '=': '26',
        '_': '26',
        ' ': '26',
        '	': '26',
        '<>!': '26',
        '()': '26',
        '{}': '26',
        ';': '26',
        '&': '26',
        '|': '26',
        '.': '26',
        ',': '26',
        '"': '26',
        "'": '26',
        '\n': '26',
        ':': '26',
    },
    '26a': {
    # '/' within a multi-line comment
        'g-z_nrtx': '26',
        'G-Z': '26',
        'a': '26',
        'b': '26',
        'c': '26',
        'd': '26',
        'e': '26',
        'f': '26',
        'n': '26',
        'r': '26',
        't': '26',
        'x': '26',
        'A': '26',
        'B': '26',
        'C': '26',
        'D': '26',
        'E': '26',
        'F': '26',
        '0-9': '26',
        '-': '26',
        '+': '26',
        '*': '27',
        '/': '26',
        '\\': '26',
        '=': '26',
        '_': '26',
        ' ': '26',
        '	': '26',
        '<>!': '26',
        '()': '26',
        '{}': '26',
        ';': '26',
        '&': '26',
        '|': '26',
        '.': '26',
        ',': '26',
        '"': '26',
        "'": '26',
        '\n': '26',
        ':': '26',
    },
    '27': {
        'g-z_nrtx': '26',
        'G-Z': '26',
        'a': '26',
        'b': '26',
        'c': '26',
        'd': '26',
        'e': '26',
        'f': '26',
        'n': '26',
        'r': '26',
        't': '26',
        'x': '26',
        'A': '26',
        'B': '26',
        'C': '26',
        'D': '26',
        'E': '26',
        'F': '26',
        '0-9': '26',
        '-': '26',
        '+': '26',
        '*': '27',
        '/': '28',
        '\\': '26',
        '=': '26',
        '_': '26',
        ' ': '26',
        '	': '26',
        '<>!': '26',
        '()': '26',
        '{}': '26',
        ';': '26',
        '&': '26',
        '|': '26',
        '.': '26',
        ',': '26',
        '"': '26',
        "'": '26',
        '\n': '26',
        ":": '26',
    },
    '28': {},
    '29': {
        '0-9': '30'
    },
    '30': {
        ' ': '30',
        '	': '30',
        '"': '11',
        '\\': '31',
    },
    '31': {
        '0-9': '9'
    },
    '32': {
        '0-9': '33',
        'a': '33',
        'b': '33',
        'c': '33',
        'd': '33',
        'e': '33',
        'f': '33',
        'A': '33',
        'B': '33',
        'C': '33',
        'D': '33',
        'E': '33',
        'F': '33',
    },
    '33': {
        '\\': '34',
        '"': '11',
        ' ': '33',
        '   ': '33',
    },
    '34': {
        'x': '12'
    },
    '35': {}

}

FINAL_STATES: List[str] = [
    '1', # Identifer
    '2', # Class name
    '3', # Negative operator
    '5', # Integer literal
    '11', # String literal
    '13', # Punctuation ";"
    '14', # Punctuation ".,"
    #'15', # New line
    '16', # Puncutation "{}"
    '17', # Punctuation "()"
    '18', # Operators "<>!="
    '19', # Boolean operators "<= >= != =="
    '21', # Operator "&&"
    '23', # Operator "||"
    '24', # Operator "/"
    '25', # Single line comment
    '28', # Multi-line comment
    '35', # Operator '+*'
]

COMMENT_INTERMEDIATE_STATES: List[str] = ['26', '26a', '27']
COMMENT_FINAL_STATES: List[str] = ['25', '28']
