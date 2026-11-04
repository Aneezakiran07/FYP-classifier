import os

# Friendly names that map to the exact model string the provider api expects
MODEL_ALIASES = {
    "claude-haiku-4-5": "claude-haiku-4-5-20251001",
    "deepseek-r1": "deepseek-reasoner",
    # Hack Club AI aliases. The value carries the hackclub/ prefix so that
    # provider_for() routes them through the proxy.
    "hackclub-classify": "hackclub/openai/gpt-6-luna",
    "hackclub-resolve": "hackclub/deepseek/deepseek-v4-pro-0813",
    "hackclub-fallback-classify": "hackclub/google/gemini-3.8-flash",
    "hackclub-fallback-resolve": "hackclub/moonshotai/kimi-k3",
}

# Hack Club AI is an OpenAI-compatible proxy
HACKCLUB_BASE_URL = "https://ai.hackclub.com/proxy/v1"
HACKCLUB_PREFIX = "hackclub/"

# One clients cache per provider so a multi model run does not rebuild them
_CLIENTS = {}


class ProviderUnavailable(Exception):
    # Raised when a sdk or key is missing, retrying can never fix this
    pass


def provider_for(model):
    name = model.lower()
    if name.startswith(HACKCLUB_PREFIX):
        return "hackclub"
    if name.startswith("gemini"):
        return "gemini"
    if name.startswith("claude"):
        return "anthropic"
    if name.startswith("deepseek"):
        return "deepseek"
    if name.startswith(("gpt", "o1", "o3", "o4")):
        return "openai"
    raise ProviderUnavailable(f"no provider known for model {model}")


def _key_for(provider):
    if provider == "gemini":
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if provider == "hackclub":
        return os.environ.get("HACKCLUB_API_KEY")
    env_name = {"anthropic": "ANTHROPIC_API_KEY", "deepseek": "DEEPSEEK_API_KEY",
                "openai": "OPENAI_API_KEY"}[provider]
    return os.environ.get(env_name)


def _sdk_module(provider):
    return {"gemini": "google.genai", "anthropic": "anthropic",
            "deepseek": "openai", "openai": "openai",
            "hackclub": "openai"}[provider]


def check_available(model):
    # Returns a pair of ok and a warning message, used to skip a model
    # cleanly before a long multi model run starts. The alias is resolved
    # first so that a friendly name like hackclub-classify is accepted here
    # just as it is inside call_model.
    resolved = MODEL_ALIASES.get(model, model)
    try:
        provider = provider_for(resolved)
    except ProviderUnavailable as e:
        return False, str(e)
    try:
        __import__(_sdk_module(provider))
    except ImportError:
        return False, f"sdk for {provider} is not installed, install {_sdk_module(provider).split('.')[0]}"
    if not _key_for(provider):
        return False, f"no api key found for {provider}"
    return True, ""


def _client(provider):
    if provider in _CLIENTS:
        return _CLIENTS[provider]
    probe = {"gemini": "gemini", "anthropic": "claude",
             "deepseek": "deepseek", "openai": "gpt",
             "hackclub": "hackclub/probe"}[provider]
    ok, warning = check_available(probe)
    if not ok:
        raise ProviderUnavailable(warning)
    if provider == "gemini":
        from google import genai
        client = genai.Client()
    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
    elif provider == "hackclub":
        from openai import OpenAI
        client = OpenAI(api_key=_key_for("hackclub"), base_url=HACKCLUB_BASE_URL)
    else:
        from openai import OpenAI
        base_url = "https://api.deepseek.com" if provider == "deepseek" else None
        client = OpenAI(api_key=_key_for(provider), base_url=base_url)
    _CLIENTS[provider] = client
    return client


def call_model(model, system_instruction, user_message):
    # One function per provider behind a single entry point, any error other
    # than ProviderUnavailable is treated by the caller as retryable.
    #
    # The alias is resolved BEFORE the provider is detected, so that a
    # friendly name such as hackclub-classify is routed correctly. The
    # previous order checked provider_for() on the raw alias, which failed
    # because the alias starts with hackclub- not hackclub/.
    resolved = MODEL_ALIASES.get(model, model)
    provider = provider_for(resolved)
    api_model = resolved
    # A hackclub-prefixed model carries its real OpenRouter slug after the
    # prefix. The proxy expects the slug without the prefix.
    if provider == "hackclub" and api_model.startswith(HACKCLUB_PREFIX):
        api_model = api_model[len(HACKCLUB_PREFIX):]
    client = _client(provider)
    if provider == "gemini":
        from google.genai import types
        response = client.models.generate_content(
            model=api_model, contents=user_message,
            config=types.GenerateContentConfig(system_instruction=system_instruction))
        return response.text
    if provider == "anthropic":
        response = client.messages.create(
            model=api_model, max_tokens=1024, system=system_instruction,
            messages=[{"role": "user", "content": user_message}])
        return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    response = client.chat.completions.create(
        model=api_model,
        messages=[{"role": "system", "content": system_instruction},
                  {"role": "user", "content": user_message}])
    return response.choices[0].message.content