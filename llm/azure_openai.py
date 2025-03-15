import os
from openai import AzureOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Optional, Dict, Any
from langchain_core.tools import BaseTool

class AzureOpenAIChat(BaseChatModel, BaseModel):
    """Custom LLM wrapper for Azure OpenAI GPT-4 Mini."""

    api_key: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY"))
    api_version: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION"))
    azure_endpoint: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT"))
    deployment: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    _client: AzureOpenAI = PrivateAttr()

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )

    def _generate(self, messages: List[HumanMessage], **kwargs) -> ChatResult:
        try:
            openai_messages = [
                {"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content}
                for msg in messages
            ]

            response = self._client.chat.completions.create(
                model=self.deployment,
                messages=openai_messages,
                **kwargs
            )

            return ChatResult(
                generations=[
                    ChatGeneration(message=AIMessage(content=response.choices[0].message.content))
                ]
            )
        except Exception as e:
            return ChatResult(
                generations=[
                    ChatGeneration(message=AIMessage(content=f"Error: {str(e)}"))
                ]
            )

    def _llm_type(self) -> str:
        return "azure_openai_chat"
