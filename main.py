import os
import sys
from os import path
from pathlib import Path
import tree_sitter
from tree_sitter import Tree, Language, Parser
import tree_sitter_haibara_parser
from frontend.cst_to_gir import TransHaibara
# import pprint

HAIBARA_LANGUAGE = Language(tree_sitter_haibara_parser.language())
parser = Parser(HAIBARA_LANGUAGE)
source_code = r'''print(a);
let a : String = b;
let s : Session = construct_session (gpt);
query s with q"aaa {let x:String} bbb {let y:String}" requires (a&&b) role user;'''
# print(source_code)
# source_code = '(a)'
tree: Tree = parser.parse(bytes(source_code, 'utf8'))
trans = TransHaibara()
gir = []
trans.trans_source_file(tree.root_node, gir)
# print(tree.root_node)
print(gir)
