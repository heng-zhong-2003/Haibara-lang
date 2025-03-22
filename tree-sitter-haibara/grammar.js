/**
 * @file A parser for the Haibara LLM query language
 * @author Heng Zhong
 * @license GPL-3.0
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

const PREC = {
  OR: 10,
  AND: 11,
  EQ: 12,
  LT: 12,
  GT: 12,
};

module.exports = grammar({
  name: "haibara_parser",

  rules: {
    // TODO: add the actual grammar rules
    source_file: $ => repeat($.statement),
    // source_file: $ => $.primary_expr,
    statement: $ => seq(
      choice(
        $.decl_statement,
        $.query_statement,
        $.print_statement
      ),
      ';'
    ),
    print_statement: $ => seq('print', '(', $.expr, ')'),
    query_statement: $ => seq(
      field(
        'query_clause',
        seq('query', field('session', $.expr), 'with', field('context', $.query_string))
      ),
      optional(seq('requires', field('requires_clause', $.expr))),
      optional(seq('role', field('role_clause', $.role))),
    ),
    decl_statement: $ => seq(
      'let',
      field('decl_identifier', $.identifier),
      ':',
      field('decl_type', $.type),
      '=',
      field('decl_expr', $.expr)
    ),
    type: $ => $.primitive_type,
    primitive_type: $ => choice(
      field('string_type', 'String'),   // field(<name>, <rule>)
      field('session_type', 'Session')
    ),
    expr: $ => choice(
      $.primary_expr,
      $.construct_session_expr,
      $.bop_expr
    ),
    construct_session_expr: $ => seq('construct_session', '(', field('llm', $.llm), ')'),
    bop_expr: $ => choice(
      prec.left(PREC.EQ, seq(field('left', $.expr), field('op', $.bop_eq), field('right', $.expr))),
      prec.left(PREC.LT, seq(field('left', $.expr), field('op', $.bop_lt), field('right', $.expr))),
      prec.left(PREC.GT, seq(field('left', $.expr), field('op', $.bop_gt), field('right', $.expr))),
      prec.left(PREC.AND, seq(field('left', $.expr), field('op', $.bop_and), field('right', $.expr))),
      prec.left(PREC.OR, seq(field('left', $.expr), field('op', $.bop_or), field('right', $.expr)))
    ),
    bop_eq: $ => '==',
    bop_lt: $ => '<',
    bop_gt: $ => '>',
    bop_and: $ => '&&',
    bop_or: $ => '||',
    primary_expr: $ => choice(
      $.primary_parenthesized_expr,
      $.primary_identifier_expr,
      $.primary_true_expr,
      $.primary_false_expr
    ),
    primary_parenthesized_expr: $ => seq('(', field('expr_in_parentheses', $.expr), ')'),
    primary_identifier_expr: $ => field('ident', $.identifier),
    primary_true_expr: $ => 'true',
    primary_false_expr: $ => 'false',
    query_string: $ => seq(
      'q"',
      repeat(
        choice(
          field('decl', $.query_decl),
          field('segment', $.query_string_segment)
        )
      ),
      '"'
    ),
    query_decl: $ => seq('{', 'let', field('decl_identifier', $.identifier), ':', field('type', 'String'), '}'),
    query_string_segment: $ => token(/[^{}"]+/),
    role: $ => choice(
      'user',
      'assistant',
      'system'
    ),
    llm: $ => choice('gpt', 'zhipu'),
    identifier: $ => token(/[a-zA-Z_][a-zA-Z0-9_]*/)
  }
});
