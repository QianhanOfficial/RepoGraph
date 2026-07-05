# SSL fix for Python 3.9 on Windows (bypass broken Windows cert store)
import ssl, certifi
_orig_create_default_context = ssl.create_default_context
def _patched_create_default_context(*args, **kwargs):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(certifi.where())
    return ctx
ssl._create_default_https_context = _patched_create_default_context
ssl.create_default_context = _patched_create_default_context

import os
import signal
import time
from typing import Dict, Union

import openai
import tiktoken

# 支持自定义 BASE_URL (如 DeepSeek)
base_url = os.environ.get("OPENAI_BASE_URL", None)
api_key = os.environ.get("OPENAI_API_KEY", "sk-placeholder")
if base_url:
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
else:
    client = openai.OpenAI(api_key=api_key)

# Windows 不支持 SIGALRM，用简单超时替代
HAS_SIGALRM = hasattr(signal, 'SIGALRM')
if HAS_SIGALRM:
    def handler(signum, frame):
        raise Exception("end of time")
else:
    def handler(signum, frame):
        pass  # Windows: no-op


def num_tokens_from_messages(message, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if isinstance(message, list):
        # use last message.
        num_tokens = len(encoding.encode(message[0]["content"]))
    else:
        num_tokens = len(encoding.encode(message))
    return num_tokens


def create_chatgpt_config(
    message: Union[str, list],
    max_tokens: int,
    temperature: float = 1,
    batch_size: int = 1,
    system_message: str = "You are a helpful assistant.",
    model: str = "gpt-3.5-turbo",
) -> Dict:
    if isinstance(message, list):
        config = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "n": batch_size,
            "messages": [{"role": "system", "content": system_message}] + message,
        }
    else:
        config = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "n": batch_size,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message},
            ],
        }
    # DeepSeek 推理模型：开启 thinking 模式，提升代码修复质量
    # thinking tokens 和 content tokens 共享 max_tokens 额度，需设足够大
    if "deepseek" in model.lower():
        config["extra_body"] = {"thinking": {"type": "enabled"}}
        # thinking 模式不支持 temperature 参数，移除之
        config.pop("temperature", None)
        # 确保 max_tokens 足够容纳 thinking + 补丁代码
        if config["max_tokens"] < 8192:
            config["max_tokens"] = 8192
    return config


def request_chatgpt_engine(config):
    ret = None

    # DeepSeek 不支持 n>1，自动拆分为多次独立调用
    model = config.get("model", "")
    batch_size = config.get("n", 1)
    if "deepseek" in str(model).lower() and batch_size > 1:
        # 逐个调用，合并 choices
        single_config = {**config, "n": 1}
        choices = []
        total_usage = None
        for i in range(batch_size):
            r = None
            while r is None:
                try:
                    r = client.chat.completions.create(**single_config)
                except openai.BadRequestError as e:
                    print(e)
                    break
                except openai.RateLimitError as e:
                    print("Rate limit exceeded. Waiting...")
                    print(e)
                    time.sleep(5)
                except openai.APIConnectionError as e:
                    print("API connection error. Waiting...")
                    time.sleep(5)
                except Exception as e:
                    print("Unknown error. Waiting...")
                    print(e)
                    time.sleep(1)
            if r is None:
                return None
            choices.extend(r.choices)
            total_usage = r.usage  # last call's usage
        # 构造复合响应对象
        ret = r  # 用最后一次响应做模板
        ret.choices = choices
        return ret

    while ret is None:
        try:
            if HAS_SIGALRM:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(100)
            ret = client.chat.completions.create(**config)
            if HAS_SIGALRM:
                signal.alarm(0)
        except openai.BadRequestError as e:
            print(e)
            if HAS_SIGALRM:
                signal.alarm(0)
            break  # 400 错误不重试
        except openai.RateLimitError as e:
            print("Rate limit exceeded. Waiting...")
            print(e)
            if HAS_SIGALRM:
                signal.alarm(0)
            time.sleep(5)
        except openai.APIConnectionError as e:
            print("API connection error. Waiting...")
            if HAS_SIGALRM:
                signal.alarm(0)
            time.sleep(5)
        except Exception as e:
            print("Unknown error. Waiting...")
            print(e)
            if HAS_SIGALRM:
                signal.alarm(0)
            time.sleep(1)
    return ret


def create_anthropic_config(
    message: str,
    prefill_message: str,
    max_tokens: int,
    temperature: float = 1,
    batch_size: int = 1,
    system_message: str = "You are a helpful assistant.",
    model: str = "claude-2.1",
) -> Dict:
    if isinstance(message, list):
        config = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system": system_message,
            "messages": message,
        }
    else:
        config = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system": system_message,
            "messages": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": prefill_message},
            ],
        }
    return config


def request_anthropic_engine(client, config):
    ret = None
    while ret is None:
        try:
            if HAS_SIGALRM:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(100)
            ret = client.messages.create(**config)
            if HAS_SIGALRM:
                signal.alarm(0)
        except Exception as e:
            print("Unknown error. Waiting...")
            print(e)
            if HAS_SIGALRM:
                signal.alarm(0)
            time.sleep(10)
    return ret
