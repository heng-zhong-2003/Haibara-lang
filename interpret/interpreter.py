import sys
from typing import Any, Callable
from frontend.cst_to_gir import TransHaibara
from interpret.session import Session
from interpret.value_env import ValueEnv, RuntimeValue
from colorama import Fore, Style

class Interpreter:
    def __init__(self) -> None:
        self.gir_stmt_kind_interp_table: \
            dict[str, Callable[[TransHaibara.GIRCommand], Any]] = {
                'variable_decl': self.interp_variable_decl,
                'assign_stmt': self.interp_assign_stmt,
                'call_stmt': self.interp_call_stmt,
                'query_stmt': self.interp_query_stmt,
            }
        self.var_type_value_env: ValueEnv = ValueEnv()
    
    def interp(self, gir_prog: list[TransHaibara.GIRCommand]) -> None:
        for cmd in gir_prog:
            cmd_kind: str = next(iter(cmd))
            # print(f'{Fore.RED}cmd: {cmd}\ncmd_kind: {cmd_kind}{Style.RESET_ALL}\n')
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
            if src_name[0:5] == r'%lit:':
                src_value = src_name
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
                    'TODO: replace with real API key.'
                )
                target_tmp: str = cmd['call_stmt']['target']
                self.var_type_value_env.assign_variable(target_tmp, new_sess)

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
        match optr:
            case '==':
                return opd1 == opd2
            case '<':
                return opd1 < opd2 # type: ignore
            case '>':
                return opd1 > opd2 # type: ignore
            case '&&':
                return opd1 and opd2
            case '||':
                return opd1 or opd2
            case _:
                sys.exit('Error: unidentified operator.')
