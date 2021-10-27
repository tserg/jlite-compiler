import os
import sys

from gen import (
    IR3Generator
)

from typing import (
    Dict,
    List,
    TextIO,
)

from instruction import (
    Instruction,
)

class Compiler:
    """
    Compiler instance to generate ARM assembly code from input file
    ...

    Attributes
    ----------
    ir3_generator: IR3Generator
    address_descriptor: Dict[str, List[str]]
    register_descriptor: Dict[str, List[str]]

    Methods
    -------
    _parse_content(f)
        Run the parser through the given file

    """
    ir3_generator: "IR3Generator"
    address_descriptor: Dict[str, List[str]]
    register_descriptor: Dict[str, List[str]]
    instructions: "Instruction"

    def __init__(
        self,
        debug: bool=False
    ) -> None:
        self.ir3_generator = IR3Generator()
        self.debug = debug
        self.address_descriptor = {}
        self.register_descriptor = {}

    def _convert_ir3_to_assembly(self, ir3_tree: "IR3Tree") -> None:

        self.address_descriptor = {}
        self.register_descriptor = {}

        self.instructions = Instruction(1)
        self.instructions.set_instruction("Hello!")

    def _compile(self, f: TextIO) -> None:
        """
        Lexes, parses, type checks the input file, then generates
        the IR3 tree.

        :param TextIO f: the input file
        """
        self.ir3_generator.generate_ir3(f)
        self._convert_ir3_to_assembly(self.ir3_generator.ir3_tree)

        self.instructions.pretty_print()

    def compile(self, f: TextIO) -> None:
        self._compile(f)


def __main__():

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        sys.stdout.write("File does not exist.\n")

    elif not filepath.endswith('.j'):
        sys.stdout.write("Invalid file provided. "
            "Please check the file name or extension.\n")

    else:
        f = open(filepath, 'r')
        c = Compiler(debug=True)
        c.compile(f)

if __name__ == "__main__":

    __main__()
