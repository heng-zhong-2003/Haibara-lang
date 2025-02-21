/**
 * @file A parser for the Haibara LLM query language
 * @author Heng Zhong
 * @license GPL-3.0
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: "haibara_parser",

  rules: {
    // TODO: add the actual grammar rules
    source_file: $ => "hello",
    query: $ => seq(
      'query',
      '{',
      $.format_str,
      '}'
    ),
    format_str: $ => seq(
      'f',
      '"',
      repeat(
        choice(
          seq('{', $.decl, '}'),
          token(/.*/)
        )
      ),
      '"'
    ),
    decl: $ => seq(
      'let',
      $.identifier, // Name of variable declared
      ':',
      $.identifier  // Type of variable declared
    ),
    identifier: $ => token(/[a-zA-Z_][a-zA-Z0-9_]*/)
  }
});
