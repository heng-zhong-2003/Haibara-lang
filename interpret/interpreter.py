from typing import Any, Callable
from frontend.cst_to_gir import TransHaibara
from session import Session

class Interpreter:
    def __init__(self):
        self.gir_stmt_kind_interp_table: \
            dict[str, Callable[[TransHaibara.GIRCommand], Any]] = {
                'variable_decl': self.interp_variable_decl,
                'assign_stmt': self.interp_assign_stmt,
            }

    def interp_variable_decl(self, cmd: TransHaibara.GIRCommand) -> None:
        pass

    def interp_assign_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        pass

    def interp_query_stmt(self, cmd: TransHaibara.GIRCommand) -> None:
        pass
