import json
import uuid

from django.template.loader import render_to_string
from django.conf import settings
from channels.generic.websocket import WebsocketConsumer
from openai import OpenAI

from langchain_community.llms.llamafile import Llamafile
from langchain_core.messages import HumanMessage, AIMessage


def _format_token(token: str) -> str:
     # apply very basic formatting while we're rendering tokens in real-time
     token = token.replace("\n", "<br>")
     return token


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.messages = []
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]
        print(message_text)

        # do nothing with empty messages
        if not message_text.strip():
            return

        # add to messages
        self.messages.append(
            HumanMessage(content=message_text)
        )

        # show user's message
        user_message_html = render_to_string(
            "ai/websocket_components/user_message.html",
            {
                "message_text": message_text,
            },
        )
        self.send(text_data=user_message_html)

        # render an empty system message where we'll stream our response
        message_id = uuid.uuid4().hex
        contents_div_id = f"message-response-{message_id}"
        system_message_html = render_to_string(
            "ai/websocket_components/ai_message.html",
            {
                "contents_div_id": contents_div_id,
            },
        )
        self.send(text_data=system_message_html)

        llm = Llamafile(
            base_url=settings.OPENAI_BASE_URL,
            streaming=True,
        )
        chunks = []
        for chunk in llm.stream(self.messages):
            chunks.append(chunk)
            # use htmx to insert the next token at the end of our system message.
            chunk = f'<div hx-swap-oob="beforeend:#{contents_div_id}">{_format_token(chunk)}</div>'
            self.send(text_data=chunk)
        system_message = "".join(chunks)
        print(system_message)
        # replace final input with fully rendered version, so we can render markdown, etc.
        final_message_html = render_to_string(
            "ai/websocket_components/final_ai_message.html",
            {
                "contents_div_id": contents_div_id,
                "message": system_message,
            },
        )
        # add to messages
        self.messages.append(
            AIMessage(content=system_message)
        )
        self.send(text_data=final_message_html)
