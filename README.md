# bachelor-thesis-project
A general purpose programming language natively supporting LLM querying. My bachelor's thesis project.

Use

```
cd tree-sitter-haibara
tree-sitter generate --abi 14
tree-sitter build
pip install .
```

to build the parser and wrap it into a python package. The `--abi 14` argument is indespensible because the python binding of tree-sitter does not support the version 15 ABI, which is the default of the version 0.24.0 tree-sitter. It lacks even scarce seriousness to make the ABI and API vary to such a tremendous extent while providing NO related information in your documentation!
