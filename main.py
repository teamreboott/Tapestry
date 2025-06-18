from __future__ import annotations

import asyncio
import json
import os
import structlog
import uvicorn
import uvloop
import time
from enum import Enum
from pydantic import field_validator
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
from src.search.engines import load_search_engine
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

TOTAL_MODEL_USAGE = {}
for model_name in [QUERY_REWRITE_MODEL_NAME, OUTLINE_GENERATOR_MODEL_NAME, ANSWER_GENERATOR_MODEL_NAME]:
    TOTAL_MODEL_USAGE[model_name] = {"model": {"model_vendor": get_llm_info(model_name)['vendor'], "model_type": get_llm_info(model_name)['model_type'], "model_name": model_name}, "usage": {"input_token_count": 0, "output_token_count": 0}}

configure_logging(LOG_FILE)
logger = structlog.get_logger()


query_rewriter = QueryRewriter(model=QUERY_REWRITE_MODEL_NAME, max_tokens=config['models']['query_generator']['max_tokens'])
outline_generator = OutlineGenerator(model=OUTLINE_GENERATOR_MODEL_NAME, max_tokens=config['models']['outline_generator']['max_tokens'])
answer_generator = AnswerGenerator(model=ANSWER_GENERATOR_MODEL_NAME, max_tokens=config['models']['answer_generator']['max_tokens'])

crawler = Crawler(news_list=config['domain_crawler']['news'], blog_list=config['domain_crawler']['blog'], media_list=config['domain_crawler']['media'], use_db_content=config['db']['use_db_content'], max_content_length=20000)

# --------------------------------------------------------------------------------
# FastAPI application & lifespan events
# --------------------------------------------------------------------------------

async def lifespan(app: FastAPI):
    logger.info("Application startup...")

    # TODO: Alembic (migration)

    # Create (or reuse) PostgreSQL tables if use_db_content is True
    if config['db']['use_db_content']:
        create_pg_tables()
    yield


app = FastAPI(title="Web Search API", version="0.1.0", lifespan=lifespan)
semaphore = asyncio.Semaphore(settings.SEMAPHORE_LIMIT)

search_type_map = {
    "auto": "auto",
    "general": "Search",
    "scholar": "Scholar",
    "news": "News",
    "youtube": "Videos",
}


class SearchType(str, Enum):
    auto = "auto"
    general = "general"
    scholar = "scholar"
    news = "news"
    youtube = "youtube"


class Query(BaseModel):
    query: str
    language: str
    search_type: SearchType = SearchType.auto
    messages: list[dict] | None = []
    persona_prompt: str | None = "N/A"
    custom_prompt: str | None = "N/A"
    target_nuance: str | None = "Natural"
    return_process: bool = True
    stream: bool = False
    use_youtube_transcript: bool = False
    top_k: int | str = "auto"

    @field_validator("top_k", mode="before")
    def validate_top_k(cls, v):
        if v is None or v == "auto":
            return "auto"
        if isinstance(v, int):
            return v
        raise ValueError("top_k는 정수 또는 'auto'만 허용됩니다.")


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

    # ================================
    # Initialize components
    # ================================
    history_messages = payload.messages
    num_history_messages = len(history_messages)
    if num_history_messages > 4:
        history_messages = history_messages[-4:]
    query = payload.query.replace('\n', ' ').replace('\t', ' ').strip()
    language = payload.language
    search_type = search_type_map[payload.search_type]
    persona_prompt = payload.persona_prompt
    custom_prompt = payload.custom_prompt
    target_nuance = payload.target_nuance
    return_process = payload.return_process
    stream = payload.stream
    use_youtube_transcript = payload.use_youtube_transcript
    top_k = payload.top_k if isinstance(payload.top_k, int) else None

    if search_type == "Videos":
        use_youtube_transcript = True

    target_language_name = Language.from_code(language).query_params["name"]
    reference_label = Language.from_code(language).query_params["source_tag"]

    answer_prompt_usage = answer_completion_usage = answer_total_usage = 0

    web_engine_client = load_search_engine(engine_name=config['web_search']['engine'],
                                           browser_client=browser_client,
                                           num_output_per_query=config['web_search']['num_output_per_query'],
                                           content_type_timeout=config['web_search']['content_type_timeout'],
                                           use_youtube_transcript=use_youtube_transcript,
                                           top_k=top_k,
                                           exclude_domain=config['exclude_domain'])

    if return_process:
        yield json_line({"status": "processing", "message": {"title": "Analyzing the question..."}})

    try:
        query_list = []
        if len(query) > 100:
            num_samples = config['web_search']['n_queries']
        else:
            num_samples = max(config['web_search']['n_queries'] - 1, 1)
            if search_type == "auto" or search_type == "Search":
                query_list.append({"query": query, "type": "Search", "language": language, "period": "Any time"})
            else:
                query_list.append({"query": query, "type": search_type, "language": language, "period": "Any time"})

        date_str = query_rewriter.get_date()

        if num_history_messages > 0:
            prompt = prompts['web_prompt_history'].format(history=history_messages, query=query, date=date_str, num_samples=num_samples, target_language=target_language_name, request_search_type=search_type)
        else:
            prompt = prompts['web_prompt'].format(query=query, date=date_str, num_samples=num_samples, target_language=target_language_name, request_search_type=search_type)

        if num_history_messages == 0 and is_url(query):
            use_search_engine = False
            pass
        else:
            use_search_engine = True
            response = await query_rewriter.get_response([{"role": "user", "content": prompt}])

            TOTAL_MODEL_USAGE[QUERY_REWRITE_MODEL_NAME]['usage']['input_token_count'] += response.get("prompt_usage", 0)
            TOTAL_MODEL_USAGE[QUERY_REWRITE_MODEL_NAME]['usage']['output_token_count'] += response.get("completion_usage", 0)
            total_answers = response.get("answer", [])

            if len(total_answers) != 0:
                query_list.extend(total_answers)

            urls = extract_urls(query)
            for url in urls:
                query_list.append({"query": url, "type": "Search", "language": "ko"})

        if len(query_list) == 0:
            yield json_line({"status": "failure", "data": {"title": "I couldn't understand the question."}})
            return

        if return_process:
            yield json_line({"status": "processing", "message": {"title": "Searching for related questions..."}})

        if use_search_engine:
            scraped_sources = await web_engine_client.multiple_search(query_list)
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

        if total_results == 0:
            logger.error("no_results", query=query, message="No web search results found.")
            yield json_line({"status": "failure", "message": {"title": "No web search results found."}})
            return
        
        console.print(f"[green]Crawler-Extract: {query_list}")

        merged_query = " ".join([q["query"] for q in query_list])
        merged_content = ""
        for src in scraped_sources:
            title = src.get("title", "")
            snippet = src.get("snippet", "")
            merged_content += f"{title}: {snippet}\n"

        if return_process:
            yield json_line({"status": "processing", "message": {"title": f"Searching {total_results} search results..."}})

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
            crawl_task = crawler.multiple_crawl(browser_client, scraped_sources)
            outline_results, web_contents = await asyncio.gather(outline_task, crawl_task)

        else:
            web_contents = await crawler.crawl(browser_client, scraped_sources[0])
            web_contents = [web_contents]
            url_content = web_contents[0]['content']
            outline_prompt = prompts['outline_prompt'].format(query=query, content=url_content, target_language=target_language_name)
            outline_results = await get_outlines(outline_prompt)
            outlines = outline_results.get("outlines", [])

        TOTAL_MODEL_USAGE[OUTLINE_GENERATOR_MODEL_NAME]['usage']['input_token_count'] += outline_results.get("prompt_usage", 0)
        TOTAL_MODEL_USAGE[OUTLINE_GENERATOR_MODEL_NAME]['usage']['output_token_count'] += outline_results.get("completion_usage", 0)

        outlines = outline_results.get("outlines", [])

        end_time = time.time()
        execution_time = end_time - start_time
        console.print(f"[pink bold]Processing time: {execution_time:.2f} seconds")

        if return_process:
            yield json_line({"status": "processing", "message": {"title": "Web search completed"}})

        answer_content_for_summary = ""
        today_date = date_str
        sub_titles = str(outlines)
        prompt_web_search = json.dumps(web_contents)

        answer_prompt = prompts['answer_prompt'].format(persona_prompt=persona_prompt, 
                                                        custom_prompt=custom_prompt, 
                                                        target_language=target_language_name, 
                                                        target_nuance=target_nuance, 
                                                        reference_label=reference_label, 
                                                        today_date=today_date, 
                                                        sub_titles=sub_titles, 
                                                        prompt_web_search=prompt_web_search)
        if num_history_messages > 0:
            messages = history_messages + [{"role": "user", "content": answer_prompt}]
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
                if hasattr(chunk, "usage") and chunk.usage is not None:
                    TOTAL_MODEL_USAGE[ANSWER_GENERATOR_MODEL_NAME]['usage']['input_token_count'] += chunk.usage.prompt_tokens
                    TOTAL_MODEL_USAGE[ANSWER_GENERATOR_MODEL_NAME]['usage']['output_token_count'] += chunk.usage.completion_tokens
                    break
                # Make sure chunk and its attributes are not None
                if chunk and chunk.choices and chunk.choices[0].delta:
                    token_text = chunk.choices[0].delta.content
                    if token_text is not None: # Ensure content is not None
                        collected_answer_chunks.append(token_text)
                        # Yield in the format requested by the user
                        yield json_line({"status": "streaming", "delta": {"content": token_text}})
            
            answer_content_for_summary = "".join(collected_answer_chunks)

        else: # Non-streaming answer
            answer_response_dict = await answer_generator.get_response(
                messages,
                stream=False
            )
            answer_prompt_usage = answer_response_dict.get("prompt_usage", 0)
            answer_completion_usage = answer_response_dict.get("completion_usage", 0)
            TOTAL_MODEL_USAGE[ANSWER_GENERATOR_MODEL_NAME]['usage']['input_token_count'] += answer_prompt_usage
            TOTAL_MODEL_USAGE[ANSWER_GENERATOR_MODEL_NAME]['usage']['output_token_count'] += answer_completion_usage
            answer_content_for_summary = answer_response_dict.get("answer", "")

        metadata = {
            "queries": [q["query"] for q in query_list],
            "sub_titles": outlines,
        }

        usages = []
        for k, v in TOTAL_MODEL_USAGE.items():
            usages.append(v)

        # 5) 최종 요약
        summary = {
            "status": "complete",
            "message": {
                "content": answer_content_for_summary,
                "metadata": metadata,
                "models": usages,
            },
        }
        yield json_line(summary)

        # save web contents to database
        if config['db']['save_content_to_db']:
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
        yield json_line({"status": "failure", "message": {"title": "Web search timeout"}})
    except Exception as exc:  # noqa: BLE001
        logger.error("stream_error", error=str(exc))
        yield json_line({"status": "failure", "message": {"title": "Web search failed"}})
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