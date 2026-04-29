# core/llm.py
import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from .prompts import build_system_prompt

def get_advisor_response(protocol, user_query):
    # Get the token from environment variables
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not found in environment variables."

    client = ChatCompletionsClient(
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(token),
    )

    system_msg = build_system_prompt(protocol)

    response = client.complete(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_query},
        ],
        model="gpt-4o",
        temperature=0.7,
        max_tokens=1500
    )

    return response.choices[0].message.content