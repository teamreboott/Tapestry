
LLM_TOKEN_INFO = {
    "o1": {
        "price":{
            "input": 15.00 / 1000000,
            "cached": 7.50 / 1000000,
            "output": 60.00 / 1000000,
        },
        "token": {
            "context_window": 200000,
            "max_tokens": 100000,
        },
        "vendor": "openai",
        "reasoning": True,
        "model_type": "o1"
    },
    "o3": {
        "price":{
            "input": 10.00 / 1000000,
            "cached": 2.50 / 1000000,
            "output": 40.00 / 1000000,
        },
        "token": {
            "context_window": 200000,
            "max_tokens": 100000,
        },
        "vendor": "openai",
        "reasoning": True,
        "model_type": "o3"
    },
    "o3-mini": {
        "price":{
            "input": 1.10 / 1000000,
            "cached": 0.55 / 1000000,
            "output": 4.40 / 1000000,
        },
        "token": {
            "context_window": 200000,
            "max_tokens": 100000,
        },
        "vendor": "openai",
        "reasoning": True,
        "model_type": "o3-mini"
    },
    "o4-mini": {
        "price": {
            "input": 1.10 / 1000000,
            "cached": 0.275 / 1000000,
            "output": 4.40 / 1000000,
        },
        "token": {
            "context_window": 200000,
            "max_tokens": 100000,
        },
        "vendor": "openai",
        "reasoning": True,
        "model_type": "o4-mini"
    },
    "gpt-4o": {
        "price": {
            "input": 2.50 / 1000000,
            "cached": 1.25 / 1000000,
            "output": 10.00 / 1000000,
        },
        "token": {
            "context_window": 128000,
            "max_tokens": 16384,
        },
        "vendor": "openai",
        "reasoning": False,
        "model_type": "gpt-4o"
    },
    "gpt-4.1": {
        "price": {
            "input": 2.00 / 1000000,
            "cached": 0.50 / 1000000,
            "output": 8.00 / 1000000,
        },
        "token": {
            "context_window": 1047576,
            "max_tokens": 32768,
        },
        "vendor": "openai",
        "reasoning": False,
        "model_type": "gpt-4.1"
    },
    "gpt-4.1-mini": {
        "price": {
            "input": 0.4 / 1000000,
            "cached": 0.1 / 1000000,
            "output": 1.6 / 1000000,
        },
        "token": {
            "context_window": 1047576,
            "max_tokens": 32768,
        },
        "vendor": "openai",
        "reasoning": False,
        "model_type": "gpt-4.1-mini"
    },
    "gpt-4.1-nano": {
        "price": {
            "input": 0.1 / 1000000,
            "cached": 0.025 / 1000000,
            "output": 0.4 / 1000000,
        },
        "token": {
            "context_window": 1047576,
            "max_tokens": 32768,
        },
        "vendor": "openai",
        "reasoning": False,
        "model_type": "gpt-4.1-nano"
    },
    "claude-3-7-sonnet": {
        "price": {
            "input": 3.0 / 1000000,
            "cached": 0.3 / 1000000,
            "output": 15.0 / 1000000,
        },
        "token": {
            "context_window": 200000,
            "max_tokens": 64000,
        },
        "vendor": "anthropic",
        "reasoning": True,
        "model_type": "claude-3-7-sonnet-thinking"
    },
    "claude-3-5-sonnet": {
        "price": {
            "input": 3.0 / 1000000,
            "cached": 0.3 / 1000000,
            "output": 15.0 / 1000000,
        },
        "token": {
            "context_window": 200000,
            "max_tokens": 8192,
        },
        "vendor": "anthropic",
        "reasoning": False,
        "model_type": "claude-3-5-sonnet"
    },
    "gemini-2.0-flash": {
        "price": {
            "input": 0.1 / 1000000,
            "cached": 0.01 / 1000000,
            "output": 0.4 / 1000000,
        },
        "token": {
            "context_window": 1000000,
            "max_tokens": 64000,
        },
        "vendor": "google",
        "reasoning": False,
        "model_type": "gemini-2.0-flash"
    },
    "gemini-2.5-flash": {
        "price": {
            "input": 0.15 / 1000000,
            "cached": 0.01 / 1000000,
            "output": 0.6 / 1000000,
        },
        "token": {
            "context_window": 1000000,
            "max_tokens": 64000,
        },
        "vendor": "google",
        "reasoning": False,
        "model_type": "gemini-2.5-flash"
    }
}

def get_llm_info(model_name: str):
    for candidate in LLM_TOKEN_INFO.keys():
        if candidate in model_name:
            model = candidate
            break
    return LLM_TOKEN_INFO[model]