import ell
from openai import Client


# connect to local OpenAI API (Llama at 8080)
client = Client(
    base_url="http://localhost:8080",
    api_key="your-api-key"
)


@ell.simple(model="gpt-4o", client=client)
def gpt(prompt):
    """
You will return answer for user in the best way possible.
"""
    return prompt
