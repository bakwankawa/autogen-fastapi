from autogen.agentchat import AssistantAgent, UserProxyAgent, Agent
from typing import Dict, Optional, Union
from app.utils import save_message_to_redis

class ChainlitAssistantAgent(AssistantAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = None
        self.pn_rm = '138626'

    def send(
        self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ) -> bool:
        if self.name == "Spokesman":
            content = message if isinstance(message, str) else message.get('content', '')
            save_message_to_redis(self.pn_rm, content, "assistant", self.name)

            if self.response:
                self.response.body = content.encode('utf-8')
                self.response.status_code = 200
                raise SystemExit
            return True

        return super().send(message=message, recipient=recipient, request_reply=request_reply, silent=silent)

    def set_fastapi_response(self, response):
        self.response = response

class ChainlitUserProxyAgent(UserProxyAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pn_rm = '138626'

    def send(
        self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ):
        save_message_to_redis(self.pn_rm, message, "user", self.name)
        super().send(message=message, recipient=recipient, request_reply=request_reply, silent=silent)