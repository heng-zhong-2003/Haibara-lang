from typing import Any, Callable
import sys
import json
from openai.types.chat.chat_completion import ChatCompletion
from zhipuai.core._sse_client import StreamResponse
from zhipuai.types.chat.chat_completion import Completion
from zhipuai.types.chat.chat_completion_chunk import ChatCompletionChunk
from frontend.cst_to_gir import TransHaibara
from zhipuai import ZhipuAI
from openai import OpenAI
from colorama import Fore, Style

class Session():
    """
    Class for storing and using instances of Haibara `Session`s in the runtime.
    Maintains its own context (all `assistant`, `system` and `user` messages from
    and to the LLM) and LLM connection.
    Currently we use the Chih-P'u LLM (since free API is provided). API
    reference at https://open.bigmodel.cn/dev/api/normal-model/glm-4.
    """

    type Message = dict[str, Any]
    type Client = ZhipuAI | OpenAI

    def __init__(self, llm: str, api_key: str) -> None:
        self.client_constructor: dict[str, Callable[[str], Session.Client]] = {
            'zhipu': lambda key: ZhipuAI(api_key=key),
            'openai': lambda key: OpenAI(api_key=key)
        }
        self.context: list[Session.Message] = [
            {
                'role': 'user',
                'content': 'Your are an expert in anwsering cloze questions by filling blanks. '
                    'In the following prompts, you will receive sentences with blanks that '
                    'you are required to complete. Within each blank delimited by a pair '
                    'of curly brakets `{variable_name}`, you will find some identifier. '
                    'You must fill these blanks in your mind and reply with a string in '
                    'json format that maps all these variable_name\'s to the value you '
                    'answer with. You must not include any other extra characters in '
                    'your reply! When the sentence given to you does not have any blanck '
                    'to complete, you must reply with the most appropriate answer. '
                    'You must output only the json string without any other redundant '
                    'characters such as code block delimiters in markdown.',
                'response_format': {'type': 'json_object'},
            }
        ]
        self.client: Session.Client = self.client_constructor[llm](api_key)
        response: ChatCompletion | Completion | StreamResponse[ChatCompletionChunk] = \
            self.client.chat.completions \
            .create(model='glm-4-plus', messages=self.context) # type: ignore
        self.context.append(
            {
                'role': response.choices[0].message.role,
                'content': response.choices[0].message.content,
            }
        )
        print(f'{Fore.BLUE}Response to init message: {response}{Style.RESET_ALL}')

    def query(self, prompt: str, role: str) -> dict[str, str]:
        """
        Signature (especiall return type) will be further refined in refactoring.
        """
        self.context.append({'role': 'user', 'content': prompt})
        response: ChatCompletion | Completion | StreamResponse[ChatCompletionChunk] = \
            self.client.chat.completions \
            .create(model='glm-4-plus', messages=self.context) # type: ignore
        self.context.append(
            {
                'role': response.choices[0].message.role,
                'content': response.choices[0].message.content,
            }
        )
        if response.choices[0].message.content == None:
            sys.exit('Error: LLM response is `None`.')
        # Slice the content to strip off the ```json ... ``` markdown code block delimiters.
        # TODO: should be refactored to more elegant methods such as regex later.
        # TODO: if fail, prompt again!
        print(f'{Fore.YELLOW}LLM response json slice: '
              f'{response.choices[0].message.content}{Style.RESET_ALL}')
        ret: dict[str, str]
        if response.choices[0].message.content[0] == '`':
            ret = json.loads(response.choices[0].message.content[7:-4])
        else:
            ret = json.loads(response.choices[0].message.content)
        return ret
