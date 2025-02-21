import os
import sys
from os import path
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_haibara_parser

HAIBARA_LANGUAGE = Language(tree_sitter_haibara_parser.language())
parser = Parser(HAIBARA_LANGUAGE)
source_code = 'hello'
tree = parser.parse(bytes(source_code, 'utf8'))
print(tree.root_node)
