"""Minimal HTTP client for llama-server."""

import json
import urllib.request
import urllib.error
from typing import Generator, Optional
from sovereign.infrastructure.config import get_settings
from sovereign.core.exceptions import ModelRuntimeError, ContextOverflowError
from sovereign.core.runtime.models import (
    InferenceRequest,
    InferenceResponse,
    StreamingResponseChunk
)

class LlamaCppClient:
    """Client for the /completion API."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self._settings = get_settings()
        self._host = host or self._settings.server_host
        self._port = port or self._settings.server_port
        
    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"
        
    def set_endpoint(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        
    def _estimate_tokens(self, text: str) -> int:
        """Roughly estimate token count to prevent silent overflow (approx 4 chars/token)."""
        return len(text) // 4
        
    def _build_payload(self, request: InferenceRequest, context_size: Optional[int] = None) -> bytes:
        ctx = context_size or self._settings.context_size
        estimated_prompt_tokens = self._estimate_tokens(request.prompt)
        # Check against context size
        if estimated_prompt_tokens + request.max_tokens > ctx * 1.5:
             # Generous buffer for estimation error, but block obvious overflows
             raise ContextOverflowError(f"Estimated tokens exceed configured context size of {ctx}")

        data = {
            "prompt": request.prompt,
            "n_predict": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }
        if request.stop:
            data["stop"] = request.stop
            
        return json.dumps(data).encode("utf-8")

    def _build_chat_payload(self, request: InferenceRequest, context_size: Optional[int] = None) -> bytes:
        ctx = context_size or self._settings.context_size
        estimated_prompt_tokens = self._estimate_tokens(request.prompt)
        if estimated_prompt_tokens + request.max_tokens > ctx * 1.5:
             raise ContextOverflowError(f"Estimated tokens exceed configured context size of {ctx}")

        if request.images:
            content = [{"type": "text", "text": request.prompt}]
            for img in request.images:
                content.append({"type": "image_url", "image_url": {"url": img}})
        else:
            content = request.prompt

        data = {
            "messages": [
                {"role": "user", "content": content}
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }
        if request.response_format is not None:
            data["response_format"] = request.response_format
        if request.stop:
            data["stop"] = request.stop
            
        return json.dumps(data).encode("utf-8")

    def generate(self, request: InferenceRequest, context_size: Optional[int] = None) -> InferenceResponse:
        url_base = self.base_url
        use_chat_api = request.response_format is not None or request.images is not None
        if not use_chat_api:
            url = f"{url_base}/completion"
            payload = self._build_payload(request, context_size=context_size)
        else:
            url = f"{url_base}/v1/chat/completions"
            payload = self._build_chat_payload(request, context_size=context_size)
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                
                if not use_chat_api:
                    return InferenceResponse(
                        text=result.get("content", ""),
                        usage={
                            "prompt_tokens": result.get("tokens_evaluated", 0),
                            "completion_tokens": result.get("tokens_predicted", 0)
                        },
                        stop_reason=result.get("stop_type", "unknown")
                    )
                else:
                    choices = result.get("choices", [])
                    choice = choices[0] if choices else {}
                    message = choice.get("message", {})
                    usage_info = result.get("usage", {})
                    return InferenceResponse(
                        text=message.get("content", ""),
                        usage={
                            "prompt_tokens": usage_info.get("prompt_tokens", 0),
                            "completion_tokens": usage_info.get("completion_tokens", 0)
                        },
                        stop_reason=choice.get("finish_reason", "unknown")
                    )
        except urllib.error.URLError as e:
            raise ModelRuntimeError(f"Failed to communicate with llama-server: {e}")

    def stream(self, request: InferenceRequest, context_size: Optional[int] = None) -> Generator[StreamingResponseChunk, None, None]:
        url_base = self.base_url
        use_chat_api = request.response_format is not None or request.images is not None
        if not use_chat_api:
            url = f"{url_base}/completion"
            payload = self._build_payload(request, context_size=context_size)
        else:
            url = f"{url_base}/v1/chat/completions"
            payload = self._build_chat_payload(request, context_size=context_size)
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            result = json.loads(data_str)
                            if not use_chat_api:
                                is_done = result.get("stop", False)
                                chunk = StreamingResponseChunk(
                                    text=result.get("content", ""),
                                    is_done=is_done
                                )
                                if is_done:
                                    chunk.stop_reason = result.get("stop_type", "unknown")
                                    chunk.usage = {
                                        "prompt_tokens": result.get("tokens_evaluated", 0),
                                        "completion_tokens": result.get("tokens_predicted", 0)
                                    }
                                yield chunk
                            else:
                                choices = result.get("choices", [])
                                choice = choices[0] if choices else {}
                                delta = choice.get("delta", {})
                                finish_reason = choice.get("finish_reason")
                                is_done = finish_reason is not None
                                chunk = StreamingResponseChunk(
                                    text=delta.get("content", ""),
                                    is_done=is_done
                                )
                                if is_done:
                                    chunk.stop_reason = finish_reason
                                    usage_info = result.get("usage", {})
                                    chunk.usage = {
                                        "prompt_tokens": usage_info.get("prompt_tokens", 0),
                                        "completion_tokens": usage_info.get("completion_tokens", 0)
                                    }
                                yield chunk
                        except json.JSONDecodeError:
                            continue
        except urllib.error.URLError as e:
            raise ModelRuntimeError(f"Failed to communicate with llama-server: {e}")
