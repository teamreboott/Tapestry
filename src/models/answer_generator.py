import os
import time
import json
import structlog
import asyncio, os, traceback
from litellm import acompletion
from datetime import datetime
from rich.console import Console

console = Console()
logger = structlog.get_logger(__name__)


class AnswerGenerator:
    def __init__(
        self,
        model='gemini-2.5-flash-preview-04-17', # Corrected default to match logic
        max_tokens=8000,
        timeout=120
    ):

        self.max_tokens = max_tokens
        self.timeout = timeout
        # Corrected model name logic to be more robust, gemini/ is added by litellm if needed
        if model == "gemini-2.0-flash" or model == "gemini-2.5-flash-preview-04-17":
            self.model_name = f"gemini/{model}"
        else:
            self.model_name = model
        # Fallback models should ideally be full model names recognized by litellm
        self.fallback_model = ["claude-3-haiku-20240307", "gpt-3.5-turbo", "gemini-1.5-flash-latest"]


    def get_date(self):
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_date

    async def get_response(self, messages: list, stream=False):
        if stream:
            try:
                # Return the stream object directly.
                # The caller will iterate through it and then access .usage.
                response_stream = await acompletion(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=1.0,
                    fallbacks=self.fallback_model,
                    stream=True,
                    timeout=self.timeout # Add timeout for streaming calls too
                )
                return response_stream
            except Exception as e: # Catch any exception from acompletion
                logger.error(f"Stream acompletion error: {traceback.format_exc()}")
                # Return an empty async generator in case of error to avoid breaking the caller's async for loop
                async def empty_async_generator():
                    if False: # Ensure it's a generator
                        yield
                return empty_async_generator()
        else: # Non-streaming
            try:
                response = await acompletion(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=1.0,
                    timeout=self.timeout,
                    fallbacks=self.fallback_model
                )

                answers = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = input_tokens + output_tokens

                return {
                    "answer": answers,
                    "prompt_usage": input_tokens,
                    "completion_usage": output_tokens,
                    "total_usage": total_tokens,
                }
            except Exception as e:
                logger.error(f"Non-stream acompletion error: {e}", exc_info=True)
                return { # Return a consistent error structure or empty dict
                    "answer": "",
                    "prompt_usage": 0,
                    "completion_usage": 0,
                    "total_usage": 0,
                    "error": str(e)
                }
