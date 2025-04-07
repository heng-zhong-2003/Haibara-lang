from typing import Any, Callable
import sys
from colorama import Fore, Style
from dataclasses import dataclass
from frontend.cst_to_gir import TransHaibara
from interpret.session import Session

class ScopeSep:
    """
    Special separator value used to indicate the beginning of a scope
    in the implementation of `ValueEnv`.
    """

    def __init__(self) -> None:
        pass


# type for runtime values in the environment of the interpreter
type RuntimeValue = str | bool | int | ScopeSep | Session | None


@dataclass
class ValueEnvEntry:
    type_name: str
    val: RuntimeValue


class ValueEnv:
    """Identifier-(runtime) value table that supports nested scopes"""

    def __init__(self) -> None:
        # map { var_name |-> stack of (<type>, <value>) pairs }
        # When `enter_scope` called, a `ScopeSep()` is pushed into all stacks;
        # when `exit_scope` called, for all stacks, the elements are poped out
        # up to the first `ScopeSep()` met (that sep also deleted).
        self.name_type_value_map: dict[str, list[ValueEnvEntry]] = {}

    def enter_scope(self) -> None:
        for _, stk in self.name_type_value_map.items():
            stk.append(ValueEnvEntry('ScopeSep', ScopeSep()))

    def exit_scope(self) -> None:
        for var_name, stk in self.name_type_value_map.items():
            # print(f'Popping stack of {var_name}')
            while True:
                if len(stk) == 0:
                    break
                stack_top = stk.pop()
                # print(f'Exit scope, poped {stack_top}')
                match stack_top.val:
                    case ScopeSep():
                        # print(f'{Fore.RED}ScopeSep popped{Style.RESET_ALL}')
                        break
                    case _:
                        pass

    def contains_variable(self, identifier: str) -> RuntimeValue:
        return identifier in self.name_type_value_map

    def get_value_of_variable(self, identifier: str) -> RuntimeValue:
        """
        Return the value of the newest declaration of `identifier`. Error
        and exit if `identifier` not declared at all.
        """
        if identifier not in self.name_type_value_map:
            sys.exit(f'Error: cannot `get_value` of an undefined identifier {identifier}.')
        stk: list[ValueEnvEntry] = self.name_type_value_map[identifier]
        for i in range(len(stk) - 1, -1, -1):
            match stk[i]:
                case ScopeSep():
                    pass
                case _:
                    return stk[i].val
        # Undefined because there is only scope separators in `identifier`'s stack
        sys.exit(f'Error: cannot `get_value` of an '
                 f'undefined identifier {identifier}, only separators.')

    def declare_variable(self, identifier: str, type_name: str) -> None:
        """
        Add a new variable to current scope. Sets its runtime value to `None`.
        If the same identifier already in outer-layer scope, the old declaration
        will be shadowed until current scope is exited.
        If the same identifier exists in the current scope, then that occurrence
        (together with its value) will be shadowed forever (since it will be
        deleted when exiting the current scope).
        """
        if identifier not in self.name_type_value_map:
            self.name_type_value_map[identifier] = [ValueEnvEntry(type_name, None)]
        else:
            stk: list[ValueEnvEntry] = self.name_type_value_map[identifier]
            is_in_current_scope: bool = False
            occur_pos: int = -1
            for i in range(len(stk) - 1, -1, -1):
                match stk[i]:
                    case ScopeSep():
                        break
                    case _:
                        is_in_current_scope = True
                        occur_pos = i
            if is_in_current_scope:
                stk[occur_pos] = ValueEnvEntry(type_name, None)
            else:
                stk.append(ValueEnvEntry(type_name, None))

    def assign_variable(self, identifier: str, new_value: RuntimeValue) -> None:
        """
        Assign `new_value` to the newest (closest to the stack top) declaration
        of `identifier`. Error and exit if `identifier` not declared at all.
        """
        if identifier not in self.name_type_value_map:
            sys.exit('Error: assigning to undeclared variable.')
        stk: list[ValueEnvEntry] = self.name_type_value_map[identifier]
        latest_decl_index: int = -1
        for i in range(len(stk) - 1, -1, -1):
            match stk[i]:
                case ScopeSep():
                    pass
                case _:
                    latest_decl_index = i
                    break
        if latest_decl_index == -1:
            sys.exit('Error: assigning to undeclared variable, all '
                     'entries in `stk` are separators.')
        stk[latest_decl_index] = ValueEnvEntry(stk[latest_decl_index].type_name, new_value)
