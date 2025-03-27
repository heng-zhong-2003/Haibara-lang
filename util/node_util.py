from tree_sitter import Node
from colorama import Fore, Style

def find_child_by_type(input_node: Node, input_type: str) -> Node | None:
    """
    Returns the first child of `input_node` with node kind `input_type`.
    If no such child found, returns `None`.
    """
    for child in input_node.children:
        if child.type != None and child.type == input_type:
            return child
    return None

def read_node_text(input_node: Node) -> str:
        if (not input_node) or (not input_node.text):
            print(f'{Fore.RED}None node or empty text{Fore.RESET}')
            return ''
        return str(input_node.text, 'utf8')

