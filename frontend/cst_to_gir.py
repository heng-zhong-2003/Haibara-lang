import tree_sitter
from tree_sitter import Node
from typing import Any
from colorama import Fore, Style
import sys
from util import node_util

class TransHaibara:
    def __init__(self) -> None:
        self.tmp_variable_id: int = 0
    
    type GIRCommand = dict[str, dict[str, Any]]

    def generate_tmp_variable(self) -> str:
        self.tmp_variable_id += 1
        return f'%tmp{self.tmp_variable_id}'

    def trans_source_file(self, node: Node, gir_statements: list[GIRCommand]) -> None:
        prog_stmts: list[Node] = node.children
        for stmt in prog_stmts:
            self.trans_statement(stmt, gir_statements)

    def trans_statement(self, node: Node, gir_statements: list[GIRCommand]) -> None:
        """
        Dispatch the task of translating a statement to its corresponding concrete statement
        translator. `trans_statement` itself does not generate GIR commands.
        """
        # In our CST, the concrete kind of a statement is at its child (only one) level.
        concrete_stmt: Node | None = node.child(0)
        if concrete_stmt == None:
            sys.exit('Error: statement node does not have a concrete statement child.')
        stmt_kind: str = concrete_stmt.type
        match stmt_kind:
            case 'print_statement':
                self.trans_print_statement(concrete_stmt, gir_statements)
            case 'decl_statement':
                self.trans_decl_statement(concrete_stmt, gir_statements)
            case 'query_statement':
                # print('trans_query_statement')
                self.trans_query_statement(concrete_stmt, gir_statements)

    def trans_print_statement(self, node: Node, gir_statements: list[GIRCommand]) -> None:
        arg_node: Node | None = node_util.find_child_by_type(node, 'expr')
        if arg_node == None:
            sys.exit('Error: missing argument for `print` expression.')
        arg_result_tmp: str = self.trans_expression(arg_node, gir_statements)
        dummy_tmp: str = self.generate_tmp_variable()
        gir_call: TransHaibara.GIRCommand = {
            'call_stmt': {
                'target': dummy_tmp,
                'name': 'print',
                'positional_args': arg_result_tmp,
            }
        }
        gir_statements.append(gir_call)

    def trans_query_statement(self, node: Node, gir_statements: list[GIRCommand]) -> None:
        """
        To provide a high-level representation for queries to streamline interpretation,
        we add a `query_stmt` command to GIR. This should be lowered to the original
        basic commands in terms of external API invocation if we develop a compiler.
        Syntax of `query_stmt`:
        {
            'query_stmt': {
                'session': <session_name>,
                'content': [tuple['segment', str] | tuple['query_decl', type, identifier]],
                optional 'constraint': {
                    'constraint_compute_stmts': [<stmt>],
                    'constraint_value': <temp/var storing constraint_expr>,
                },
                optional 'role': <role: str>,
            },
        }
        """
        # Field within a `seq` inside another `seq` is not one level deeper than 
        # the outer `seq`. Therefore, `session` is not a child of `query_clause`.
        # In other words, neither `field` or `seq` increases the depth of children
        # inside them compared with not using these grammar functions in tree-sitter.
        queried_session: Node | None = node.child_by_field_name('session')
        if queried_session == None:
            sys.exit('Error: missing session for query statement.')
        gir_session: str = self.trans_expression(queried_session, gir_statements)
        query_content: Node | None = node.child_by_field_name('context')
        if query_content == None:
            sys.exit('Error: missing query content for query statement.')
        query_content_components: list[Node] = query_content.children
        gir_query_component: list[tuple[str, str] | tuple[str, str, str]] = []
        for component in query_content_components:
            match component.type:
                case 'query_decl':
                    decl_ident: Node | None = component.child_by_field_name('decl_identifier')
                    if decl_ident == None:
                        sys.exit('Error: decl in query string does not specify variable name')
                    gir_query_decl: tuple[str, str, str] = (
                        'query_decl',
                        'dummy_type',
                        node_util.read_node_text(decl_ident)
                    )
                    gir_query_component.append(gir_query_decl)
                case 'query_string_segment':
                    # print('query string segment:', node_util.read_node_text(component))
                    gir_string_segment: tuple[str, str] = (
                        'segment',
                        node_util.read_node_text(component)
                    )
                    gir_query_component.append(gir_string_segment)
                case _:
                    continue
        gir_query_internal: dict[str, Any] = {
            'session': gir_session,
            'content': gir_query_component
        }
        constraint: Node | None = node.child_by_field_name('requires_clause')
        if constraint != None:
            compute_constraint_stmts: list[TransHaibara.GIRCommand] = []
            constraint_tmp: str = self.trans_expression(constraint, compute_constraint_stmts)
            gir_query_internal['constraint'] = {
                'constraint_compute_stmts': compute_constraint_stmts,
                'constraint_value': constraint_tmp,
            }
        role: Node | None = node.child_by_field_name('role_clause')
        if role != None:
            gir_query_internal['role'] = node_util.read_node_text(role)
        gir_query_stmt: TransHaibara.GIRCommand = {'query_stmt': gir_query_internal}
        gir_statements.append(gir_query_stmt)

    def trans_decl_statement(self, node: Node, gir_statements: list[GIRCommand]) -> None:
        decl_ident: Node | None = node.child_by_field_name('decl_identifier')
        decl_type: Node | None = node.child_by_field_name('decl_type')
        decl_expr: Node | None = node.child_by_field_name('decl_expr')
        if decl_ident == None or decl_type == None or decl_expr == None:
            sys.exit('Error: missing child node for decl statement.')
        decl_ident_name: str = node_util.read_node_text(decl_ident)
        decl_expr_store: str = self.trans_expression(decl_expr, gir_statements)
        gir_decl: TransHaibara.GIRCommand = {
            'variable_decl': {
                'attrs': None,
                'data_type': None,  # TODO: trans_type
                'name': decl_ident_name,
            }
        }
        gir_asgn: TransHaibara.GIRCommand = {
            'assign_stmt': {
                'data_type': None,  # TODO: trans_type
                'target': decl_ident_name,
                'operand': decl_expr_store,
            }
        }
        gir_statements.append(gir_decl)
        gir_statements.append(gir_asgn)

    def trans_expression(self, node: Node, gir_statements: list[GIRCommand]) -> str:
        """
        Dispatch the translation task for an expression to its corresponding concrete
        translators. Returns the variable name or temp name that receives the result value
        of the expression. `trans_expression` itself does not generate GIR commands.
        """
        # In our CST, the concrete kind of an expression is at its child (only one) level.
        concrete_expr: Node | None = node.child(0)
        if concrete_expr == None:
            sys.exit('Error: expression node does not have a concrete expression child.')
        expr_kind: str = concrete_expr.type
        match expr_kind:
            case 'primary_expr':
                return self.trans_primary_expression(concrete_expr, gir_statements)
            case 'construct_session_expr':
                return self.trans_construct_session_expression(concrete_expr, gir_statements)
            case 'bop_expr':
                return self.trans_bop_expression(concrete_expr, gir_statements)
            case _:
                sys.exit('Error: unidentified expression kind.')
        # Unreachable `return`. Added to conciliate mypy.
        return ''

    def trans_primary_expression(self, node: Node, gir_statements: list[GIRCommand]) -> str:
        concrete_primary_expression: Node | None = node.child(0)
        if concrete_primary_expression == None:
            sys.exit(
                'Error: primary expression node does not '
                'have a concrete primary expression child.'
            )
        match concrete_primary_expression.type:
            case 'primary_parenthesized_expr':
                content_in_parentheses: Node | None = \
                    concrete_primary_expression.child_by_field_name('expr_in_parentheses')
                if content_in_parentheses == None:
                    sys.exit('Error: contents within parentheses is `None`.')
                parenthesized_tmp: str = self.trans_expression(
                    content_in_parentheses,
                    gir_statements
                )
                return parenthesized_tmp
            case 'primary_identifier_expr':
                ident: Node | None = concrete_primary_expression.child_by_field_name('ident')
                if ident == None:
                    sys.exit('Error: identifier inside `primary_identifier_expr` is `None`.')
                ident_name: str = node_util.read_node_text(ident)
                return ident_name
            case 'primary_true_expr':
                pass
            case 'primary_false_expr':
                pass
            case _:
                sys.exit('Error: unidentified primary expression kind.')
        # Unreachable `return`. Added to conciliate mypy.
        return ''

    def trans_construct_session_expression(self, node: Node, gir_statements: list[GIRCommand]) -> str:
        llm: Node | None = node.child_by_field_name('llm')
        if llm == None:
            sys.exit('Error: empty llm name.')
        llm_name: str = node_util.read_node_text(llm)
        llm_construct_tmp: str = self.generate_tmp_variable()
        gir_call: TransHaibara.GIRCommand = {
            'call_stmt': {
                'target': llm_construct_tmp,
                'name': 'construct_session',
                'positional_args': llm_name,
            }
        }
        gir_statements.append(gir_call)
        return llm_construct_tmp

    def trans_bop_expression(self, node: Node, gir_statements: list[GIRCommand]) -> str:
        left_opd: Node | None = node.child_by_field_name('left')
        if left_opd == None:
            sys.exit('Error: binary operator has `None` left operand')
        right_opd: Node | None = node.child_by_field_name('right')
        if right_opd == None:
            sys.exit('Error: binary operator has `None` right operand')
        optr: Node | None = node.child_by_field_name('op')
        if optr == None:
            sys.exit('Error: binary operator has `None` operator')
        left_tmp: str = self.trans_expression(left_opd, gir_statements)
        right_tmp: str = self.trans_expression(right_opd, gir_statements)
        rslt_tmp: str = self.generate_tmp_variable()
        gir_decl_tmp: TransHaibara.GIRCommand = {
            'variable_decl': {
                'attrs': None,
                'data_type': None,  # TODO: trans_type
                'name': rslt_tmp,
            }
        }
        gir_bop: TransHaibara.GIRCommand = {
            'assign_stmt': {
                'data_type': None,
                'target': rslt_tmp,
                'operand': left_tmp,
                'operator': node_util.read_node_text(optr),
                'operand2': right_tmp,
            }
        }
        gir_statements.append(gir_decl_tmp)
        gir_statements.append(gir_bop)
        return rslt_tmp
