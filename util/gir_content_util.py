from colorama import Fore, Style

def is_string_literal(content: str) -> bool:
    if len(content) <= 1:
        return False
    return content[0] == '\"' and content[-1] == '\"'

def is_int_literal(content: str) -> bool:
    try:
        int(content)
        return True
    except ValueError:
        return False

def is_bool_literal(content: str) -> bool:
    return content == 'true' or content == 'false'
