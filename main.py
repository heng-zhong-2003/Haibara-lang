import os
import sys
from os import path
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_haibara_parser
# import pprint

HAIBARA_LANGUAGE = Language(tree_sitter_haibara_parser.language())
parser = Parser(HAIBARA_LANGUAGE)
source_code = r'''let a : String = b;
let s : Session = construct_session gpt;
query s with q"aaa {let x:String} bbb {let y:String}" requires b role user;'''
# print(source_code)
tree = parser.parse(bytes(source_code, 'utf8'))
print(tree.root_node)
