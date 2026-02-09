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

        # GPT-5 models support special parameters
        if self.model.startswith('gpt-5'):
            def _build_input(role: str, text: str) -> dict:
                return {
                    "role": role,
                    "content": [{"type": "input_text", "text": text}]
                }

            inputs = []
            if system_prompt:
                inputs.append(_build_input("system", system_prompt))
            inputs.append(_build_input("user", prompt))

            response = self.client.responses.create(
                model=self.model,
                input=inputs,
                max_output_tokens=_max,
            )

            # Prefer the convenience helper when available
            output_text = getattr(response, "output_text", None)
            if output_text:
                return output_text.strip()

            # Fallback: stitch together any text fragments
            text_fragments = []
            for item in getattr(response, "output", []) or []:
                item_type = getattr(item, "type", None)
                if item_type is None:
                    item_type = getattr(item, "role", None)
                if item_type is None and isinstance(item, dict):
                    item_type = item.get("type") or item.get("role")
                if item_type == "message":
                    contents = getattr(item, "content", None)
                    if contents is None and isinstance(item, dict):
                        contents = item.get("content", [])
                    contents = contents or []
                    for content_part in contents:
                        text = getattr(content_part, "text", None)
                        if text is None and isinstance(content_part, dict):
                            text = content_part.get("text")
                        if text:
                            text_fragments.append(text)
                elif item_type == "output_text":
                    content = getattr(item, "content", None)
                    if content is None and isinstance(item, dict):
                        content = item.get("content")
                    if isinstance(content, list):
                        for chunk in content:
                            text = getattr(chunk, "text", None)
                            if text is None and isinstance(chunk, dict):
                                text = chunk.get("text")
                            if text:
                                text_fragments.append(text)
                    elif isinstance(content, str):
                        text_fragments.append(content)

            if text_fragments:
                return "".join(text_fragments).strip()

            # As a last resort, return stringified response
            return str(response)

        # o-series models (o1, o3, o4) don't support system prompts, so prepend to user message
        if self.model.startswith('o1') or self.model.startswith('o3') or self.model.startswith('o4'):
            messages = []
            # Combine system prompt with user prompt for o-series models
            if system_prompt:
                combined_prompt = f"{system_prompt}\n\n{prompt}"
                messages.append({"role": "user", "content": combined_prompt})
            else:
                messages.append({"role": "user", "content": prompt})

            # o-series models also don't support temperature or max_tokens in the same way
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
        else:
            messages = []
            # Standard GPT models support system prompts
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=_max,
                temperature=temperature if temperature is not None else 0.7,
            )

        return response.choices[0].message.content


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
