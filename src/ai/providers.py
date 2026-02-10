"""
AI Provider abstraction layer
Supports both Claude (Anthropic) and OpenAI
"""

from abc import ABC, abstractmethod
from typing import Optional

from anthropic import Anthropic
from openai import OpenAI


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text from a prompt

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override (0.0–1.0)
            max_tokens: Optional max_tokens override

        Returns:
            Generated text response
        """
        pass


class ClaudeProvider(AIProvider):
    """Claude (Anthropic) provider implementation"""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        """
        Initialize Claude provider

        Args:
            api_key: Anthropic API key
            model: Claude model identifier
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Claude

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature (0.0–1.0)
            max_tokens: Optional max output tokens (default 4096)

        Returns:
            Generated text response
        """
        messages = [
            {"role": "user", "content": prompt}
        ]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or 4096,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self.client.messages.create(**kwargs)

        # Extract text from response
        return response.content[0].text


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""

    def __init__(self, api_key: str, model: str = "gpt-5.2-thinking"):
        """
        Initialize OpenAI provider

        Args:
            api_key: OpenAI API key
            model: OpenAI model identifier
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using OpenAI

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (not supported by o1 models)
            temperature: Optional temperature (0.0–1.0)
            max_tokens: Optional max output tokens (default 4096)

        Returns:
            Generated text response
        """
        _max = max_tokens or 4096

        # Build a reusable message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Use Responses API for newer reasoning/model families first.
        if (
            self.model.startswith("gpt-5")
            or self.model.startswith("o1")
            or self.model.startswith("o3")
            or self.model.startswith("o4")
        ):
            input_payload = [{"role": m["role"], "content": m["content"]} for m in messages]

            try:
                response_kwargs = {
                    "model": self.model,
                    "input": input_payload,
                    "max_output_tokens": _max,
                }
                if temperature is not None:
                    response_kwargs["temperature"] = temperature
                response = self.client.responses.create(**response_kwargs)
                output_text = getattr(response, "output_text", None)
                if output_text:
                    return output_text.strip()
            except Exception:
                # Fall through to Chat Completions fallback below.
                pass

        # Chat Completions fallback with conservative retries for parameter compatibility.
        attempt_kwargs = []
        primary_kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if max_tokens is not None:
            primary_kwargs["max_tokens"] = _max
        if temperature is not None:
            primary_kwargs["temperature"] = temperature
        attempt_kwargs.append(primary_kwargs)
        attempt_kwargs.append({"model": self.model, "messages": messages, "max_tokens": _max})
        attempt_kwargs.append({"model": self.model, "messages": messages})

        last_error = None
        for kwargs in attempt_kwargs:
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            except Exception as e:
                last_error = e

        if last_error:
            raise last_error
        raise RuntimeError("OpenAI request failed without an explicit error")


def get_ai_provider(provider_type: str, api_key: str, model: str) -> AIProvider:
    """
    Factory function to get the appropriate AI provider

    Args:
        provider_type: 'claude' or 'openai'
        api_key: API key for the provider
        model: Model identifier

    Returns:
        Configured AIProvider instance

    Raises:
        ValueError: If provider_type is not supported
    """
    if provider_type.lower() == "claude":
        return ClaudeProvider(api_key=api_key, model=model)
    elif provider_type.lower() == "openai":
        return OpenAIProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unsupported AI provider: {provider_type}")
