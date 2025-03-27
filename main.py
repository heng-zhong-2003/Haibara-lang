import os
import sys
from os import path
from pathlib import Path
import tree_sitter
from tree_sitter import Tree, Language, Parser
import tree_sitter_haibara_parser
from frontend.cst_to_gir import TransHaibara
from interpret.interpreter import Interpreter
from colorama import Fore, Style
# import pprint

HAIBARA_LANGUAGE = Language(tree_sitter_haibara_parser.language())
parser = Parser(HAIBARA_LANGUAGE)
source_code = r'''
let s : Session = construct_session (zhipu);
query s with q"The reason that some audience think there is a romantic relation between Conan and Ai Haibara is {let reason:String}";
print(reason);
query s with q"Two essential properties that have to be verified to prove the type safety of a programming language is {let cond1:String} and {let cond2:String}.";
print(cond1);
print(cond2);
query s with q"I think they should be progress and preservation. So answer me again: the two conditions are {let c1:String} and {let c2:String}."
print(c1);
print(c2);
'''

source_code = r'''
let s : Session = construct_session (zhipu);
let format_req : String = "Do not include any other characters other then the json in your reply";
query s with q"Write for me a quicksort in c: {let qs:String}. You have to wrap the c code in a json \
field named `qs`. {format_req}.";
print(qs);
query s with q"Suppose this program is saved to file `qk.c`, then a `CMakeLists.txt` that can build \
this program is {let cmk:String}. My environment is Ubuntu 22.01, using GCC and cmake. You have to wrap \
the command in a json field named `cmk`. {format_req}.";
print(cmk);
'''

tree: Tree = parser.parse(bytes(source_code, 'utf8'))
trans = TransHaibara()
print(f'{Fore.GREEN}---- Concrete Syntax Tree ---{Style.RESET_ALL}')
print(tree.root_node)
gir: list[TransHaibara.GIRCommand] = []
trans.trans_source_file(tree.root_node, gir)
print(f'{Fore.GREEN}---- GIR statements ----{Style.RESET_ALL}')
print(gir)
interp = Interpreter()
interp.interp(gir)
