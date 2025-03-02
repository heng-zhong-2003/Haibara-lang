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
    source_file: $ => repeat($.statement),
    statement: $ => seq(
      choice(
        seq('let', $.identifier, ':', choice('String', 'Session'), '=', $.expr),
        seq(
          'query', $.identifier, 'with', $.query_string,
          optional(seq('requires', $.expr)),
          optional(seq('role', $.role)),
        ),
        seq('print', $.expr)
      ),
      ';'
    ),
    expr: $ => choice(
      $.identifier,
      seq('construct_session', $.llm)
    ),
    query_string: $ => seq(
      'q"',
      repeat(
        choice(
          seq('{', 'let', $.identifier, ':', 'String', '}'), // this statement can only be `let`
          token(/[^{}"]+/)
        )
      ),
      '"'
    ),
    role: $ => choice(
      'user',
      'assistant',
      'system'
    ),
    llm: $ => 'gpt',
    identifier: $ => token(/[a-zA-Z_][a-zA-Z0-9_]*/)
  }
});
