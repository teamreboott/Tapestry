import gradio as gr
import asyncio
import aiohttp
import json
from rich import print as rprint
from rich.panel import Panel
from rich.syntax import Syntax
import os

# --- Server URL Configuration ---
SERVER_URL = os.environ.get("API_URL", "http://127.0.0.1:9012/websearch")
GRADIO_PORT = int(os.environ.get("GRADIO_PORT", "80"))
TIMEOUT = 180

# --- Language Mapping ---
LANG_DISPLAY_TO_CODE = {
    "English": "en",
    "한국어": "ko",
    "中文": "zh",
    "日本語": "ja"
}

# --- UI & Logic Functions ---

async def respond(
        chat_history,
        language,
        search_type="auto",
        persona_prompt="N/A",
        custom_prompt="N/A",
        target_nuance="Natural",
        stream_flag=True,
        youtube_flag=False,
        top_k=None):
    """
    Receives user messages and sends streaming requests to the backend API,
    displaying responses in real-time in the chatbot UI.
    """
    message = chat_history[-1][0]
    if not message:
        yield chat_history
        return

    # Convert chat history to messages array
    messages = []
    for user_msg, bot_msg in chat_history[:-1]:  # Exclude last message (no response yet)
        if user_msg:
            messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})

    payload = {
        "language": language,
        "query": message,
        "search_type": search_type,
        "persona_prompt": persona_prompt,
        "custom_prompt": custom_prompt,
        "target_nuance": target_nuance,
        "messages": messages,
        "stream": stream_flag,
        "use_youtube_transcript": youtube_flag,
        "top_k": top_k,
    }

    # messages의 content를 15글자까지만 보이게 변환 (터미널 출력용)
    payload_for_print = json.loads(json.dumps(payload))  # deep copy
    for msg in payload_for_print["messages"]:
        if "content" in msg and len(msg["content"]) > 15:
            msg["content"] = msg["content"][:15] + "..."

    json_str = json.dumps(payload_for_print, ensure_ascii=False, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    rprint(Panel(syntax, title="[bold green]API PAYLOAD[/]", expand=False))

    bot_message = ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SERVER_URL, json=payload, timeout=TIMEOUT) as response:
                response.raise_for_status()
                async for line in response.content:
                    data_str = line.decode("utf-8").strip()
                    if data_str:
                        data_json = json.loads(data_str)
                        status = data_json.get("status")
                        
                        if status == "processing":
                            title = data_json.get("message", {}).get("title", "Processing...")
                            chat_history[-1] = (message, f"*{title}*")
                        elif status == "streaming":
                            delta = data_json.get("delta", {}).get("content", "")
                            if bot_message.startswith("*"):
                                bot_message = ""
                            bot_message += delta
                            chat_history[-1] = (message, bot_message)
                        elif status == "complete":
                            content = data_json.get("message", {}).get("content")
                            if content:
                                chat_history[-1] = (message, content)
                            break
                        elif status == "success":
                            content = data_json.get("message", {}).get("content")
                            if content:
                                chat_history[-1] = (message, content)
                            break
                        elif status == "failure":
                            error_msg = data_json.get("message", "An error occurred while processing the request.")
                            chat_history[-1] = (message, f"Error: {error_msg}")
                            break
                        
                        yield chat_history
    except Exception as e:
        chat_history[-1] = (message, f"Error: {e}")
        yield chat_history

css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary-color: #6366f1;
    --primary-hover: #5856eb;
    --background-primary: #fafbfc;
    --background-secondary: #ffffff;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --border-hover: #d1d5db;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --radius-sm: 0.5rem;
    --radius-md: 0.75rem;
    --radius-lg: 1rem;
    --radius-xl: 1.5rem;
    --user-bubble-color: linear-gradient(135deg, #6366f1, #818cf8);
    --bot-bubble-color: #eef2ff; /* Light indigo */
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.gradio-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    min-height: 100vh;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

.main {
    background: transparent !important;
    width: 100% !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 1.5rem !important;
}

/* 채팅 헤더 */
.chat-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 1rem 2rem !important;
    border-bottom: 1px solid var(--border-color) !important;
    position: relative !important;
    z-index: 20 !important;
}

.chat-header h2 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
}

#new-chat-btn {
    background: var(--background-primary) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

#new-chat-btn:hover {
    background: var(--border-color) !important;
    border-color: var(--border-hover) !important;
}

/* 채팅 컨테이너 */
.chat-container {
    background: var(--background-secondary) !important;
    border-radius: var(--radius-xl) !important;
    box-shadow: var(--shadow-lg) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden !important;
    height: 95vh !important;
    display: flex !important;
    flex-direction: column !important;
    position: relative !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* 환영 메시지 */
#welcome-container {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
    padding: 2rem !important;
    text-align: center !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 110px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    overflow-y: auto !important;
    z-index: 10 !important;
    pointer-events: none !important; /* Allow clicks to pass through so Advanced Options accordion remains interactive before chat starts */
}

#welcome-container h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin-bottom: 1rem !important;
    line-height: 1.2 !important;
}

#welcome-container .subtitle {
    font-size: 1.1rem !important;
    color: var(--text-secondary) !important;
    max-width: 600px !important;
    width: auto !important;
    margin: 0 auto 2.5rem !important;
    text-align: center !important;
}

/* 챗봇 UI */
#chatbot {
    flex: 1 !important;
    border: none !important;
    box-shadow: none !important;
    background: linear-gradient(180deg, rgba(249, 250, 255, 0.8) 0%, rgba(255, 255, 255, 0.8) 60%) !important;
    padding: 0.5rem !important;
    padding-bottom: 125px !important;
    overflow-y: auto !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
}

/* 말풍선 겹침 문제 해결 및 너비 조정 */
#chatbot .message-wrap {
    background: transparent !important;
    border: none !important;
    padding: 0.2rem 0 !important;
    display: flex !important;
    flex-direction: column !important;
    margin-bottom: 0.4rem !important;
}

#chatbot .message {
    padding: 0 !important;
    background: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    max-width: 100% !important;
    border: none !important;
}

#chatbot .message::before,
#chatbot .message::after {
    display: none !important;
}

#chatbot .message.user > .message-body,
#chatbot .message.bot > .message-body {
    padding: 0.8rem 1.2rem !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
    width: fit-content !important;
    width: -moz-fit-content !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
    max-width: 80% !important;
}

#chatbot .message.user {
    align-self: flex-end !important;
}

#chatbot .message.bot {
    justify-content: flex-start;
}

#chatbot .message.user > .message-body {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(229, 231, 235, 0.6) !important; /* subtle border */
}

#chatbot .message.bot > .message-body {
    background: linear-gradient(135deg, #f3f4f6 0%, #eef2ff 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(229, 231, 235, 0.6) !important; /* subtle border */
    box-shadow: var(--shadow-sm) !important;
}

/* === 신규: DOM 구조에 .message-body 가 없을 경우를 대비해 직접 .message 요소에 배경 적용 === */
#chatbot .message.user,
#chatbot .message.bot {
    padding: 0.8rem 1.2rem !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
    width: fit-content !important;
    width: -moz-fit-content !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
    max-width: 80% !important;
}

#chatbot .message.user {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(229, 231, 235, 0.6) !important; /* subtle border */
}

#chatbot .message.bot {
    background: linear-gradient(135deg, #f3f4f6 0%, #eef2ff 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(229, 231, 235, 0.6) !important; /* subtle border */
}

/* 아바타 이미지 스타일 */
#chatbot .avatar-container {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    min-height: 48px !important;
    border-radius: 50% !important;
    background: #fff !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    box-shadow: 0 0 0 1px #e5e7eb;
}

#chatbot .avatar-container img {
    width: 100% !important;
    height: 100% !important;
    object-fit: contain !important;  /* cover로 해도 되지만, contain이 로고에 더 적합할 수 있음 */
    border-radius: 50% !important;
    background: transparent !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* 입력 영역 */
.input-area {
    background: var(--background-secondary) !important;
    padding: 1rem 1.5rem !important;
    border-top: 1px solid var(--border-color) !important;
    border-bottom-left-radius: var(--radius-xl) !important;
    border-bottom-right-radius: var(--radius-xl) !important;
    position: absolute !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 1000 !important;
    max-width: none !important;
    width: 100% !important;
    margin: 0 auto !important;
}

#input-row {
    background: var(--background-primary) !important;
    border: 2px solid var(--border-color) !important;
    border-radius: var(--radius-xl) !important;
    padding: 0.75rem !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-sm) !important;
    display: flex !important;
    align-items: center !important;
    gap: 1rem !important;
    width: 80% !important;
    max-width: none !important;
    margin: 0 auto !important;
    min-height: 48px !important;
}

#input-row:focus-within {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}

#message-input {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    padding: 0.5rem 0 !important;
    flex: 1 !important;
    outline: none !important;
    resize: none !important;
    overflow-y: auto !important;
    max-height: 200px !important;
    min-height: 24px !important;
}

#message-input::-webkit-scrollbar {
    width: 6px !important;
}

#message-input::-webkit-scrollbar-track {
    background: transparent !important;
}

#message-input::-webkit-scrollbar-thumb {
    background: var(--border-color) !important;
    border-radius: 3px !important;
}

#message-input::-webkit-scrollbar-thumb:hover {
    background: var(--border-hover) !important;
}

#message-input::placeholder {
    color: var(--text-secondary) !important;
    font-weight: 400 !important;
}

#submit-button {
    background: linear-gradient(135deg, var(--primary-color), var(--primary-hover)) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    width: 36px !important;
    height: 36px !important;
    color: white !important;
    font-size: 1rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: var(--shadow-sm) !important;
    flex-shrink: 0 !important;
}

#submit-button:hover {
    background: linear-gradient(135deg, var(--primary-hover), var(--primary-color)) !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-2px) !important;
}

#submit-button:active {
    transform: scale(0.98) !important;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .main {
        padding: 0 !important;
        height: 100vh;
    }
    .chat-container {
        border-radius: 0 !important;
        height: 100% !important;
    }
    
    .chat-header {
        padding: 0.75rem 1rem !important;
    }

    #welcome-container {
        padding: 2rem 1rem !important;
    }
    
    #welcome-container h1 {
        font-size: 2.2rem !important;
    }
    
    #chatbot .message.user > .message-body,
    #chatbot .message.bot > .message-body {
        max-width: 90% !important;
    }
    
    #input-row {
        padding: 0.5rem !important;
        max-width: 100% !important;
    }
    .input-area {
        padding: 0.75rem !important;
    }
}

/* 스크롤바 */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--background-primary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--border-hover);
}

/* 로딩 애니메이션 */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* JavaScript로 강제 숨김 처리 */
.force-hidden {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -999 !important;
    position: absolute !important;
    top: -9999px !important;
    left: -9999px !important;
}

/* 강제로 최우선 적용 */
#chatbot .message.user,
#chatbot .message.bot {
    min-width: 0 !important;
    max-width: 800px !important;
    width: fit-content !important;
    flex-shrink: 0 !important;
    word-wrap: break-word !important;
    white-space: normal !important;
    overflow-wrap: break-word !important;
}
"""

# JavaScript 함수 - 개선된 robust 버전
js_code = """
// 전역 상태 관리
let chatStarted = false;
let accordionOpen = false;
let debugMode = false; // 디버깅용

function log(message, data = null) {
    if (debugMode) {
        console.log('[Welcome Control]', message, data || '');
    }
}

function hideWelcomeContainer() {
    const welcomeContainer = document.getElementById('welcome-container');
    if (welcomeContainer) {
        welcomeContainer.style.display = 'none';
        welcomeContainer.style.visibility = 'hidden';
        welcomeContainer.style.opacity = '0';
        welcomeContainer.style.pointerEvents = 'none';
        welcomeContainer.style.zIndex = '-999';
        welcomeContainer.classList.add('force-hidden');
        
        const parentCol = welcomeContainer.closest('.gr-column');
        if (parentCol) {
            parentCol.style.display = 'none';
        }
    }
}

function showWelcomeContainer() {
    const welcomeContainer = document.getElementById('welcome-container');
    if (welcomeContainer) {
        welcomeContainer.style.display = 'flex';
        welcomeContainer.style.visibility = 'visible';
        welcomeContainer.style.opacity = '1';
        welcomeContainer.style.pointerEvents = 'auto';
        welcomeContainer.style.zIndex = '10';
        welcomeContainer.classList.remove('force-hidden');
        
        const parentCol = welcomeContainer.closest('.gr-column');
        if (parentCol) {
            parentCol.style.display = 'flex';
        }
    }
}

function updateWelcomeVisibility() {
    const welcomeContainer = document.getElementById('welcome-container');
    if (!welcomeContainer) {
        log('Welcome container not found');
        return;
    }
    
    log('Updating welcome visibility', {chatStarted, accordionOpen});
    
    // 채팅이 시작된 경우 항상 웰컴 메시지 숨김
    if (chatStarted) {
        log('Chat started - hiding welcome');
        welcomeContainer.classList.add('force-hidden');
        return;
    }
    
    // 채팅이 시작되지 않은 경우 아코디언 상태에 따라 결정
    if (accordionOpen) {
        log('Accordion open - hiding welcome');
        welcomeContainer.classList.add('force-hidden');
    } else {
        log('Accordion closed - showing welcome');
        welcomeContainer.classList.remove('force-hidden');
    }
}

function checkAccordionState() {
    const accordion = document.getElementById('advanced-options-accordion');
    if (!accordion) {
        log('Accordion not found');
        return false;
    }
    
    let results = [];
    
    // Method 1: details 태그 체크
    const details = accordion.querySelector('details');
    if (details) {
        const isOpen = details.open;
        log('Method 1 - details element', {open: isOpen});
        results.push({method: 'details', result: isOpen});
    }
    
    // Method 2: aria-expanded 체크
    const button = accordion.querySelector('[aria-expanded]');
    if (button) {
        const expanded = button.getAttribute('aria-expanded') === 'true';
        log('Method 2 - aria-expanded', {expanded});
        results.push({method: 'aria-expanded', result: expanded});
    }
    
    // Method 3: 내용 영역의 가시성 체크 (개선된 셀렉터)
    const selectors = [
        '.gr-form', '.gradio-form', '[class*="form"]',
        '.gr-box', '.gradio-box', '[class*="box"]',
        '.gr-column:not(:first-child)', // 첫 번째가 아닌 컬럼 (보통 내용)
        '.gr-row:not(:first-child)',   // 첫 번째가 아닌 로우
    ];
    
    for (let selector of selectors) {
        const content = accordion.querySelector(selector);
        if (content) {
            const rect = content.getBoundingClientRect();
            const isVisible = content.offsetHeight > 0 && 
                            window.getComputedStyle(content).display !== 'none' &&
                            rect.height > 0;
            log(`Method 3 - content area (${selector})`, {
                visible: isVisible, 
                offsetHeight: content.offsetHeight,
                rectHeight: rect.height,
                display: window.getComputedStyle(content).display
            });
            results.push({method: `content-${selector}`, result: isVisible});
            if (isVisible) break; // 하나라도 보이면 열린 것
        }
    }
    
    // Method 4: 클래스 기반 체크 (더 많은 클래스 확인)
    const openClasses = ['open', 'expanded', 'active', 'show', 'visible'];
    for (let className of openClasses) {
        if (accordion.classList.contains(className)) {
            log('Method 4 - open class found', {className});
            results.push({method: `class-${className}`, result: true});
        }
    }
    
    // Method 5: 자식 요소들의 가시성 체크 (개선됨)
    const allChildren = accordion.querySelectorAll('*');
    let visibleContentCount = 0;
    let totalHeight = 0;
    
    for (let child of allChildren) {
        const rect = child.getBoundingClientRect();
        const styles = window.getComputedStyle(child);
        
        if (rect.height > 0 && 
            styles.display !== 'none' && 
            styles.visibility !== 'hidden' &&
            !child.closest('button')) { // 버튼 안에 있지 않은 요소
            visibleContentCount++;
            totalHeight += rect.height;
        }
    }
    
    const hasVisibleContent = visibleContentCount > 2 && totalHeight > 100; // 임계값 조정
    log('Method 5 - visible children analysis', {
        visibleContentCount, 
        totalHeight, 
        hasVisibleContent
    });
    results.push({method: 'visible-children', result: hasVisibleContent});
    
    // Method 6: 아코디언 자체의 높이 체크
    const accordionRect = accordion.getBoundingClientRect();
    const isExpanded = accordionRect.height > 60; // 닫힌 상태보다 높음
    log('Method 6 - accordion height', {
        height: accordionRect.height,
        isExpanded
    });
    results.push({method: 'accordion-height', result: isExpanded});
    
    // 결과 분석
    log('All method results', results);
    
    // true인 결과가 하나라도 있으면 열린 것으로 판단
    const finalResult = results.some(r => r.result === true);
    log('Final accordion state', {finalResult});
    
    return finalResult;
}

function setupChatObserver() {
    const chatbot = document.getElementById('chatbot');
    if (!chatbot) {
        log('Chatbot not found, retrying...');
        setTimeout(setupChatObserver, 100);
        return;
    }
    
    log('Setting up chat observer');
    
    // chatbot의 가시성 변화를 감지하는 observer
    const chatbotObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && 
                (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
                
                const chatbotVisible = chatbot.style.display !== 'none' && 
                                     !chatbot.classList.contains('hidden') &&
                                     window.getComputedStyle(chatbot).display !== 'none';
                
                if (chatbotVisible && !chatStarted) {
                    log('Chat started detected');
                    chatStarted = true;
                    updateWelcomeVisibility();
                }
            }
        });
    });
    
    // chatbot의 부모 요소들도 관찰
    let element = chatbot;
    while (element) {
        chatbotObserver.observe(element, {
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        element = element.parentElement;
        if (element && element.classList.contains('gradio-container')) break;
    }
}

function setupAccordionObserver() {
    const accordion = document.getElementById('advanced-options-accordion');
    if (!accordion) {
        log('Accordion not found, retrying...');
        setTimeout(setupAccordionObserver, 200);
        return;
    }
    
    log('Setting up accordion observer');
    
    // 초기 상태 확인
    const initialState = checkAccordionState();
    accordionOpen = initialState;
    log('Initial accordion state', {accordionOpen});
    updateWelcomeVisibility();
    
    // 1. 클릭 이벤트 캐처 (가장 확실한 방법)
    accordion.addEventListener('click', function(e) {
        log('Accordion clicked', {target: e.target.tagName});
        
        // 클릭 후 상태 확인 (여러 시점에서)
        setTimeout(() => {
            const newState = checkAccordionState();
            if (newState !== accordionOpen) {
                log('Accordion state changed via click', {from: accordionOpen, to: newState});
                accordionOpen = newState;
                updateWelcomeVisibility();
            }
        }, 50);
        
        setTimeout(() => {
            const newState = checkAccordionState();
            if (newState !== accordionOpen) {
                log('Accordion state changed via click (delayed)', {from: accordionOpen, to: newState});
                accordionOpen = newState;
                updateWelcomeVisibility();
            }
        }, 200);
    }, true); // capture phase
    
    // 2. MutationObserver로 모든 변화 감지
    const accordionObserver = new MutationObserver(function(mutations) {
        let shouldCheck = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes') {
                if (['style', 'class', 'aria-expanded', 'open'].includes(mutation.attributeName)) {
                    shouldCheck = true;
                }
            } else if (mutation.type === 'childList') {
                shouldCheck = true;
            }
        });
        
        if (shouldCheck) {
            const newState = checkAccordionState();
            if (newState !== accordionOpen) {
                log('Accordion state changed via mutation', {from: accordionOpen, to: newState});
                accordionOpen = newState;
                updateWelcomeVisibility();
            }
        }
    });
    
    // 아코디언과 모든 자식 요소 관찰
    accordionObserver.observe(accordion, {
        attributes: true,
        childList: true,
        subtree: true,
        attributeFilter: ['style', 'class', 'aria-expanded', 'open']
    });
    
    // 3. 주기적 상태 체크 (fallback)
    setInterval(() => {
        const newState = checkAccordionState();
        if (newState !== accordionOpen) {
            log('Accordion state changed via polling', {from: accordionOpen, to: newState});
            accordionOpen = newState;
            updateWelcomeVisibility();
        }
    }, 1000);
}

function resetChatState() {
    log('Resetting chat state');
    chatStarted = false;
    accordionOpen = false;
    updateWelcomeVisibility();
}

// DOM 로딩 완료 후 초기화
function initialize() {
    log('Initializing welcome control system');
    
    // 초기화
    setupChatObserver();
    setupAccordionObserver();
    
    // 휴지통 아이콘 클릭 이벤트 처리
    document.addEventListener('click', function(e) {
        if (e.target.closest('.message-actions')) {
            e.preventDefault();
            e.stopPropagation();
            // New chat 버튼 클릭 이벤트 트리거
            const newChatBtn = document.getElementById('new-chat-btn');
            if (newChatBtn) {
                newChatBtn.click();
            }
        }
    });
    
    // 전역 함수로 등록 (디버깅용)
    window.checkAccordionState = checkAccordionState;
    window.updateWelcomeVisibility = updateWelcomeVisibility;
    window.resetChatState = resetChatState;
}

// 여러 시점에서 초기화 시도
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

// Gradio 로딩 완료 후에도 시도
setTimeout(initialize, 1000);
setTimeout(initialize, 3000);
"""

# JavaScript helper to hide welcome container but still pass inputs to Python
hide_and_pass_js = """
function(text, history) {
    // 채팅이 시작됨을 표시
    chatStarted = true;
    updateWelcomeVisibility();
    return [text, history];
}
"""

# New chat 버튼을 위한 JavaScript
show_welcome_js = """
function() {
    resetChatState();
}
"""

# 다크 모드 비활성화
theme = gr.themes.Soft(primary_hue="indigo", secondary_hue="purple")

# 다크 모드 속성을 라이트 모드 값으로 설정하기 위한 맵
# Gradio 버전에 따라 존재하지 않을 수 있는 속성을 안전하게 처리
dark_to_light_map = {
    # General
    "body_background_fill_dark": "body_background_fill",
    "body_text_color_dark": "body_text_color",
    "text_color_subdued_dark": "text_color_subdued",
    "background_fill_primary_dark": "background_fill_primary",
    "background_fill_secondary_dark": "background_fill_secondary",
    
    # Blocks
    "block_background_fill_dark": "block_background_fill",
    "block_border_color_dark": "block_border_color",
    "block_label_background_fill_dark": "block_label_background_fill",
    "block_label_text_color_dark": "block_label_text_color",
    "block_title_text_color_dark": "block_title_text_color",

    # Inputs (Textbox, Checkbox, etc.)
    "input_background_fill_dark": "input_background_fill",
    "input_border_color_dark": "input_border_color",
    "input_placeholder_color_dark": "input_placeholder_color",
    
    # Buttons
    "button_primary_background_fill_dark": "button_primary_background_fill",
    "button_primary_text_color_dark": "button_primary_text_color",
    "button_secondary_background_fill_dark": "button_secondary_background_fill",
    "button_secondary_text_color_dark": "button_secondary_text_color",
    "button_cancel_background_fill_dark": "button_cancel_background_fill",
    "button_cancel_text_color_dark": "button_cancel_text_color",
    
    # Accent colors (often used for checkboxes, sliders, etc.)
    "border_color_accent_dark": "border_color_accent",
    "color_accent_soft_dark": "color_accent_soft",

    # Other
    # "shadow_drop_dark": "shadow_drop",
    # "shadow_drop_lg_dark": "shadow_drop_lg",
}

settings_to_apply = {}
for dark_attr, light_attr in dark_to_light_map.items():
    if hasattr(theme, light_attr):
        settings_to_apply[dark_attr] = getattr(theme, light_attr)

theme.set(**settings_to_apply)

with gr.Blocks(
    theme=theme,
    title="🌐 Tapestry Web Search",
    css=css,
    head=f"<script>{js_code}</script>"
) as demo:
    
    with gr.Column(elem_classes=["main"]):
        # --- 메인 채팅 영역 ---
        with gr.Column(elem_classes=["chat-container"]):
            with gr.Row(elem_classes=["chat-header"]):
                gr.Markdown("<h2>🌐 Tapestry Web Search</h2>")
                new_chat_btn = gr.Button("✨ New chat", elem_id="new-chat-btn")

            # 추가 옵션 UI (검색 타입, 프롬프트 등)
            with gr.Accordion("🔧 Advanced Options", open=False, elem_id="advanced-options-accordion"):
                # 1행: Language / Search Type / Target Nuance (3열)
                with gr.Row():
                    language_dropdown = gr.Dropdown(
                        choices=["English", "한국어", "中文", "日本語"],
                        value="English",
                        label="Language",
                        multiselect=False,
                        elem_id="language-dropdown",
                        scale=1
                    )
                    search_type_dropdown = gr.Dropdown(
                        choices=["auto", "general", "scholar", "news", "youtube"],
                        value="auto",
                        label="Search Type",
                        scale=1
                    )
                    target_nuance_dropdown = gr.Dropdown(
                        choices=["Natural", "Formal", "Friendly", "Technical"],
                        value="Natural",
                        label="Target Nuance",
                        scale=1
                    )

                # 2행: Stream Output / YouTube Transcript (2열)
                with gr.Row():
                    stream_checkbox = gr.Checkbox(value=True, label="Stream Output", scale=1)
                    youtube_checkbox = gr.Checkbox(value=False, label="Use YouTube Transcript", scale=1)

                # 나머지 옵션들 (한 줄씩)
                persona_prompt_tb = gr.Textbox(label="Persona Prompt", value="")
                custom_prompt_tb = gr.Textbox(label="Custom Prompt", value="")
                topk_slider = gr.Slider(minimum=0, maximum=20, step=1, value=0, label="Top K (0 = auto)")

            # 환영 메시지
            with gr.Column(elem_id="welcome-container", visible=True) as welcome_col:
                gr.Markdown("""
<h1>Welcome!</h1>
<p class='subtitle'>Ask me anything.</p>
""")

            # 챗봇 UI
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                type="messages",
                avatar_images=(None, "logo.png"),
                visible=False,
                show_label=False,
                container=False
            )

            # 입력 영역
            with gr.Column(elem_classes=["input-area"]):
                with gr.Row(elem_id="input-row"):
                    textbox = gr.Textbox(
                        container=False,
                        show_label=False,
                        placeholder="Type your message here...",
                        elem_id="message-input",
                        scale=1,
                        lines=1,
                        max_lines=5,
                        interactive=True
                    )
                    submit_btn = gr.Button("↑", elem_id="submit-button", scale=0)

    # --- 이벤트 핸들러 ---
    
    def handle_message_submit(text_input, chat_history):
        if not text_input or not text_input.strip():
            return {chatbot: chat_history or [], textbox: "", welcome_col: gr.update()}
            
        if chat_history is None:
            chat_history = []
        
        new_history = chat_history + [{"role": "user", "content": text_input}]
        
        return {
            welcome_col: gr.update(visible=False),
            chatbot: gr.update(visible=True, value=new_history),
            textbox: ""
        }

    async def respond_wrapper(history, selected_language_label, search_type, persona_prompt, custom_prompt, target_nuance, stream_flag, youtube_flag, top_k_value):
        if not history:
            yield []
            return

        # messages 형식을 tuple 형식으로 변환
        tuple_history = []
        i = 0
        while i < len(history):
            user_msg = history[i]["content"] if i < len(history) else ""
            bot_msg = history[i+1]["content"] if (i+1) < len(history) and history[i+1]["role"] == "assistant" else None
            tuple_history.append((user_msg, bot_msg))
            i += 2

        language_code = LANG_DISPLAY_TO_CODE.get(selected_language_label, "en")

        # top_k 값 처리 (0 또는 None → auto)
        top_k = None if (top_k_value in [0, None, ""]) else int(top_k_value)

        # API 호출 및 응답 처리
        async for updated_tuple_history in respond(
                tuple_history,
                language_code,
                search_type,
                persona_prompt,
                custom_prompt,
                target_nuance,
                stream_flag,
                youtube_flag,
                top_k):
            messages_history = []
            for user_msg, bot_msg in updated_tuple_history:
                messages_history.append({"role": "user", "content": user_msg})
                if bot_msg is not None:
                    messages_history.append({"role": "assistant", "content": bot_msg})
            yield messages_history

    # 메시지 전송 이벤트 (버튼 클릭과 엔터 키 모두 동일하게 처리)
    submit_event = submit_btn.click(
        fn=handle_message_submit,
        inputs=[textbox, chatbot],
        outputs=[welcome_col, chatbot, textbox],
        queue=False,
        js=hide_and_pass_js
    ).then(
        fn=respond_wrapper, 
        inputs=[chatbot, language_dropdown, search_type_dropdown, persona_prompt_tb, custom_prompt_tb, target_nuance_dropdown, stream_checkbox, youtube_checkbox, topk_slider], 
        outputs=[chatbot]
    )
    
    # 엔터 키로도 동일한 이벤트 실행
    textbox.submit(
        fn=handle_message_submit,
        inputs=[textbox, chatbot],
        outputs=[welcome_col, chatbot, textbox],
        queue=False,
        js=hide_and_pass_js
    ).then(
        fn=respond_wrapper, 
        inputs=[chatbot, language_dropdown, search_type_dropdown, persona_prompt_tb, custom_prompt_tb, target_nuance_dropdown, stream_checkbox, youtube_checkbox, topk_slider], 
        outputs=[chatbot]
    )

    def on_new_chat():
        return {
            chatbot: gr.update(value=[], visible=False),
            textbox: gr.update(value=""),
            welcome_col: gr.update(visible=True),
            language_dropdown: gr.update(value="English"),
            search_type_dropdown: gr.update(value="auto"),
            persona_prompt_tb: gr.update(value=""),
            custom_prompt_tb: gr.update(value=""),
            target_nuance_dropdown: gr.update(value="Natural"),
            stream_checkbox: gr.update(value=True),
            youtube_checkbox: gr.update(value=False),
            topk_slider: gr.update(value=0)
        }

    new_chat_btn.click(
        fn=on_new_chat, 
        inputs=None, 
        outputs=[chatbot, textbox, welcome_col, language_dropdown, search_type_dropdown, persona_prompt_tb, custom_prompt_tb, target_nuance_dropdown, stream_checkbox, youtube_checkbox, topk_slider], 
        queue=False,
        js=show_welcome_js
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch(share=False, server_name="0.0.0.0", server_port=GRADIO_PORT)