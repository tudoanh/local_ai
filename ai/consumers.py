import json
import uuid

from django.template.loader import render_to_string
from django.conf import settings
from channels.generic.websocket import WebsocketConsumer
from openai import OpenAI
from rag.utils import create_embedding, search_similar_knowledge, get_query_embedding
from ai.models import Thread, Message

from langchain_community.llms.llamafile import Llamafile
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def _format_token(token: str) -> str:
     # apply very basic formatting while we're rendering tokens in real-time
     token = token.replace("\n", "<br>")
     return token


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.messages = [
            SystemMessage(content="You are a knowledgeable, efficient, and direct AI assistant. Provide concise answers, focusing on the key information needed. Offer suggestions tactfully when appropriate to improve outcomes. Engage in productive collaboration with the user.")
        ]
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json["message"]
        thread_id = text_data_json.get("thread_id")
        uploaded_files = text_data_json.get("uploaded_files")
        print(message_text)
        print(thread_id)
        print(uploaded_files)

        # do nothing with empty messages
        if not message_text.strip():
            return
        
        if not thread_id:
            thread = Thread.objects.create(title=message_text[:50].strip().replace("\n", " ").capitalize())
            thread_id = thread.id
            user_msg = Message.objects.create(thread=thread, text=message_text, role=Message.Role.USER)
        else:
            thread = Thread.objects.get(id=thread_id)
            last_msg = thread.message_set.order_by("-created").first()
            user_msg = Message.objects.create(thread=thread, text=message_text, role=Message.Role.USER, previous_message=last_msg)
        
        if uploaded_files:
            file_ids = uploaded_files.split(",")
            query = get_query_embedding(message_text)
            similars = search_similar_knowledge(query, file_ids, limit=20)
            similar_docs_html = render_to_string(
                "ai/websocket_components/similar_documents.html",
                {
                    "similar_docs": similars
                }
            )
            self.send(text_data=f'<div id="related-documents" hx-swap-oob="innerHTML">{similar_docs_html}</div>')

            print(f"Similar knowledge entries: {similars}")
            self.messages.append(
                AIMessage(content=f"Similar knowledge entries: {similars}. Please return response based on this.")
            )

        # add to messages
        self.messages.append(
            HumanMessage(content="<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n"+message_text+"<|eot_id|><|start_header_id|>assistant<|end_header_id|>")
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
        for chunk in llm.stream(self.messages, stop=["<|eot_id|>"]):
            chunks.append(chunk)
            # use htmx to insert the next token at the end of our system message.
            chunk = f'<div class="message-content" hx-swap-oob="beforeend:#{contents_div_id}">{_format_token(chunk)}</div>'
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
        ai_msg = Message.objects.create(thread=thread, text=system_message, role=Message.Role.AI, previous_message=user_msg)
        self.messages.append(
            AIMessage(content=system_message)
        )
        self.send(text_data=final_message_html)
