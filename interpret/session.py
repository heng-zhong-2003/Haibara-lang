from typing import Any
from frontend.cst_to_gir import TransHaibara

class Session():
    """
    Class for storing and using values of Haibara `Session`s in the interpreter.
    Maintains its own context (all `assistant`, `system` and `user` messages from
    and to the LLM) and LLM connection.
    Currently we use the Chih-P'u LLM (since free API is provided). API
    reference at https://open.bigmodel.cn/dev/api/normal-model/glm-4.
    """

    type Message = dict[str, Any]

    def __init__(self, llm: str) -> None:
        self.llm: str = llm
        self.context: list[Session.Message] = []
