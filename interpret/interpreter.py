import sys
from typing import Any, Callable
from frontend.cst_to_gir import TransHaibara
from interpret.session import Session
from interpret.value_env import ValueEnv, RuntimeValue
from colorama import Fore, Style
from util import gir_content_util, dev_util


class Interpreter:
    def __init__(self) -> None:
        self.gir_stmt_kind_interp_table: \
            dict[str, Callable[[TransHaibara.GIRCommand], Any]] = {
                'variable_decl': self.interp_variable_decl,
                'assign_stmt': self.interp_assign_stmt,
                'call_stmt': self.interp_call_stmt,
                'query_stmt': self.interp_query_stmt,
                'if_stmt': self.interp_if_stmt,
                'while_stmt': self.interp_while_stmt,
                'block': self.interp_block,
            }
        # Not every `RuntimeValue` has arithmetic operations, e.g., `Session` and `ScopeSep`.
        # Type checking disabled here for convenience because otherwise there
        # cannot be dynamic dispatching (will have to use match cases instead).
        # Runtime type correctness manually guaranteed.
        self.bop_evaluation_function_map: \
            dict[str, Callable[[RuntimeValue, RuntimeValue], RuntimeValue]] = {
                '+': lambda x, y: x + y, # type: ignore
                '-': lambda x, y: x - y, # type: ignore
                '*': lambda x, y: x * y, # type: ignore
                '//': lambda x, y: x // y, # type: ignore
                '<': lambda x, y: x < y, # type: ignore
                '>': lambda x, y: x > y, # type: ignore
                '&&': lambda x, y: x and y,
                '||': lambda x, y: x or y,
            }
        self.var_type_value_env: ValueEnv = ValueEnv()
    
    def interp(self, gir_prog: list[TransHaibara.GIRCommand]) -> None:
        """
        Interpret a whole GIR program.
        """
        for cmd in gir_prog:
            # cmd_kind: str = next(iter(cmd))
            # print(f'{Fore.RED}cmd: {cmd}\ncmd_kind: {cmd_kind}{Style.RESET_ALL}\n')
            # interp_cmd: Callable[[TransHaibara.GIRCommand], Any] = \
            #     self.gir_stmt_kind_interp_table[cmd_kind]
            # interp_cmd(cmd)
            self.interp_stmt(cmd)

    def interp_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        """
        Dispatches the actual interpretation task to the corresponding concrete
        `interp_<stmt_kind>` function.
        """
        cmd_kind: str = next(iter(cmd))
        # print(f'{Fore.CYAN}GIR command: {cmd}{Style.RESET_ALL}')
        # print(f'{Fore.RED}GIR command kind: {cmd_kind}{Style.RESET_ALL}')
        interp_cmd: Callable[[TransHaibara.GIRCommand], Any] = \
            self.gir_stmt_kind_interp_table[cmd_kind]
        interp_cmd(cmd)

    def interp_variable_decl(self, cmd: TransHaibara.GIRCommand) -> None:
        var_name: str = cmd['variable_decl']['name']
        # var_type_name: str = cmd['variable_decl']['data_type']
        # Currently the generated GIR does not yet contain types
        var_type_name: str = ''
        self.var_type_value_env.declare_variable(var_name, var_type_name)

    def interp_assign_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        target_name: str = cmd['assign_stmt']['target']
        if 'operator' in cmd['assign_stmt']:
            opd1: str = cmd['assign_stmt']['operand']
            opd1_value: RuntimeValue = self.var_type_value_env.get_value_of_variable(opd1)
            opd2: str = cmd['assign_stmt']['operand2']
            opd2_value: RuntimeValue = self.var_type_value_env.get_value_of_variable(opd2)
            optr: str = cmd['assign_stmt']['operator']
            bin_expr_rslt: RuntimeValue = self.aux_compute_bin_expr(opd1_value, optr, opd2_value)
            self.var_type_value_env.assign_variable(target_name, bin_expr_rslt)
        else:
            src_name: str = cmd['assign_stmt']['operand']
            src_value: RuntimeValue
            if gir_content_util.is_string_literal(src_name):
                src_value = src_name
            elif gir_content_util.is_int_literal(src_name):
                src_value = int(src_name)
            elif gir_content_util.is_bool_literal(src_name):
                src_value = True if src_name == 'true' else False
            else:
                src_value = self.var_type_value_env.get_value_of_variable(src_name)
            self.var_type_value_env.assign_variable(target_name, src_value)

    def interp_call_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        """
        Currently, we do not yet support user-defined functions, so we hard
        code `print` and `construct_session` in this function. Should be
        radically refactored later to support user-defined functions.
        """
        match cmd['call_stmt']['name']:
            case 'print':
                arg_tmp: str = cmd['call_stmt']['positional_args']
                arg_val: RuntimeValue = self.var_type_value_env.get_value_of_variable(arg_tmp)
                print(arg_val)
            case 'construct_session':
                llm_name: str = cmd['call_stmt']['positional_args']
                new_sess: Session = Session(
                    llm_name,
                    'TODO: replace with actual API key'
                )
                target_tmp: str = cmd['call_stmt']['target']
                self.var_type_value_env.assign_variable(target_tmp, new_sess)

    def interp_if_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        cond_tmp: str = cmd['if_stmt']['condition']
        cond_val: RuntimeValue = self.var_type_value_env.get_value_of_variable(cond_tmp)
        if cond_val:
            self.interp_stmt(cmd['if_stmt']['then_body'])
        else:
            self.interp_stmt(cmd['if_stmt']['else_body'])

    def interp_while_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        cond_tmp: str = cmd['while_stmt']['condition']
        while True:
            cond_val: RuntimeValue = self.var_type_value_env.get_value_of_variable(cond_tmp)
            if not cond_val:
                break
            self.interp_stmt(cmd['while_stmt']['body'])

    def interp_block(self, cmd: TransHaibara.GIRCommand) -> None:
        # print(f'{Fore.RED}Env before enter block: {self.var_type_value_env.name_type_value_map}{Style.RESET_ALL}')
        self.var_type_value_env.enter_scope()
        # print(f'{Fore.MAGENTA}Env after enter block: {self.var_type_value_env.name_type_value_map}{Style.RESET_ALL}')
        block_contents: list[TransHaibara.GIRCommand] = cmd['block']['body']
        for cmd_in_block in block_contents:
            self.interp_stmt(cmd_in_block)
        # print(f'{Fore.CYAN}Env before exit block: {self.var_type_value_env.name_type_value_map}{Style.RESET_ALL}')
        self.var_type_value_env.exit_scope()
        # print(f'{Fore.BLUE}Env after exit block: {self.var_type_value_env.name_type_value_map}{Style.RESET_ALL}')

    def interp_query_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        query_string: str = ''
        for content_component in cmd['query_stmt']['content']:
            if content_component[0] == 'query_decl':
                query_string += f' {content_component[2]} '
            elif content_component[0] == 'segment':
                query_string += content_component[1]
            elif content_component[0] == 'variable':
                ident: str = content_component[1]
                val: RuntimeValue = self.var_type_value_env.get_value_of_variable(ident)
                # print(f'{Fore.CYAN}{val}{Style.RESET_ALL}')
                query_string += str(val)
            else:
                sys.exit('Error: unidentified `query_stmt` content component.')
        session_name: str = cmd['query_stmt']['session']
        session_obj: RuntimeValue = self.var_type_value_env.get_value_of_variable(session_name)
        match session_obj:
            case Session():
                pass
            case _:
                sys.exit('Error: session object in the runtime environment has wrong type')
        init_map: dict[str, str] = session_obj.query(query_string, 'user')
        for var_name, val in init_map.items():
            self.var_type_value_env.declare_variable(var_name, 'String')
            self.var_type_value_env.assign_variable(var_name, val)

    def aux_compute_bin_expr(self, opd1: RuntimeValue, optr: str, opd2: RuntimeValue) \
        -> RuntimeValue:
        return self.bop_evaluation_function_map[optr](opd1, opd2)
