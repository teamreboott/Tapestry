import os
import time
import json
import structlog
from litellm import acompletion
from datetime import datetime
from rich.console import Console

console = Console()
logger = structlog.get_logger(__name__)


class QueryRewriter:
    def __init__(
        self, 
        model='gpt-4.1-nano-2025-04-14',
        max_tokens=5000,
        timeout=10
    ):
        self.input_tokens = 0
        self.output_tokens = 0
        self.max_tokens = max_tokens
        self.timeout = timeout
        if model == "gemini-2.0-flash" or model == "gemini-2.5-flash-preview-04-17":
            self.model_name = f"gemini/{model}"
        else:
            self.model_name = model
        self.fallback_model = ["gpt-4.1-mini-2025-04-14", "gpt-4.1", "gemini/gemini-2.0-flash"]

    def get_date(self):
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_date

    async def get_response(self, messages: list):  # async로 변경
        start_time = time.time()
        try:
            response = await acompletion(
                model=self.model_name,
                response_format={ "type": "json_object" },
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=1.0,
                timeout=self.timeout,
                fallbacks=self.fallback_model
            )

            answers = json.loads(response.choices[0].message.content)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = input_tokens + output_tokens

            structed_answers = []
            for key, val in answers.items():
                answer_list = list(val)
                structed_answers.append(
                    {
                        'query': answer_list[0],
                        'type': answer_list[1],
                        'language': answer_list[2],
                        'period': answer_list[3]
                    }
                )

            end_time = time.time()
            console.log(f"[pink bold]QueryRewriter: {end_time - start_time:.2f} seconds")

            return {
                "answer": structed_answers,
                "prompt_usage": input_tokens,
                "completion_usage": output_tokens,
                "total_usage": total_tokens,
            }
            
        except Exception as e:
            logger.warning("query_rewrite_error", error=str(e), messages='openai 모델 에러')
            return {}
