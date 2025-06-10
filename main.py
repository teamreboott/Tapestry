from __future__ import annotations

import asyncio
import json
import os
import structlog
import uvicorn
import uvloop
import time
from typing import AsyncGenerator
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from src.models.query_rewriter import QueryRewriter
from src.models.outline_generator import OutlineGenerator
from src.models.answer_generator import AnswerGenerator
from src.models.model_list import get_llm_info
from src.utils.common import is_url, extract_urls, load_yaml, json_line
from src.utils.logging import configure_logging
from rich.console import Console
from src.search.serper import SerperClientAsync
from src.search.crawl import Crawler
from configs.config import Settings
from src.types.language import Language
from src.search.browser_utils import load_browser_client
from src.db.pg_utils import create_pg_tables, save_document_to_pg
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
load_dotenv()

# ────────────────────────────────────────────────────────────────────────────────
# Config & settings
# ────────────────────────────────────────────────────────────────────────────────
settings = Settings()
console = Console()

prompts = load_yaml(os.path.join(os.path.dirname(__file__), "src", "prompts", "prompts.yaml"))
config = load_yaml(os.path.join(os.path.dirname(__file__), "configs", "config.yaml"))

LOG_DIR = os.getenv("LOG_DIR")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "server.log")

QUERY_REWRITE_MODEL_NAME: str = config['models']['query_generator']['model_name']
OUTLINE_GENERATOR_MODEL_NAME: str = config['models']['outline_generator']['model_name']
ANSWER_GENERATOR_MODEL_NAME: str = config['models']['answer_generator']['model_name']

QUERY_REWRITE_MODEL_INFO = get_llm_info(QUERY_REWRITE_MODEL_NAME)
OUTLINE_GENERATOR_MODEL_INFO = get_llm_info(OUTLINE_GENERATOR_MODEL_NAME)
ANSWER_GENERATOR_MODEL_INFO = get_llm_info(ANSWER_GENERATOR_MODEL_NAME)
configure_logging(LOG_FILE)
logger = structlog.get_logger()


query_rewriter = QueryRewriter(model=QUERY_REWRITE_MODEL_NAME, max_tokens=config['models']['query_generator']['max_tokens'])
outline_generator = OutlineGenerator(model=OUTLINE_GENERATOR_MODEL_NAME, max_tokens=config['models']['outline_generator']['max_tokens'])
answer_generator = AnswerGenerator(model=ANSWER_GENERATOR_MODEL_NAME, max_tokens=config['models']['answer_generator']['max_tokens'])


# --------------------------------------------------------------------------------
# FastAPI application & lifespan events
# --------------------------------------------------------------------------------

async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    # TODO: Alembic (migration)
    create_pg_tables()
    yield


app = FastAPI(title="Web Search API", version="0.1.0", lifespan=lifespan)
semaphore = asyncio.Semaphore(settings.SEMAPHORE_LIMIT)

class Query(BaseModel):
    query: str
    language: str
    messages: list[dict] | None = []
    persona_prompt: str | None = "N/A"
    custom_prompt: str | None = "N/A"
    target_nuance: str | None = "Natural"
    return_process: bool = True
    stream: bool = False
    use_youtube_transcript: bool = False
    top_k: int | None = "auto"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url.path), error=str(exc))
    return JSONResponse(status_code=500, content={"status": "error", "message": "Internal Server Error"})

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Service is healthy"}


@app.post("/websearch", response_class=StreamingResponse)
async def websearch(payload: Query, request: Request):
    client_host = request.client.host if request.client else "unknown"
    logger.info("/websearch_called", client_host=client_host, payload=payload)
    return StreamingResponse(webchat(payload), media_type="text/event-stream")


async def webchat(payload: Query) -> AsyncGenerator[str, None]:
    start_time = time.time()
    browser_client = load_browser_client()

    # 1) Initialize components
    history_messages = payload.messages
    num_history_messages = len(history_messages)
    if num_history_messages > 4:
        history_messages = history_messages[-4:]
    query = payload.query.replace('\n', ' ').replace('\t', ' ').strip()
    language = payload.language
    persona_prompt = payload.persona_prompt
    custom_prompt = payload.custom_prompt
    target_nuance = payload.target_nuance
    return_process = payload.return_process
    stream = payload.stream
    use_youtube_transcript = payload.use_youtube_transcript
    top_k = payload.top_k if isinstance(payload.top_k, int) else None

    target_language_name = Language.from_code(language).query_params["name"]
    reference_label = Language.from_code(language).query_params["source_tag"]

    query_rewrite_prompt_usage = query_rewrite_completion_usage = query_rewrite_total_usage = 0
    outline_prompt_usage = outline_completion_usage = outline_total_usage = 0
    answer_prompt_usage = answer_completion_usage = answer_total_usage = 0

    # 2) Initialize SerperClientAsync
    serper_client = SerperClientAsync(browser_client=browser_client, 
                                      api_key=settings.SERPER_API_KEY, 
                                      num_output_per_query=10, 
                                      content_type_timeout=1.0,
                                      use_youtube_transcript=use_youtube_transcript,
                                      top_k=top_k)

    # 3) Initialize Crawler
    crawler = Crawler(browser_client=browser_client, max_content_length=20000)

    if return_process:
        yield json_line({"status": "processing", "message": {"title": "질문 분석 중..."}})

    try:
        query_list = []
        if len(query) > 300:
            num_samples = config['web_search']['n_queries']
        else:
            num_samples = max(config['web_search']['n_queries'] - 1, 1)
            query_list.append({"query": query, "type": "Search", "language": language, "period": "Any time"})

        date_str = query_rewriter.get_date()

        if num_history_messages > 0:
            prompt = prompts['web_prompt_history'].format(history=history_messages, query=query, date=date_str, num_samples=num_samples)
        else:
            prompt = prompts['web_prompt'].format(query=query, date=date_str, num_samples=num_samples)

        if num_history_messages == 0 and is_url(query):
            use_search_engine = False
            pass
        else:
            use_search_engine = True
            response = await query_rewriter.get_response([{"role": "user", "content": prompt}])

            query_rewrite_prompt_usage += response.get("prompt_usage", 0)
            query_rewrite_completion_usage += response.get("completion_usage", 0)
            query_rewrite_total_usage += response.get("total_usage", 0)
            total_answers = response.get("answer", [])

            if len(total_answers) != 0:
                query_list.extend(total_answers)

            urls = extract_urls(query)
            for url in urls:
                query_list.append({"query": url, "type": "Search", "language": "ko"})

        if len(query_list) == 0:
            yield json_line({"status": "failure", "data": {"title": "질문을 이해하지 못했습니다."}})
            return

        if return_process:
            yield json_line({"status": "processing", "message": {"title": "관련 질문 검색 중..."}})

        serper_credits = int(2 * len(query_list))

        if use_search_engine:
            scraped_sources = await serper_client.multiple_search(query_list)
            total_results = len(scraped_sources)
        else:
            scraped_sources = [{
                "title": "",
                "url": query,
                "snippet": "",
                "image_url": "",
                "date": "",
                "language": "ko",
                "type": "search",
                "pdf_url": "",
            }]
            total_results = 1
            serper_credits = 0

        if total_results == 0:
            logger.error("no_results", query=query, message="웹 검색 결과가 없습니다.")
            yield json_line({"status": "failure", "message": {"title": "웹 검색 결과가 없습니다."}})
            return

        merged_query = " ".join([q["query"] for q in query_list])
        merged_content = ""
        for src in scraped_sources:
            title = src.get("title", "")
            snippet = src.get("snippet", "")
            merged_content += f"{title}: {snippet}\n"

        if return_process:
            yield json_line({"status": "processing", "message": {"title": f"{total_results}개의 검색 결과를 살펴보는 중..."}})

        # 소제목 생성과 웹 콘텐츠 스크래핑을 병렬로 실행
        async def get_outlines(outline_prompt):
            outline_response = await outline_generator.get_response([{"role": "user", "content": outline_prompt}])
            prompt_usage = outline_response.get("prompt_usage", 0)
            completion_usage = outline_response.get("completion_usage", 0)
            total_usage = outline_response.get("total_usage", 0)
            outlines = outline_response.get("sub_titles", [])

            outline_results = {
                "outlines": outlines,
                "prompt_usage": prompt_usage,
                "completion_usage": completion_usage,
                "total_usage": total_usage,
            }
            return outline_results

        if use_search_engine:
            outline_prompt = prompts['outline_prompt'].format(query=merged_query, content=merged_content, target_language=target_language_name)
            outline_task = get_outlines(outline_prompt)
            crawl_task = crawler.multiple_crawl(scraped_sources)
            outline_results, web_contents = await asyncio.gather(outline_task, crawl_task)

        else:
            web_contents = await crawler.crawl(scraped_sources[0])
            web_contents = [web_contents]
            url_content = web_contents[0]['content']
            outline_prompt = prompts['outline_prompt'].format(query=query, content=url_content)
            outline_results = await get_outlines(outline_prompt)
            outlines = outline_results.get("outlines", [])

        outline_prompt_usage += outline_results.get("prompt_usage", 0)
        outline_completion_usage += outline_results.get("completion_usage", 0)
        outline_total_usage += outline_results.get("total_usage", 0)

        outlines = outline_results.get("outlines", [])

        end_time = time.time()
        execution_time = end_time - start_time
        console.print(f"[pink bold]Processing time: {execution_time:.2f} seconds")

        if return_process:
            yield json_line({"status": "processing", "message": {"title": "웹 검색 완료"}})

        answer_content_for_summary = ""
        today_date = date_str
        sub_titles = str(outlines)
        prompt_web_search = json.dumps(web_contents)

        console.print(f"[pink bold]WebSearch-Answer: {target_language_name} !!!!")

        answer_prompt = prompts['answer_prompt'].format(persona_prompt=persona_prompt, 
                                                        custom_prompt=custom_prompt, 
                                                        target_language=target_language_name, 
                                                        target_nuance=target_nuance, 
                                                        reference_label=reference_label, 
                                                        today_date=today_date, 
                                                        sub_titles=sub_titles, 
                                                        prompt_web_search=prompt_web_search)
        if num_history_messages > 0:
            messages = history_messages.extend([{"role": "user", "content": answer_prompt}])
        else:
            messages = [{"role": "user", "content": answer_prompt}]

        if stream: # Check the renamed flag
            collected_answer_chunks = []
            # answer_generator.get_response now returns the stream object when stream=True
            llm_stream_iterator = await answer_generator.get_response(
                messages,
                stream=True
            )
            async for chunk in llm_stream_iterator: # Iterate over LiteLLM's chunk objects
                # Make sure chunk and its attributes are not None
                if chunk and chunk.choices and chunk.choices[0].delta:
                    token_text = chunk.choices[0].delta.content
                    if token_text is not None: # Ensure content is not None
                        collected_answer_chunks.append(token_text)
                        # Yield in the format requested by the user
                        yield json_line({"status": "streaming", "delta": {"content": token_text}})
            
            answer_content_for_summary = "".join(collected_answer_chunks)

            # After the stream is exhausted, get usage from the iterator object
            if hasattr(llm_stream_iterator, 'usage') and llm_stream_iterator.usage:
                answer_prompt_usage = llm_stream_iterator.usage.prompt_tokens
                answer_completion_usage = llm_stream_iterator.usage.completion_tokens
            else:
                logger.warning("Could not retrieve usage info from streaming response.")
                # answer_prompt_usage, answer_completion_usage, answer_total_usage remain 0

        else: # Non-streaming answer
            answer_response_dict = await answer_generator.get_response(
                messages,
                stream=False
            )
            answer_prompt_usage = answer_response_dict.get("prompt_usage", 0)
            answer_completion_usage = answer_response_dict.get("completion_usage", 0)
            answer_content_for_summary = answer_response_dict.get("answer", "")

        metadata = {
            "queries": [q["query"] for q in query_list],
            # "candidate_references": web_contents,
            "sub_titles": outlines,
        }

        # save_path = os.path.join(save_dir, f"{chat_index}.json")
        # async with aiofiles.open(save_path, "w", encoding="utf-8") as f:
        #     await f.write(json.dumps(search_info, ensure_ascii=False, indent=4))

        # 5) 최종 요약
        summary = {
            "status": "complete",
            "message": {
                "content": answer_content_for_summary,
                "metadata": metadata,
                "models": [
                    {
                        "model": {
                            "model_vendor": QUERY_REWRITE_MODEL_INFO['vendor'],
                            "model_type": QUERY_REWRITE_MODEL_INFO['model_type'],
                            "model_name": QUERY_REWRITE_MODEL_NAME,
                        },
                        "usage": {
                            "input_token_count": query_rewrite_prompt_usage,
                            "output_token_count": query_rewrite_completion_usage,
                        },
                    },
                    {
                        "model": {
                            "model_vendor": OUTLINE_GENERATOR_MODEL_INFO['vendor'],
                            "model_type": OUTLINE_GENERATOR_MODEL_INFO['model_type'],
                            "model_name": OUTLINE_GENERATOR_MODEL_NAME,
                        },
                        "usage": {
                            "input_token_count": outline_prompt_usage,
                            "output_token_count": outline_completion_usage,
                        },
                    },
                    {
                        "model": {
                            "model_vendor": "serper",
                            "model_type": "serper",
                            "model_name": "serper",
                        },
                        "usage": {
                            "input_token_count": serper_credits,
                            "output_token_count": 0,
                        },
                    },
                ],
            },
        }
        yield json_line(summary)

        # save web contents to database
        for web_content in web_contents:
            db_payload = {
                "url": web_content.get("url"),
                "title": web_content.get("title"),
                "snippet": web_content.get("snippet"),
                "content": web_content.get("content"),
                "date": web_content.get("date"),
                "language": web_content.get("language"),
                "type": web_content.get("type"),
            }
            db_payload_cleaned = {k: v for k, v in db_payload.items() if v is not None}
            await save_document_to_pg(db_payload_cleaned)

    except asyncio.TimeoutError as exc:
        logger.error("timeout", error=str(exc))
        yield json_line({"status": "failure", "message": {"title": "웹 검색 시간 초과"}})
    except Exception as exc:  # noqa: BLE001
        logger.error("stream_error", error=str(exc))
        yield json_line({"status": "failure", "message": {"title": "웹 검색 실패"}})
    finally:
        await browser_client.aclose()

# ────────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ────────────────────────────────────────────────────────────────────────────────

def main() -> None:
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        workers=8,
        log_config=None,
    )


if __name__ == "__main__":
    main()
